"""
FILE:       gates/t00_foundation.py
ROLE:       Gate for T0 - Foundation and Reset.
DOMAIN:     factory
DOES:       Asserts the project has one authority, one numbering, and no
            inherited memory.
NOTES:      Written during tranche declaration, before implementation, per
            .bcc/TRANCHE_PROTOCOL.md sec 3.2 rule 1.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

OUTCOME = "one authority, one numbering, no inherited memory"

ARCHIVE = "_ARCHIVE-PRE-RESET-2026-08-06"
SECRET_SUFFIXES = (".pfx", ".p12", ".pem", ".key", ".jks")


def _tracked(root: Path) -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True)
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


def check(r, root: Path) -> None:
    # --- one authority -----------------------------------------------------
    bcc = root / ".bcc"
    expected = {
        "BUILDER-CONSTRAINT-CONTRACT.md",
        "CHARTER.md",
        "TRANCHE_PROTOCOL.md",
        "TRANCHE_PLAN.md",
        "evidence",
    }
    actual = {p.name for p in bcc.iterdir()} if bcc.is_dir() else set()
    r.check(".bcc holds exactly the live authority set",
            actual == expected,
            f"unexpected={sorted(actual - expected)} missing={sorted(expected - actual)}")

    # --- one numbering -----------------------------------------------------
    tranche_hits, status_done_hits = [], []
    for p in root.rglob("*.py"):
        s = str(p)
        if ARCHIVE in s or "_trash" in s or "__pycache__" in s or ".venv" in s:
            continue
        if "_PARTS-FOR-PLANS" in s or "test-tmp" in s:
            continue
        try:
            head = p.read_text(encoding="utf-8", errors="replace")[:4000]
        except OSError:
            continue
        if re.search(r"^TRANCHE:\s", head, re.M):
            tranche_hits.append(str(p.relative_to(root)))
        if re.search(r"^STATUS:\s+DONE", head, re.M):
            status_done_hits.append(str(p.relative_to(root)))

    r.check("no live source carries a foreign TRANCHE header",
            not tranche_hits,
            f"{len(tranche_hits)} files, e.g. {tranche_hits[:3]}")
    r.check("no live source claims STATUS: DONE",
            not status_done_hits,
            f"{len(status_done_hits)} files, e.g. {status_done_hits[:3]}")

    prov = root / ".plans-and-parts_FOR-REFERENCE-ONLY" / ARCHIVE / "toolkit-header-provenance.json"
    r.check("header provenance preserved before stripping", prov.is_file(),
            "expected toolkit-header-provenance.json in the archive")

    # --- journal starts clean ---------------------------------------------
    jdir = root / "_docs" / "AppJOURNAL"
    entries = sorted(p.name for p in jdir.glob("*.md")) if jdir.is_dir() else []
    r.check("journal starts at 0001 with no predecessor entries",
            bool(entries) and entries[0].startswith("0001"),
            f"entries={entries}")

    # --- no inherited memory ----------------------------------------------
    # `_design` was archived and must never reappear at the root. `_artifacts` is
    # NOT in this group: it is regenerable runtime output that any tool run
    # recreates, and it is covered by the runtime-output checks above. Asserting
    # its absence was the same mistake already corrected for _state and logs -
    # a check that the act of testing itself defeats.
    stale = [d for d in ("_design",) if (root / d).exists()]
    r.check("archived zones have not reappeared at the root", not stale, f"present={stale}")

    # --- one sidecar, not a sidecar inside a sidecar -----------------------
    r.check("no nested toolkit/ directory", not (root / "toolkit").exists(),
            "the sidecar is the root; the ship boundary is a manifest, not a folder")
    for d in ("src", "tools", "config"):
        r.check(f"{d}/ is at the sidecar root", (root / d).is_dir())

    # --- the sidecar still works ------------------------------------------
    out = subprocess.run(
        ["python3", "-m", "src.app", "cli", "tool-list"],
        cwd=root, capture_output=True, text=True, timeout=180,
    )
    count = None
    try:
        count = json.loads(out.stdout).get("count")
    except Exception:
        pass
    r.check("toolkit runs and registers its tools",
            isinstance(count, int) and count > 0,
            f"count={count} stderr={out.stderr.strip()[:120]}")

    # --- hygiene -----------------------------------------------------------
    tracked = _tracked(root)
    secrets = [f for f in tracked if f.lower().endswith(SECRET_SUFFIXES)]
    r.check("no secret material is tracked", not secrets, f"{secrets[:3]}")

    leaked = [f for f in tracked
              if "/_state/" in f or "/.venv/" in f or "__pycache__" in f
              or f.startswith("_trash/") or ".useful-helpers/" in f]
    r.check("no runtime state, venv, or removal staging is tracked",
            not leaked, f"{len(leaked)} files, e.g. {leaked[:3]}")

    # --- the tree is at its default, installable state ---------------------
    # NOT "these directories are absent": running the sidecar at all regenerates
    # _state/ and logs/, and this gate itself invokes it. An earlier revision of
    # this check could therefore never pass. The real invariant is that runtime
    # output is never TRACKED and never packaged - presence on disk after use is
    # normal, and the vend manifest excludes it.
    tracked = _tracked(root)
    debris_tracked = [f for f in tracked if f.split("/")[0] in
                      ("_state", "logs", "_artifacts", ".useful-helpers-test-tmp")]
    r.check("no runtime output is tracked", not debris_tracked, f"{debris_tracked[:3]}")

    unignored = []
    for d in ("_state", "logs", "_artifacts", ".useful-helpers-test-tmp"):
        if (root / d).exists():
            ok = subprocess.run(["git", "check-ignore", "-q", d],
                                cwd=root, capture_output=True).returncode == 0
            if not ok:
                unignored.append(d)
    r.check("runtime output is covered by ignore rules", not unignored,
            f"present but not ignored: {unignored}")
    r.check("derived registry is not tracked",
            "config/registry.json" not in tracked,
            "config/registry.json is generated by registry-refresh")

    # ...and because it is untracked, a CLEAN CLONE has none. It must therefore be
    # generated on demand, or the repository cannot pass its own suite from a fresh
    # checkout - which is exactly what happened, invisibly, because untracking a
    # file does not delete it from trees that already had one.
    reg_src = (root / "src" / "core" / "registry.py").read_text(encoding="utf-8", errors="replace")
    app_src = (root / "src" / "app.py").read_text(encoding="utf-8", errors="replace")
    test_src = (root / "tests" / "test_smoke.py").read_text(encoding="utf-8", errors="replace")
    r.check("the derived registry is generated on demand when absent",
            "def ensure_manifest" in reg_src
            and "ensure_manifest" in app_src
            and "ensure_manifest" in test_src,
            "registry.ensure_manifest must exist and be called from the composition "
            "root and the test fixture, so a clean checkout needs no setup step")
    # Scoped to our own config/ deliberately. An earlier revision matched any path
    # containing "/smoke-", which swept up legitimate predecessor fixtures in the
    # parts bin - reference material, not residue this project produced.
    residue = [f for f in tracked
               if f.startswith("config/") and "/smoke-" in f and f.endswith(".json")]
    r.check("no smoke-run residue is tracked under config/", not residue, f"{residue[:3]}")

    # --- the BCC ships inert ----------------------------------------------
    tmpl = root / "templates" / "BUILDER-CONSTRAINT-CONTRACT.md.tmpl"
    r.check("BCC ships as a template", tmpl.is_file(),
            "expected templates/BUILDER-CONSTRAINT-CONTRACT.md.tmpl")
    if tmpl.is_file():
        body = tmpl.read_text(encoding="utf-8", errors="replace")
        holes = re.findall(r"\{\{BCC_[A-Z0-9_]+\}\}", body)
        r.check("the shipped BCC is unfilled, therefore inert",
                len(holes) >= 4,
                f"placeholders found={len(holes)} - a filled contract would bind "
                f"a freshly installed sidecar to this project")

    # --- development dependencies are declared -----------------------------
    dev = root / "requirements-dev.txt"
    r.check("development dependencies are declared", dev.is_file(),
            "requirements-dev.txt should exist even if the suite is stdlib-only")

    # --- lint, surfaced at gate level --------------------------------------
    # This was reachable ONLY through the test suite, where it skipped silently when
    # ruff was absent - which it was, in the development sandbox, for the whole life
    # of the project. Every tranche since T0 shipped unlinted. The first time it ran
    # it found two real defects, both introduced that same session.
    #
    # A capability whose only path is a test that can vanish is not enforced. Surfaced
    # here so its absence is visible as a SKIP rather than invisible as a pass.
    lint = subprocess.run([sys.executable, "-m", "ruff", "check", "."],
                          cwd=root, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300)
    if lint.returncode == 0:
        r.check("the payload lints clean", True)
    elif "No module named" in (lint.stderr or ""):
        r.skip("the payload lints clean",
               "ruff is not installed here; it is declared in requirements-dev.txt. "
               "A skip is not a pass - install it or run this gate on a host that has it")
    else:
        tail = (lint.stdout or lint.stderr).strip().splitlines()
        r.check("the payload lints clean", False, " | ".join(tail[-3:]))

    # --- the test suite actually runs --------------------------------------
    # This gate previously asserted only that a runner was DECLARED, and then
    # pronounced the baseline sound. It could not, and did not, notice that a
    # test was failing. A gate that never executes the suite cannot tell you the
    # suite is broken. SUITE_TEST_TMP keeps the suite's scratch on fast local
    # storage; without it the suite redirects all temp I/O onto the project's own
    # filesystem, which stalls on network or FUSE-mounted checkouts.
    #
    # Preflight: several tests delete files they created, under the project root.
    # A filesystem that denies unlink therefore fails them for a reason that has
    # nothing to do with the project - reporting that as "the suite fails" would
    # be a false accusation. Detect it and skip honestly instead. Verified on the
    # development mount: test_c1_hands and test_c4_data both raise
    # PermissionError [Errno 1] on unlink inside _artifacts/.
    unlink_ok = r.filesystem_permits_unlink(root)

    if not unlink_ok:
        r.skip("the test suite passes",
               "this filesystem denies unlink, and the suite deletes files it "
               "creates - it cannot pass here for environmental reasons. Run it "
               "on a host with normal delete semantics before trusting the baseline")
        return

    tmp = tempfile.mkdtemp(prefix="uh-gate-")
    env = {**os.environ, "SUITE_TEST_TMP": tmp}
    try:
        out = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
            cwd=root, capture_output=True, text=True, timeout=900, env=env,
        )
        tail = (out.stderr or out.stdout).strip().splitlines()
        r.check("the test suite passes", out.returncode == 0,
                " | ".join(tail[-3:]) if tail else f"exit {out.returncode}")
    except subprocess.TimeoutExpired:
        # Honest skip: a skipped check must never read as a pass (protocol sec 3.2 rule 7).
        r.skip("the test suite passes",
               "exceeded 900s even with SUITE_TEST_TMP on local storage - "
               "investigate before trusting this baseline")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # --- history is not grafted onto a predecessor's -----------------------
    # Earlier revisions of this check asserted "exactly one commit" and then
    # "branch == main with a T0: subject". Both were assumptions about workflow,
    # not project invariants - the operator may branch and name as they like, and
    # a tranche may need several commits. The real invariant is narrower: the
    # history must have a SINGLE ROOT, i.e. no predecessor project's history was
    # merged or grafted in behind ours.
    root_sha = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"],
                              cwd=root, capture_output=True, text=True).stdout.split()
    r.check("history has a single root - not grafted onto predecessor history",
            len(root_sha) == 1, f"root commits={len(root_sha)}")

    # --- the working tree matches what is committed ------------------------
    dirty = [ln for ln in subprocess.run(
        ["git", "status", "--porcelain"], cwd=root,
        capture_output=True, text=True).stdout.splitlines() if ln.strip()]
    r.check("working tree is clean", not dirty,
            f"{len(dirty)} uncommitted paths, e.g. {[d[3:] for d in dirty[:3]]}")
