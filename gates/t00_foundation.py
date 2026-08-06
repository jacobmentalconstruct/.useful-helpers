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
import re
import subprocess
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
    stale = [d for d in ("_artifacts", "_design") if (root / d).exists()]
    r.check("root carries no pre-reset memory zones", not stale, f"present={stale}")

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
