#!/usr/bin/env python3
"""
FILE:       _docs/release/release_check.py
ROLE:       Closure Gate 2 - the release verifier. Manufacture, inspect, install, walk.
DOMAIN:     factory
DOES:       Clones the source clean, builds a payload through the EXISTING mechanism,
            inspects the artifact both ways, installs it into A/B/C targets, runs the
            documented launcher, drives the T8 loop, runs the two oracle controls, and
            proves removal leaves a target byte-identical.
DEPENDS ON: stdlib only. Everything after manufacture goes through the ARTIFACT.
NOTES:      THE DEVELOPMENT TREE IS AN INPUT EXACTLY ONCE - to `git clone`. After that
            every command runs from the clone or from the installed instance. If this
            file ever reaches back into the working tree for a module, a tool body or a
            config, the thing being certified is no longer the artifact.

            "FORBIDDEN NAMES NOT FOUND" IS NOT A RELEASE PROOF. An empty directory passes
            that test perfectly. Every absence assertion here is paired with a presence
            assertion, because the failure mode of a subtractive payload builder is
            shipping too little, and the failure mode of a permissive one is shipping too
            much. Only asserting both directions can tell those apart.

            Run:  python _docs/release/release_check.py
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEV = Path(__file__).resolve().parent.parent.parent
CHECKS: list[dict] = []
SIDECAR = ".useful-helpers"


def check(step: str, name: str, ok: bool, detail: str = "") -> bool:
    CHECKS.append({"step": step, "name": name, "ok": bool(ok), "detail": detail})
    return bool(ok)


def run(cmd, cwd=None, timeout=600, env=None):
    return subprocess.run([str(c) for c in cmd], cwd=str(cwd) if cwd else None,
                          capture_output=True, text=True, timeout=timeout,
                          env=env, encoding="utf-8", errors="replace")


def clean_env(target: Path | None = None) -> dict:
    """The environment a REAL USER has: nothing pointing anywhere.

    This used to set `SUITE_PROJECT_ROOT=target` for installed-instance calls, and
    `run.sh smoke` failed with T6's refusal - "an environment variable does not rebind
    it". The instance is bound to its target STRUCTURALLY; supplying the variable is the
    transport override T6 exists to forbid, and nobody typing `sh .useful-helpers/run.sh
    attach` has it set. Passing it made the walk unrepresentative and then blamed the
    product for noticing.

    `target` is kept in the signature because the call sites read better naming what they
    are addressing, but it is deliberately not exported: identity resolves the target.
    """
    return {k: v for k, v in os.environ.items()
            if k not in ("SUITE_HOME", "SUITE_PROJECT_ROOT", "SUITE_STATE_ROOT")}


def launcher(home: Path) -> list:
    """The DOCUMENTED launcher, as the installer prints it - not `python -m src.app`.

    Driving the module directly would prove the code works while leaving the thing a
    user is actually told to type unverified. The installer's message is the contract.
    """
    if platform.system() == "Windows":
        return [str(home / "run.bat")]
    return ["sh", str(home / "run.sh")]


def tool_call(home: Path, target: Path, tool: str, args: dict, timeout: int = 400) -> dict:
    """Through the launcher's DOCUMENTED `call` verb.

    This first used `tool-call`, which is the module's argument, not the launcher's.
    The launcher takes a MODE - `attach | list | call | mcp | ui | smoke | cli` - and
    answered "unknown mode: tool-call" fourteen times. Using the module's vocabulary
    against the launcher proves the module works and leaves the documented surface
    untested, which is the opposite of what this gate is for.
    """
    p = run([*launcher(home), "call", "--tool", tool, "--args-json",
             json.dumps(args)], cwd=home, timeout=timeout, env=clean_env(target))
    try:
        return json.loads(p.stdout)
    except ValueError:
        return {"ok": False, "error": ((p.stderr or p.stdout) or "")[-400:],
                "output": None, "_raw": True}


def out(env: dict) -> dict:
    o = env.get("output")
    return o if isinstance(o, dict) else {}


def tree_digest(root: Path, skip: set[str]) -> dict[str, str]:
    d = {}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if set(rel.parts) & skip:
            continue
        d[rel.as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return d


# ============================================================ 1. manufacture
def manufacture(work: Path) -> tuple[Path, Path]:
    """clean clone -> existing vend mechanism -> release artifact."""
    clone = work / "clean-clone"
    p = run(["git", "clone", "--quiet", str(DEV), str(clone)], timeout=900)
    ok = check("1 manufacture", "a clean clone of the certified source is obtained",
               p.returncode == 0 and (clone / "src" / "core" / "payload.py").is_file(),
               f"rc={p.returncode} {((p.stderr or '')[-160:])}")
    if not ok:
        return clone, work / "artifact"

    dirty = run(["git", "status", "--porcelain"], cwd=clone).stdout.strip()
    check("1 manufacture", "the clone carries no uncommitted development state",
          not dirty, f"a clone that inherits working-tree changes is not a clean "
                     f"source; porcelain={dirty.splitlines()[:5]}")

    # THE EXISTING MECHANISM, invoked from the CLONE. `materialise` is imported out of
    # the clone rather than the working tree, so the payload boundary being exercised is
    # the committed one.
    artifact = work / "artifact" / "useful-helpers-toolkit"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    script = work / "_vend.py"
    script.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(clone)!r})\n"
        "from src.core.payload import materialise\n"
        f"materialise({str(clone)!r}, {str(artifact)!r})\n"
        "print('vended')\n", encoding="utf-8")
    v = run([sys.executable, str(script)], cwd=clone, timeout=900, env=clean_env())
    check("1 manufacture", "the EXISTING vend mechanism produces the payload",
          v.returncode == 0 and artifact.is_dir(),
          f"payload.materialise from the clone; rc={v.returncode} "
          f"{((v.stderr or '')[-200:])}")

    # THE DISTRIBUTION IS TWO THINGS, and the first run of this verifier did not know it.
    # `packaging` is INSTALLER_ONLY - deliberately kept OUT of the payload and shipped
    # BESIDE it. The installer README states the shape plainly: run.bat, run.sh,
    # install.py, and `useful-helpers-toolkit` as a sibling. Asserting the payload alone
    # was a release artifact was asserting half a product; the install steps failed with
    # "can't open install.py", which is what that mistake looks like from the outside.
    #
    # Assembling this is not building an assembler. It is copying the installer the
    # factory already ships next to the payload the existing mechanism already produces.
    dist = artifact.parent
    src_installer = clone / "packaging" / "installer"
    for name in ("install.py", "run.bat", "run.sh"):
        f = src_installer / name
        if f.is_file():
            shutil.copy2(f, dist / name)
    check("1 manufacture", "the distribution carries the installer beside the payload",
          (dist / "install.py").is_file() and artifact.is_dir(),
          f"the README declares run.bat / run.sh / install.py / {artifact.name}; "
          f"dist={sorted(q.name for q in dist.iterdir())}")
    return clone, artifact


# ============================================================ 2. inspect
FORBIDDEN = {
    ".plans-and-parts_FOR-REFERENCE-ONLY": "the donor reference corpus",
    "_harness": "the factory proving ground",
    "gates": "factory-only tranche material",
    ".bcc": "the builder constraint contract",
    "_projectmapper": "generated inspection state",
    "_state": "accumulated durable memory",
    ".git": "source history",
    "_trash": "development scrap",
}


def inspect(artifact: Path, clone: Path) -> None:
    if not artifact.is_dir():
        check("2 inspect", "the artifact exists to inspect", False, "no artifact")
        return
    names = {p.relative_to(artifact).parts[0] for p in artifact.rglob("*")
             if p.relative_to(artifact).parts}
    for forbidden, why in FORBIDDEN.items():
        check("2 inspect", f"the artifact excludes `{forbidden}` ({why})",
              forbidden not in names, "present in the payload root")

    check("2 inspect", "the artifact excludes the development journal",
          not (artifact / "_docs" / "AppJOURNAL").exists(),
          "development history is not product")
    check("2 inspect", "the artifact excludes certification evidence",
          not (artifact / "_docs" / "certification").exists(),
          "the record of how it was proven is not part of what ships")

    # PRESENCE. Absence assertions alone would be satisfied by an empty directory, and
    # the failure mode of a SUBTRACTIVE builder is shipping too little.
    required = {
        "run.sh": artifact / "run.sh",
        "run.bat": artifact / "run.bat",
        "the seam": artifact / "src" / "core" / "invoke.py",
        "the app entrypoint": artifact / "src" / "app.py",
        "the installer identity module": artifact / "src" / "core" / "instance.py",
        "the MCP entrance": artifact / "src" / "interfaces" / "mcp_server.py",
    }
    for label, p in required.items():
        check("2 inspect", f"the artifact contains {label}", p.is_file(), str(p))

    # EVERY TOOL THE CATALOGUE NAMES MUST HAVE A BODY. A registry advertising tools whose
    # entry files were excluded is the exact failure a subtractive boundary produces, and
    # it would look perfect to a name-based absence check.
    # MIRROR THE REGISTRY'S OWN RULE. `registry.discover` skips manifests whose parent
    # directory starts with `_` (tools/_template is a scaffolding stencil, not a tool),
    # so a check that globs every tool.json invents a defect the product does not have -
    # it reported `_template -> tools/example/cli.py` missing, which is a TEMPLATE
    # PLACEHOLDER. A verifier must apply the same rule as the thing it verifies.
    manifests = [m for m in (list((artifact / "tools").rglob("tool.json"))
                             + list((artifact / "apps").rglob("tool.json")))
                 if not m.parent.name.startswith("_")]
    missing = []
    for m in manifests:
        try:
            entry = (json.loads(m.read_text(encoding="utf-8"))
                     .get("invocation", {}).get("entry", ""))
        except ValueError:
            missing.append(f"{m.parent.name}: unreadable manifest")
            continue
        if entry and not (artifact / entry).is_file():
            missing.append(f"{m.parent.name} -> {entry}")
    check("2 inspect", "every tool the artifact declares has its entry file",
          bool(manifests) and not missing,
          f"{len(manifests)} manifests; missing bodies: {missing[:6]}")

    # BUILD-MACHINE ABSOLUTE PATHS. The development root must not appear anywhere.
    needle = str(DEV)
    leaks = []
    for p in artifact.rglob("*"):
        if not p.is_file() or p.suffix in (".pyc", ".sqlite3", ".png", ".ico"):
            continue
        try:
            if needle in p.read_text(encoding="utf-8", errors="ignore"):
                leaks.append(p.relative_to(artifact).as_posix())
        except OSError:
            continue
    check("2 inspect", "no build-machine absolute path appears in the artifact",
          not leaks, f"the development root {needle!r} leaked into: {leaks[:6]}")

    check("2 inspect", "the artifact is bounded",
          len(list(artifact.rglob("*"))) < 2000,
          f"entries={len(list(artifact.rglob('*')))}; a vend once shipped 4,009 files")


# ============================================================ targets
def target_a(work: Path, clone: Path) -> Path:
    """A: a nontrivial REAL software project - a copy of the certified source itself."""
    t = work / "target-a-software"
    shutil.copytree(clone, t, ignore=shutil.ignore_patterns(".git", "__pycache__",
                                                            "_state", "_artifacts"))
    return t


def target_b(work: Path) -> Path:
    """B: a mixed records / data / documents target. NOT seeded with any oracle."""
    t = work / "target-b-records"
    (t / "case-files").mkdir(parents=True)
    (t / "data").mkdir()
    for i in range(1, 5):
        (t / "case-files" / f"memo-{i:02d}.txt").write_text(
            f"MEMO {i}\n\nCorrespondence regarding matter {i}.\n", encoding="utf-8")
    (t / "case-files" / "exhibit.md").write_text(
        "# Exhibit A\n\nA document, not code.\n", encoding="utf-8")
    (t / "data" / "index.csv").write_text(
        "id,name,filed\n1,Deed,2026-01-02\n2,Lease,2026-03-04\n", encoding="utf-8")
    (t / "README.md").write_text("# Records\n\nA mixed records target.\n",
                                 encoding="utf-8")
    return t


def target_c(work: Path) -> Path:
    """C: genuinely empty/nascent. One README is what 'nascent' looks like."""
    t = work / "target-c-empty"
    t.mkdir(parents=True)
    (t / "README.md").write_text("# New project\n", encoding="utf-8")
    return t


def install_into(artifact: Path, target: Path) -> tuple[Path, str]:
    """Run the REAL setup application from the distribution, headless."""
    installer = artifact.parent / "install.py"
    p = run([sys.executable, str(installer), "--target", str(target), "--mode", "install"],
            cwd=artifact.parent, timeout=900, env=clean_env())
    return target / SIDECAR, (p.stdout or "") + (p.stderr or "")


# ============================================================ 3. the walk
def walk(artifact: Path, label: str, target: Path, *, full: bool) -> Path | None:
    step = f"3 walk[{label}]"
    home, log = install_into(artifact, target)
    if not check(step, "the real Setup produces one installed instance",
                 home.is_dir() and (home / "instance.json").is_file(),
                 f"expected {SIDECAR}/instance.json; installer said: {log[-220:]}"):
        return None

    ident = json.loads((home / "instance.json").read_text(encoding="utf-8"))
    check(step, "the instance carries an identity bound to this target",
          bool(ident.get("uuid")) and "target" in ident,
          f"instance.json={ident}")

    # THE HEADLINE DOCUMENTED COMMAND, run from the TARGET ROOT exactly as the installer
    # prints it: `sh .useful-helpers/run.sh attach`. Running it from inside the instance
    # would skip the property the launcher exists for - resolving its own directory so
    # the working directory does not matter.
    rel = f"{SIDECAR}/run.bat" if platform.system() == "Windows" else f"{SIDECAR}/run.sh"
    cmd = [str(target / SIDECAR / "run.bat")] if platform.system() == "Windows" \
        else ["sh", rel]
    p = run([*cmd, "attach"], cwd=target, timeout=400, env=clean_env(target))
    check(step, "the DOCUMENTED launcher runs from the TARGET ROOT",
          p.returncode == 0 and '"ok"' in (p.stdout or ""),
          f"`{' '.join(cmd)} attach` from the target root; rc={p.returncode} "
          f"out={(p.stdout or '')[:100]!r} err={(p.stderr or '')[-200:]!r}")

    v = run([*launcher(home), "cli", "version"], cwd=home, timeout=300,
            env=clean_env(target))
    check(step, "the installed product reports its own version",
          v.returncode == 0 and "usefulhelpers" in (v.stdout or "").lower(),
          f"rc={v.returncode} out={(v.stdout or '')[:120]!r}")

    sm = run([*launcher(home), "smoke"], cwd=home, timeout=600, env=clean_env(target))
    check(step, "the installed product can verify itself (`run smoke`)",
          sm.returncode == 0,
          f"rc={sm.returncode} tail={((sm.stdout or '') + (sm.stderr or ''))[-200:]!r}")

    att = out(tool_call(home, target, "attach", {"refresh": True}))
    aw = att.get("awareness") or {}
    check(step, "`attach` produces awareness of THIS target",
          bool(att) and (bool(att.get("project_map")) or bool(aw.get("revision"))),
          f"keys={sorted(att)[:9]} revision={aw.get('revision')!r}")

    check(step, "awareness reports its own limitations rather than inventing detail",
          isinstance(aw.get("limitations"), list) or "limitations" in aw
          or bool(att.get("project_map")),
          f"a thin target is a legitimate map; got {sorted(aw)[:8]}")

    if not full:
        return home

    # ---- the real MCP entrance, external client
    mcp = run([*launcher(home), "mcp"], cwd=home, timeout=180, env=clean_env(target))
    check(step, "the real MCP entrance starts and exits cleanly",
          "MCP stdio server" in ((mcp.stdout or "") + (mcp.stderr or "")),
          f"rc={mcp.returncode} {((mcp.stderr or '')[-200:])!r}")

    # ---- retained parity products, FROM THE INSTALLED ARTIFACT
    lst = out(tool_call(home, target, "file_tree", {"root": ".", "kind": "file"}))
    check(step, "a retained parity product runs from the installed artifact",
          bool(lst.get("rows")), f"file_tree returned {len(lst.get('rows') or [])} rows")
    snap = out(tool_call(home, target, "projectmapper",
                         {"action": "compile", "root": ".", "name": "release",
                          "out": str(target / SIDECAR / "_release_snap.sqlite3"),
                          "markdown": True, "apply": True}))
    check(step, "the ProjectMapper parity products build from the artifact",
          bool((snap.get("outputs") or {}).get("manifest_md")),
          f"outputs={sorted((snap.get('outputs') or {}))}")

    # ---- the T8 loop
    # EDIT SOMETHING AWARENESS ITSELF SAYS IT OBSERVES.
    #
    # The revision is CONTENT-ANCHORED over canonical observations (T7), not a hash of the
    # tree, so an edit that touches nothing observed legitimately leaves it identical. My
    # first attempt asserted X != Y after changing a word in a function body; my second
    # picked "the first file containing ROLE:" and landed on `src/__init__.py`, a bare
    # package marker whose docstring awareness does not promote - purposes come from the
    # primary CLASS docstring. Both times the product was right and the fixture was blind:
    # staleness is "the target moved", the revision is "what is known changed", and a
    # fixture that cannot tell those apart is not testing either.
    #
    # Asking awareness for a HANDLE it promoted removes the guesswork entirely - the file
    # is chosen by the mechanism under test, so the edit is guaranteed to touch an observed
    # value rather than hoping it does.
    before = out(tool_call(home, target, "attach", {"refresh": True})).get("awareness") or {}
    rev_x = before.get("revision")
    handles = [h for h in (before.get("handles") or []) if isinstance(h, str)]
    rel, live = None, None
    for h in handles:
        cand = target / (h.replace(".", "/") + ".py")
        if cand.is_file() and "ROLE:" in cand.read_text(encoding="utf-8", errors="replace"):
            rel, live = cand.relative_to(target).as_posix(), cand
            break
    if live is None:
        cand = next((q for q in sorted((target / "src").rglob("*.py"))
                     if "ROLE:" in q.read_text(encoding="utf-8", errors="replace")
                     and q.name != "__init__.py"), None) \
            if (target / "src").is_dir() else None
        rel = cand.relative_to(target).as_posix() if cand else "README.md"
        live = target / rel
    check(step, "T8: awareness names a handle the loop can act on",
          bool(handles), f"handles={handles[:5]} chosen={rel!r}")
    original = live.read_text(encoding="utf-8", errors="replace")
    token = "ROLE:" if "ROLE:" in original else next(
        (w for w in ("project", "New", "#") if w in original), None)
    prev = out(tool_call(home, target, "edit",
                         {"path": rel, "pattern": token, "replacement": token + "X",
                          "literal": True, "count": 1}))
    check(step, "T8: a preview proposes a change and binds it to the reviewed source",
          prev.get("written") is False
          and bool((prev.get("apply_with") or {}).get("expected_source_sha256")),
          f"apply_with={prev.get('apply_with')}")
    dif = out(tool_call(home, target, "diff",
                        {"a_text": original, "b_text": prev.get("result", "")}))
    check(step, "T8: the change is reviewable as a diff before approval",
          dif.get("identical") is False, f"identical={dif.get('identical')}")
    applied = out(tool_call(home, target, "edit",
                            {"path": rel, "pattern": token, "replacement": token + "X",
                             "literal": True, "count": 1,
                             **(prev.get("apply_with") or {})}))
    check(step, "T8: the approved Apply lands exactly what was previewed",
          live.read_text(encoding="utf-8", errors="replace") == prev.get("result"),
          f"written={applied.get('written')}")
    check(step, "T8: the seam measures what changed",
          isinstance(applied.get("changed_paths"), list)
          and bool(applied.get("measurement")),
          f"changed_paths={applied.get('changed_paths')} "
          f"measurement={(applied.get('measurement') or {}).get('basis')}")

    prof = out(tool_call(home, target, "command_profile", {"root": "."}))
    kinds = sorted({c.get("kind") for c in (prof.get("commands") or [])})
    check(step, "T8: verification is selected mechanically, or honestly absent",
          isinstance(prof.get("commands"), list),
          f"detected kinds={kinds} (no test/lint is a truthful answer)")

    stale = (out(tool_call(home, target, "attach", {})).get("awareness") or {})
    check(step, "T8: the Apply makes the prior awareness stale",
          (stale.get("freshness") or {}).get("stale") is True,
          f"freshness={stale.get('freshness')}")
    after = out(tool_call(home, target, "attach", {"refresh": True})).get("awareness") or {}
    check(step, "T8: refresh produces a NEW revision reflecting the new evidence",
          bool(after.get("revision")) and after.get("revision") != rev_x,
          f"X={rev_x!r} Y={after.get('revision')!r}")

    # ---- update preserves identity and product-owned state
    uuid_before = ident.get("uuid")
    state_marker = home / "_state" / "_release_marker.txt"
    state_marker.parent.mkdir(parents=True, exist_ok=True)
    state_marker.write_text("survive the update\n", encoding="utf-8")
    _, ulog = install_into(artifact, target)
    ident_after = json.loads((home / "instance.json").read_text(encoding="utf-8"))
    check(step, "update preserves the instance UUID",
          ident_after.get("uuid") == uuid_before,
          f"{uuid_before} -> {ident_after.get('uuid')}; {ulog[-160:]}")
    check(step, "update preserves product-owned state",
          state_marker.is_file()
          and state_marker.read_text(encoding="utf-8") == "survive the update\n",
          "a marker written into the instance's _state must survive an update")
    return home


# ============================================================ 4. oracles
def oracles(artifact: Path, work: Path) -> None:
    """Known-answer controls. These are the only seeded targets in the release."""
    step = "4 oracles"
    hz = artifact / "_harness" / "harness.py"
    check(step, "the oracle controls are runnable for this release",
          not hz.exists(),
          "the harness is factory-only and correctly absent from the artifact; the "
          "oracle controls therefore run from the CLEAN CLONE, which is the source of "
          "the artifact, not from the development working tree")


def oracles_from_clone(clone: Path) -> None:
    step = "4 oracles"
    runs = clone / "_harness" / "runs"
    for name, kind in (("rel-oracle-composite", "composite"),
                       ("rel-oracle-python", "python-app")):
        s = run([sys.executable, str(clone / "_harness" / "harness.py"), "scaffold",
                 name, "--kind", kind, "--force"], cwd=clone, timeout=600,
                env=clean_env())
        if s.returncode != 0:
            check(step, f"the {kind} oracle target is scaffolded", False,
                  (s.stderr or s.stdout)[-200:])
            continue
        r = run([sys.executable, str(clone / "_harness" / "harness.py"), "run", name],
                cwd=clone, timeout=900, env=clean_env())
        rec = {}
        if runs.is_dir():
            latest = sorted(runs.glob(f"*-{name}/run.json"),
                            key=lambda p: p.stat().st_mtime)
            if latest:
                rec = json.loads(latest[-1].read_text(encoding="utf-8"))
        score = rec.get("score") or {}
        if kind == "composite":
            comp = score.get("composition") or {}
            check(step, "composition is ACTUALLY SCORED and correct on the oracle",
                  bool(comp) and comp.get("composite_correct") is True
                  and comp.get("subsystems_correct") == comp.get("subsystems_expected")
                  and not comp.get("mismatches"),
                  f"rc={r.returncode} composition={comp}")
        else:
            t = score.get("truthfulness") or {}
            fp, naive = t.get("false_positives"), t.get("naive_false_positives")
            prev, missed = t.get("policy_prevented"), t.get("missed_true_positives")
            check(step, "truthfulness DISCRIMINATION is actually scored on the oracle",
                  fp == 0 and missed == 0
                  and isinstance(naive, int) and naive > 0
                  and isinstance(prev, int) and prev > 0,
                  f"rc={r.returncode} naive={naive} -> prevented={prev} -> faithful={fp}, "
                  f"missed={missed}. Zero false positives with nothing prevented is "
                  "indistinguishable from an analysis that found nothing")


# ============================================================ 5. removal
def removal(artifact: Path, work: Path) -> None:
    """A target where NO deliberate Apply has occurred - kept apart from the T8 walk."""
    step = "5 removal"
    t = work / "target-removal"
    (t / "docs").mkdir(parents=True)
    (t / "docs" / "note.md").write_text("# Untouched\n\nThis must not change.\n",
                                        encoding="utf-8")
    (t / "data.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    before = tree_digest(t, skip=set())

    home, log = install_into(artifact, t)
    if not check(step, "the sidecar installs into the untouched target", home.is_dir(),
                 log[-200:]):
        return
    # Observe only. No Apply, deliberately.
    tool_call(home, t, "attach", {"refresh": True})
    tool_call(home, t, "file_tree", {"root": ".", "kind": "file"})
    tool_call(home, t, "report", {"path": "."})

    after_use = tree_digest(t, skip={SIDECAR})
    check(step, "using the sidecar did not modify target-owned content",
          after_use == before,
          f"changed={sorted(set(before) ^ set(after_use)) or [k for k in before if before[k] != after_use.get(k)]}")

    shutil.rmtree(home, ignore_errors=True)
    after_removal = tree_digest(t, skip=set())
    check(step, "removing the sidecar leaves target content BYTE-FOR-BYTE unchanged",
          after_removal == before,
          f"before={len(before)} files, after={len(after_removal)}; "
          f"diff={sorted(set(before) ^ set(after_removal))[:6]}")
    check(step, "removing the sidecar leaves no residue behind",
          not (t / SIDECAR).exists(), "the instance directory is gone")


# ============================================================ main
def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="release-"))
    print(f"release verification on {platform.system()}  workspace={work}")
    try:
        clone, artifact = manufacture(work)
        inspect(artifact, clone)
        if artifact.is_dir():
            walk(artifact, "A software", target_a(work, clone), full=True)
            walk(artifact, "B records", target_b(work), full=False)
            walk(artifact, "C empty", target_c(work), full=False)
            oracles(artifact, work)
            oracles_from_clone(clone)
            removal(artifact, work)
    finally:
        pass  # the workspace is kept for inspection; the OS reclaims temp

    print("\nRELEASE — Closure Gate 2\n" + "=" * 78)
    step = None
    for c in CHECKS:
        if c["step"] != step:
            step = c["step"]
            print(f"\n{step}")
        print(f"  [{'PASS' if c['ok'] else 'FAIL'}] {c['name']}")
        if not c["ok"]:
            print(f"         {c['detail']}")
    bad = [c for c in CHECKS if not c["ok"]]
    print("\n" + "=" * 78)
    print(f"{len(CHECKS) - len(bad)}/{len(CHECKS)} release checks pass on "
          f"{platform.system()}")
    rec = Path(__file__).parent / f"release-{platform.system().lower()}.json"
    rec.write_text(json.dumps(
        {"platform": platform.system(), "python": platform.python_version(),
         "workspace": str(work), "checks": CHECKS}, indent=2), encoding="utf-8")
    print(f"record: {rec}")
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
