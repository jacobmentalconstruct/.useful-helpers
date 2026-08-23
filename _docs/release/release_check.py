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
import signal
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DEV = Path(__file__).resolve().parent.parent.parent
CHECKS: list[dict] = []
SIDECAR = ".useful-helpers"


_LAST_CHECK = time.monotonic()


def check(step: str, name: str, ok: bool, detail: str = "", note: str = "") -> bool:
    """EVERY CHECK IS PRINTED THE MOMENT IT IS DECIDED, not in a report at the end.

    `note` IS EVIDENCE THAT SURVIVES A PASS. `detail` is only shown and only read when a
    check fails, which meant the Windows smoke run - 184 seconds, `rc=0`, green - recorded
    nothing at all. The launcher had lost the exit code in a parenthesized block and was
    reporting success for a suite that failed; the test counts would have said so on the
    first run, and they were thrown away because the check passed. A measurement is worth
    keeping whichever way it came out.

    The report used to be the only output, so a run that took thirty minutes and then
    wedged showed a single workspace path and nothing else - no stage, no progress, no
    way to tell a slow run from a dead one without a process explorer. The instrument
    was unobservable exactly when observing it mattered, and the operator paid for that
    in wall-clock. The elapsed figure is the gap since the previous check, which is what
    makes the expensive step name itself.

    The formal report at the end is unchanged. This is the live feed, not a replacement.
    """
    global _LAST_CHECK
    CHECKS.append({"step": step, "name": name, "ok": bool(ok),
                   "detail": detail, "note": note})
    now = time.monotonic()
    print(f"  [{'PASS' if ok else 'FAIL'}] {step} | {name}  ({now - _LAST_CHECK:.1f}s)",
          flush=True)
    if note:
        print(f"         {note}", flush=True)
    if not ok:
        print(f"         {detail}", flush=True)
    _LAST_CHECK = now
    return bool(ok)


def _kill_tree(p: subprocess.Popen) -> None:
    """Kill the child AND everything it spawned.

    `Popen.kill()` kills one process. On Windows a `.bat` is run by cmd.exe, so the
    python.exe doing the actual work is a GRANDCHILD: killing the child leaves it alive,
    still holding the inherited stdout pipe, and the wait for that pipe to close then
    blocks forever - past the timeout, with no output, indefinitely. A timeout that
    cannot end the thing it timed out on is not a timeout.
    """
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)],
                       capture_output=True)
    else:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            p.kill()


def run(cmd, cwd=None, timeout=600, env=None):
    """STDIN IS CLOSED, NEVER THE OPERATOR'S CONSOLE - and a timeout really ends things.

    Without `stdin=DEVNULL` every child inherits whatever the verifier was launched
    with, and the MCP entrance check - `run.bat mcp`, a STDIO server - reads stdin until
    EOF. Launched from an interactive Windows console that EOF never comes. The Linux
    leg could never see it: under `nohup` stdin is already /dev/null, so the server got
    its EOF and the check passed. A verifier whose result depends on how the operator
    started it is measuring the operator, not the product.

    The timeout path is spelled out rather than left to `subprocess.run`, because the
    convenience wrapper kills only the direct child and then waits on pipes the survivors
    still hold. A slow `run.bat smoke` therefore hung the whole gate with no output and
    no record - the SAME failure the MCP check produced, reached by a different road.
    Here the tree is killed and rc=124 is recorded, so a step that runs too long becomes
    a FINDING instead of a lockup.

    Every invocation narrates itself. The run is long and mostly silent otherwise, and
    a subprocess that never returns should be identifiable by name from the console.
    """
    label = " ".join(str(c) for c in cmd)
    print(f"    · {label if len(label) <= 110 else label[:107] + '…'}", flush=True)
    t0 = time.monotonic()
    kw = {} if os.name == "nt" else {"start_new_session": True}
    p = subprocess.Popen([str(c) for c in cmd], cwd=str(cwd) if cwd else None,
                         stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, env=env,
                         encoding="utf-8", errors="replace", **kw)
    timed_out = False
    try:
        so, se = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_tree(p)
        try:
            so, se = p.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            so, se = "", ""
        se = (se or "") + f"\n[verifier] TIMED OUT after {timeout}s; process tree killed"
    rc = 124 if timed_out else p.returncode
    print(f"      rc={rc} in {time.monotonic() - t0:.1f}s"
          + ("  TIMED OUT" if timed_out else ""), flush=True)
    return subprocess.CompletedProcess(cmd, rc, so, se)


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
    """Through the launcher's DOCUMENTED tool verb - WHICH IS NOT THE SAME WORD ON BOTH
    PLATFORMS.

    This first used `tool-call`, which is the module's argument, not the launcher's, and
    the launcher answered "unknown mode: tool-call" fourteen times. Using the module's
    vocabulary against the launcher proves the module works and leaves the documented
    surface untested, which is the opposite of what this gate is for.

    THEN IT MADE THE SAME MISTAKE ONE LEVEL UP. `call` was hardcoded - and `call` is
    run.sh's verb. `run.bat` has no `call`; it documents `tool <id> <args-json>`, so
    every tool invocation on Windows fell through run.bat's catch-all to
    `python -m src.app call ...`, drew "unknown mode: call", and exited 2. Fifteen
    checks went red against a product that was never asked anything. Reading run.sh's
    help and calling the result "the documented surface" is exactly the error the
    paragraph above describes, committed against the other platform's launcher.

    Each launcher's own help is the contract for that launcher. run.sh says
    `call --tool X --args-json J`; run.bat says `tool <id> <args-json>`. Both are used
    here as written. That the two disagree is a product finding, recorded as one - it is
    not something this verifier gets to paper over by picking a favourite.
    """
    payload = json.dumps(args)
    # @FILE ON WINDOWS, ALWAYS; INLINE ON POSIX, ALWAYS.
    #
    # `run.bat tool diff <json>` returned rc=1 on the Windows leg while the identical call
    # passed on Linux, and the first explanation - cmd.exe's 32,767-character command line
    # - turned out to be wrong: the payload measures ~11KB. rc=1 is the shared runner's
    # code for a tool that raised, which is what a tool does when handed JSON that no
    # longer parses. Somewhere between `list2cmdline` quoting the argument, cmd.exe
    # re-parsing it and `%~3` unwrapping it, an escaped payload stops being the payload.
    # A hand-typed call with hand-written escapes works; a programmatic one does not
    # reliably, and this verifier is a programmatic one.
    #
    # So the walk stops routing its work through a channel that cannot promise to deliver
    # it. POSIX passes an argument vector with no intermediary and needs no file. What
    # inline can and cannot carry on Windows is asserted separately, once, rather than
    # silently decided here - see `the launcher carries an inline payload intact`.
    argfile = None
    if platform.system() == "Windows":
        fd, argfile = tempfile.mkstemp(prefix="uh-check-args-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        payload = "@" + argfile
    try:
        if platform.system() == "Windows":
            cmd = [*launcher(home), "tool", tool, payload]
        else:
            cmd = [*launcher(home), "call", "--tool", tool, "--args-json", payload]
        p = run(cmd, cwd=home, timeout=timeout, env=clean_env(target))
    finally:
        if argfile:
            try:
                os.unlink(argfile)
            except OSError:
                pass
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


def reclaim(work: Path) -> bool:
    """Delete the workspace, and REPORT HONESTLY whether it went.

    `shutil.rmtree(work, ignore_errors=True)` printed "workspace reclaimed" and left the
    directory sitting in %TEMP%. Git's object files are read-only on Windows, rmtree
    cannot unlink them, and `ignore_errors` swallowed the failure - so the console
    asserted something false and the next run inherited the debris. The hygiene check
    caught it, which is the only reason anyone found out.

    Clearing the read-only bit is what the deletion actually needs; returning the truth
    is what the caller actually needs.
    """
    def force(func, path, _exc):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except OSError:
            pass

    kw = {"onexc": force} if sys.version_info >= (3, 12) else {"onerror": force}
    for _ in range(3):
        shutil.rmtree(work, **kw)
        if not work.exists():
            return True
        time.sleep(0.5)
    return not work.exists()


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
    "tests": "the toolkit's own self-test suite, which asserts the FACTORY's layout",
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


def synopsis_truthfulness(step: str, att: dict, target: Path) -> None:
    """Extracted so it can be exercised without standing up a whole walk.

    A check that decides whether an instrument told the truth is itself an instrument,
    and the first version of this one passed while testing nothing. It gets unit tests.
    """
    # THE ONE PLACE IN THE ORDINARY WALK WHERE THE RIGHT ANSWER IS KNOWN.
    #
    # C is the nascent target, and what it can support is knowable without seeding it
    # with bait: a citation naming a README or a module docstring that is not there is
    # false whatever the prose around it says, and a purpose statement about a target
    # with no files at all is fabrication by construction. This is checked HERE rather
    # than in the bait oracle because the oracle proves discrimination on a CONTROLLED
    # target and this proves truthfulness on a real one.
    #
    # SCORED-NESS IS PART OF THE ASSERTION, in the shape the oracle checks already use
    # ("ACTUALLY SCORED and correct"). The first version of this check went green on a
    # machine with no summary backend: no synopsis was produced, so nothing could be
    # wrong with one, so it passed having tested nothing. That is "forbidden names not
    # found" committed by the verifier itself, and C4 is explicit - a missing oracle
    # stays UNSCORED and never reads as PASS.
    #
    # Which of the two it is comes from the PRODUCT'S OWN limit strings, not from this
    # file going looking for a model runtime. "No summary backend reachable" is an
    # environment gap. "This target is empty, so there is no purpose to state" is the
    # product declining on purpose, which is the behaviour being verified - and it is
    # only unambiguous because the product probes availability BEFORE it decides.
    pmap = att.get("project_map") or {}
    syn = pmap.get("synopsis") or {}
    # THE PRODUCT OWNS THE VOCABULARY OF ITS OWN REASONS, so this reads the ONE
    # distinction that matters and does not try to enumerate the rest: could the feature
    # run at all? Everything else it says about withholding is a decision it made, which
    # is the behaviour under test. Matching on each individual reason would make this
    # check silently unscored every time the product worded a new one.
    absent = [ln for ln in (pmap.get("limits") or [])
              if ln.startswith("No semantic synopsis")]
    gap = any(("no summary backend reachable" in ln) or ("no usable answer" in ln)
              for ln in absent)
    declined = bool(absent) and not gap
    scored = bool(syn) or declined

    grounded = syn.get("grounded_in") or ""
    # THE WALK POLLUTES THE TARGET BEFORE THIS RUNS, so "is there a .py here" is not the
    # same question as "was there a .py for the reader to read". `run smoke` executes
    # first, and the shipped suite wrote scratch into
    # `<target>/_artifacts/test_tmp/.../scaffold/src/app.py` - five Python files the
    # product never observed, sitting in the target, enough to make a false citation of
    # "module docstrings" look satisfied. This check passed a fabricated synopsis on
    # Windows for exactly that reason, having been tested only against a clean synthetic
    # target where the situation cannot arise. Excluding one directory by name would have
    # been robust against the last scratch path, not the next one.
    #
    # Dot- and underscore-prefixed directories are this project's convention for
    # "generated, or ours, not the target's": `.useful-helpers`, `_artifacts`, `_state`,
    # `__pycache__`. The class is what gets excluded.
    def target_own(q: Path) -> bool:
        return not any(part[:1] in (".", "_")
                       for part in q.relative_to(target).parts[:-1])

    present = {
        "README": any(q.name.lower().startswith("readme")
                      for q in target.glob("*") if q.is_file()),
        "module docstrings": any(q for q in target.rglob("*.py") if target_own(q)),
    }
    uncited = [c for c, there in present.items() if c in grounded and not there]
    no_files = (pmap.get("shape") or {}).get("file_count", 0) == 0
    # A PURPOSE GROUNDED IN SHAPE ALONE IS NOT GROUNDED. When `structure` is the only
    # source named, the reader was handed file counts and directory names and asked what
    # the project is FOR. Nothing in that input can answer the question, so whatever came
    # back came from somewhere else. Asserted independently of whether the product happens
    # to guard it, because that guard is one of the things under test.
    sources = [x.strip() for x in grounded.split("(")[0].split("+") if x.strip()]
    shape_only = bool(syn) and sources == ["structure"]
    truthful = not uncited and not (syn and no_files) and not shape_only

    shape = pmap.get("shape") or {}
    check(step, "the synopsis is ACTUALLY SCORED and asserts nothing the evidence "
                "cannot support",
          scored and truthful,
          f"UNSCORED - no synopsis, and no recorded decision to withhold one, so "
          f"nothing about truthfulness was tested here; "
          f"last limit={(pmap.get('limits') or ['(none)'])[-1][:90]!r}"
          if not scored else
          f"density={pmap.get('evidence_density')!r} files={shape.get('file_count')} "
          f"grounded_in={grounded!r} cites-but-absent={uncited} "
          f"shape_only={shape_only} "
          f"purpose={(syn.get('purpose') or '(withheld)')[:110]!r}")


# ============================================================ 3. the walk
def walk(artifact: Path, label: str, target: Path, *, full: bool,
         synopsis_probe: bool = False) -> Path | None:
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

    # A GATE MAY NOT ASSERT A CAPABILITY THE PLATFORM CANNOT PROVIDE - AND MAY NOT LET
    # THE ABSENCE GO UNRECORDED EITHER.
    #
    # Measured, not inferred: a JSON payload sent by a program to a .bat arrives split
    # across several arguments, because cmd.exe does not read the backslash-escaped quotes
    # that subprocess layers emit. `{"message": "nested \"quotes\"...}` reached the batch
    # as %2=`{\"message\": \"nested` and %3=`\\\"quotes\\\"`. No amount of work inside
    # run.bat repairs that; the argument was destroyed before the batch was entered.
    #
    # Three responses were possible and two are wrong. DELETING the check would erase the
    # limitation from the record, so a reader of the certification would assume inline
    # works everywhere. INVERTING it - passing when the payload corrupts - would enshrine
    # a defect as a requirement and fail the day someone fixed it. So the assertion moves
    # to the route the product actually offers programmatic callers, and what cannot be
    # provided becomes a DISCLOSURE requirement instead: the launcher must say so itself.
    #
    # That is the standard this product already holds `attach` to. A map that cannot know
    # something says it cannot know it, and the gate checks that it said so. A launcher
    # that cannot carry something says it cannot carry it, and the gate checks the same.
    hostile = {"message": 'nested "quotes" and C:\\win\\style\\path',
               "arr": [1, {"k": True}]}
    hfd, hpath = tempfile.mkstemp(prefix="uh-hostile-", suffix=".json")
    try:
        with os.fdopen(hfd, "w", encoding="utf-8") as fh:
            json.dump(hostile, fh)
        if platform.system() == "Windows":
            fcmd = [*launcher(home), "tool", "ping", "@" + hpath]
        else:
            fcmd = [*launcher(home), "call", "--tool", "ping",
                    "--args-json", "@" + hpath]
        fp = run(fcmd, cwd=home, timeout=300, env=clean_env(target))
    finally:
        try:
            os.unlink(hpath)
        except OSError:
            pass
    try:
        echoed = ((json.loads(fp.stdout).get("output") or {}).get("echo"))
    except ValueError:
        echoed = None
    check(step, "the programmatic payload route carries a hostile payload intact",
          echoed == hostile["message"],
          f"rc={fp.returncode} sent={hostile['message']!r} got={echoed!r} - `@file` is what "
          "the launcher tells scripts to use; if it cannot carry quotes and backslashes "
          "there is no route that can",
          note=f"@file round-trip {'intact' if echoed == hostile['message'] else 'CORRUPTED'}")

    if platform.system() == "Windows":
        # The capability is impossible here, so what is asserted is that the product says
        # so, in the launcher's own help, where an operator meets it.
        hp = run([*launcher(home), "help"], cwd=home, timeout=120, env=clean_env(target))
        said = (hp.stdout or "") + (hp.stderr or "")
        check(step, "the launcher states that inline payloads are not for programs",
              "inline" in said.lower() and "@<file>" in said.lower(),
              f"rc={hp.returncode} help={said[-200:]!r} - cmd.exe shatters a "
              "programmatically-sent JSON argument before the batch sees it. That cannot "
              "be repaired here, so it must be disclosed here",
              note="inline limitation disclosed in `run.bat help`")
    else:
        # POSIX hands over an argument vector with nothing in between, so the capability
        # exists and is asserted as a capability.
        ic = [*launcher(home), "call", "--tool", "ping", "--args-json", json.dumps(hostile)]
        ip = run(ic, cwd=home, timeout=300, env=clean_env(target))
        try:
            inline_echo = ((json.loads(ip.stdout).get("output") or {}).get("echo"))
        except ValueError:
            inline_echo = None
        check(step, "inline payloads survive the launcher unchanged",
              inline_echo == hostile["message"],
              f"rc={ip.returncode} sent={hostile['message']!r} got={inline_echo!r} - a shell "
              "that passes argv through has no excuse for altering a payload",
              note="inline round-trip intact")

    # THE LAUNCHER MUST BE ABLE TO SAY "NO", NOT JUST "FINE".
    #
    # Ten checks on the Windows leg rested on a zero exit code from a launcher whose
    # ability to return a NON-zero one had never been exercised. `run.bat` expanded
    # `%ERRORLEVEL%` inside a parenthesized block - at parse time, before the command ran -
    # so eight of its modes reported success unconditionally. `run smoke` sat for 184
    # seconds watching 88 tests fail and exited 0, and every check that trusted it was
    # recording the launcher's optimism rather than the product's behaviour.
    #
    # A channel that can only report success has not been tested. This asks for a tool
    # that cannot exist and requires the failure to come back through the same door the
    # successes do - deliberately through `cli`, which is one of the modes that was broken.
    bad = run([*launcher(home), "cli", "tool-call", "--tool", "__no_such_tool__",
               "--args-json", "{}"], cwd=home, timeout=300, env=clean_env(target))
    check(step, "the launcher reports FAILURE as well as success",
          bad.returncode != 0,
          f"rc={bad.returncode} for a tool that does not exist; a launcher that cannot "
          "return non-zero makes every exit-code check above meaningless",
          note=f"unknown-tool rc={bad.returncode} (want non-zero)")

    sm = run([*launcher(home), "smoke"], cwd=home, timeout=600, env=clean_env(target))
    sm_all = (sm.stdout or "") + (sm.stderr or "")
    # KEEP THE COUNTS WHETHER IT PASSED OR NOT. `rc` alone is a claim by the launcher;
    # the suite's own tally is the measurement, and on a launcher that cannot report a
    # non-zero code the tally is the ONLY thing that distinguishes 88 passes from 88
    # failures.
    tally = " · ".join(ln.strip() for ln in sm_all.splitlines()
                       if ln.startswith(("Ran ", "OK", "FAILED"))) or "(no unittest tally)"
    check(step, "the installed product can verify itself (`run smoke`)",
          sm.returncode == 0,
          f"rc={sm.returncode} tail={sm_all[-200:]!r}",
          note=f"rc={sm.returncode} · {tally[:150]}")

    att = out(tool_call(home, target, "attach", {"refresh": True}))
    aw = att.get("awareness") or {}
    check(step, "`attach` produces awareness of THIS target",
          bool(att) and (bool(att.get("project_map")) or bool(aw.get("revision"))),
          f"keys={sorted(att)[:9]} revision={aw.get('revision')!r}")

    check(step, "awareness reports its own limitations rather than inventing detail",
          isinstance(aw.get("limitations"), list) or "limitations" in aw
          or bool(att.get("project_map")),
          f"a thin target is a legitimate map; got {sorted(aw)[:8]}")

    if synopsis_probe:
        synopsis_truthfulness(step, att, target)

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
    # HANDLES ARE OBJECTS, NOT STRINGS. This filtered with `isinstance(h, str)` against a
    # contributor that returns {"tool", "id", "kind", "resolve_with"} dicts, so every handle
    # awareness promoted was discarded, the check below always read empty, and the loop fell
    # back to guessing a file - defeating the exact property the paragraph above says this
    # fixture has. The product was never asked; it offers five handles on this target.
    raw = before.get("handles") or []
    handles = [h.get("id") if isinstance(h, dict) else h for h in raw]
    handles = [h for h in handles if isinstance(h, str) and h]
    rel, live, via = None, None, "fallback scan"
    for h in handles:
        parts = [seg for seg in h.strip(".").split(".") if seg]
        for cand in (target.joinpath(*parts).with_suffix(".py"),
                     target.joinpath(*parts, "__init__.py")):
            if cand.is_file() and "ROLE:" in cand.read_text(encoding="utf-8",
                                                            errors="replace"):
                rel, live, via = cand.relative_to(target).as_posix(), cand, f"handle {h!r}"
                break
        if live is not None:
            break
    if live is None:
        cand = next((q for q in sorted((target / "src").rglob("*.py"))
                     if "ROLE:" in q.read_text(encoding="utf-8", errors="replace")
                     and q.name != "__init__.py"), None) \
            if (target / "src").is_dir() else None
        rel = cand.relative_to(target).as_posix() if cand else "README.md"
        live = target / rel
    # "CAN ACT ON" IS PART OF THE ASSERTION. A handle that names nothing this loop can
    # open is not a handle the loop can act on, and passing on `bool(handles)` alone would
    # let the fixture quietly go back to guessing while reporting the mechanism healthy.
    check(step, "T8: awareness names a handle the loop can act on",
          bool(handles) and via.startswith("handle"),
          f"handles={handles[:5]} chosen={rel!r} via={via}",
          note=f"source={rel!r} via={via}")
    original = live.read_text(encoding="utf-8", errors="replace")

    # EDIT SOMETHING THE PRODUCT SAYS IT OBSERVED, not something that merely lives in an
    # observed file.
    #
    # This edited "ROLE:" because that token is safe to mangle. It is also invisible to
    # identity. `canonical_observation` projects `report` down to one PURPOSE LINE per
    # module, and `_module_purposes` takes the first line of the module docstring when the
    # module has no documented class - which in this codebase's header convention is
    # always `FILE:`, never `ROLE:`. So the fixture changed a byte the projection
    # deliberately excludes and then asserted the projection had changed. `X == Y` was the
    # correct answer to the question actually being asked.
    #
    # The paragraph above promises that choosing the file by handle makes the edit
    # "guaranteed to touch an observed value". Choosing the FILE by handle guarantees the
    # file is observed; it says nothing about the edit. Asking the product for the purpose
    # it recorded, and editing THAT string, is what makes the promise true - the same move
    # as the handle, one level down.
    observed = out(tool_call(home, target, "report", {"path": rel}))
    purpose = next((str(m.get("purpose") or "")
                    for m in (observed.get("modules") or [])), "")
    token = next((w for w in purpose.split() if len(w) > 3 and w in original), None)
    if token is None:
        token = "ROLE:" if "ROLE:" in original else next(
            (w for w in ("project", "New", "#") if w in original), None)
    check(step, "T8: the loop can edit a value the product reports observing",
          bool(purpose) and token is not None and token in purpose,
          f"purpose={purpose[:80]!r} token={token!r} - an edit outside the observed "
          "projection cannot make a revision change, and asserting that it does tests "
          "nothing",
          note=f"observed purpose={purpose[:60]!r} editing token={token!r}")
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


# ============================================================ artifact identity
def seal(dist: Path, clone: Path, out_dir: Path) -> dict:
    """Archive the distribution once and give it an immutable identity.

    ONE ARTIFACT, TWO PLATFORMS. Windows must exercise the BYTE-IDENTICAL distribution
    Linux exercised; rebuilding from source on each machine would prove two different
    distributions and call the pair a release. The zip is also the documented shape -
    the installer README names `useful-helpers-toolkit.zip` - so sealing is not a new
    packaging step, it is the one already declared.

    The archive is written OUTSIDE the scratch workspace, because the workspace is
    reclaimed and the artifact must outlive it.
    """
    commit = run(["git", "rev-parse", "HEAD"], cwd=clone).stdout.strip()
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / "useful-helpers-release"
    if base.with_suffix(".zip").exists():
        base.with_suffix(".zip").unlink()
    archive = Path(shutil.make_archive(str(base), "zip", root_dir=str(dist)))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    ident = {"source_commit": commit, "archive": archive.name,
             "sha256": digest, "bytes": archive.stat().st_size}
    (out_dir / "ARTIFACT.json").write_text(json.dumps(ident, indent=2), encoding="utf-8")
    check("1 manufacture", "the distribution is sealed with an immutable identity",
          bool(commit) and len(digest) == 64,
          f"commit={commit[:12]} sha256={digest[:16]}… bytes={ident['bytes']}")
    return ident


def unseal(archive: Path, work: Path) -> tuple[Path, dict]:
    """Consume a PREBUILT artifact instead of manufacturing one (the Windows leg)."""
    ident = json.loads((archive.parent / "ARTIFACT.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    check("1 manufacture", "the supplied artifact matches its recorded hash",
          digest == ident.get("sha256"),
          f"expected {ident.get('sha256')} got {digest}; Release is only PASS when both "
          "platform records name the SAME artifact")
    dist = work / "artifact"
    shutil.unpack_archive(str(archive), str(dist))
    return dist / "useful-helpers-toolkit", ident


# ============================================================ the stop condition
def verifier_fingerprint() -> str:
    """WHICH INSTRUMENT PRODUCED THIS RECORD.

    Comparing the artifact across the two legs is not enough on its own: the same
    artifact measured by two different verifiers is two different experiments, and the
    artifact comparison cannot see the difference. This file is the instrument, so this
    file's digest is the instrument's identity.
    """
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def stop_condition(rec_dir: Path, ident: dict) -> None:
    """The two-platform stop condition, ASSERTED rather than described.

    THIS USED TO BE PROSE. `seal()` says "ONE ARTIFACT, TWO PLATFORMS" in a docstring and
    `unseal()` says "Release is only PASS when both platform records name the SAME
    artifact" inside a FAILURE DETAIL STRING - text that is only ever read when some
    OTHER check has already failed. Nothing loaded the two records and compared them, so
    the one condition the whole gate turns on was the one condition no code enforced.

    The failure this closes is not hypothetical. `seal()` unlinks and rebuilds the
    archive on every manufacturing run, so a Linux re-run after Windows has passed
    silently replaces the artifact the Windows record refers to. Both records then say
    PASS, both name a real artifact, and they are not the same artifact. Only a
    comparison catches that, and a comparison is what was missing.

    Read only the OTHER platform's record; this run's identity comes from memory, so the
    check does not depend on its own record having been written yet.
    """
    me = platform.system().lower()
    other = "windows" if me == "linux" else "linux"
    mine = (ident or {}).get("sha256") or ""
    p = rec_dir / f"release-{other}.json"
    mine_v = verifier_fingerprint()
    theirs, theirs_v, note = "", "", "that leg has not run"
    if p.is_file():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            note = "record is not readable JSON"
        else:
            theirs = ((d.get("artifact") or {}).get("sha256") or "")
            theirs_v = d.get("verifier") or ""
            failing = [c for c in d.get("checks", []) if not c.get("ok")]
            note = ("record carries no artifact identity - it predates sealing"
                    if not theirs else
                    f"{len(failing)} failing check(s) there" if failing else
                    "all checks pass there")
    check("3 stop condition",
          f"the {other} record names the SAME artifact this run exercised",
          bool(mine) and mine == theirs,
          f"this run={mine[:16] or '(none)'}… {other}={theirs[:16] or '(none)'}… "
          f"({note}) - one leg alone is not a release, and two legs naming different "
          "artifacts is not a release either")
    check("3 stop condition",
          f"the {other} record was produced by the SAME verifier source",
          bool(theirs_v) and mine_v == theirs_v,
          f"this run={mine_v[:16]}… {other}={theirs_v[:16] or '(none)'}… - the artifact "
          "comparison above cannot detect a changed instrument, so the instrument names "
          "itself")


# ============================================================ main
def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Closure Gate 2 - release verification")
    ap.add_argument("--artifact", default="",
                    help="consume this sealed .zip instead of manufacturing (Windows leg)")
    ap.add_argument("--keep-workspace", action="store_true",
                    help="DEBUGGING ONLY: do not reclaim the scratch workspace")
    ns = ap.parse_args(argv)

    out_dir = Path(__file__).parent / "artifact"
    rec = Path(__file__).parent / f"release-{platform.system().lower()}.json"
    work = Path(tempfile.mkdtemp(prefix="release-"))
    print(f"release verification on {platform.system()}  workspace={work}")
    ident: dict = {}

    def write_record() -> None:
        """WRITTEN FROM A `finally`, NOT FROM THE END OF THE HAPPY PATH.

        The workspace reclaim was already protected this way; the evidence was not. A run
        that stopped mid-walk therefore left a sealed artifact on disk and NO record at
        all - the artifact said a run had happened and nothing said what it found. The
        record is the only thing that outlives the run, so it is the last thing that
        should be conditional on the run finishing.
        """
        rec.write_text(json.dumps(
            {"platform": platform.system(), "python": platform.python_version(),
             "artifact": ident, "verifier": verifier_fingerprint(),
             "workspace_reclaimed": not ns.keep_workspace,
             "checks": CHECKS}, indent=2), encoding="utf-8")

    try:
        try:
            if ns.artifact:
                artifact, ident = unseal(Path(ns.artifact).resolve(), work)
                clone = work / "clean-clone"
                p = run(["git", "clone", "--quiet", str(DEV), str(clone)], timeout=900)
                check("1 manufacture", "a clean clone is available for the oracle controls",
                      p.returncode == 0, f"rc={p.returncode} {((p.stderr or '')[-160:])}")
            else:
                clone, artifact = manufacture(work)
                if artifact.is_dir():
                    ident = seal(artifact.parent, clone, out_dir)
            inspect(artifact, clone)
            if artifact.is_dir():
                walk(artifact, "A software", target_a(work, clone), full=True)
                walk(artifact, "B records", target_b(work), full=False)
                walk(artifact, "C empty", target_c(work), full=False,
                     synopsis_probe=True)
                oracles(artifact, work)
                oracles_from_clone(clone)
                removal(artifact, work)
        finally:
            # RECLAIM BY DEFAULT, INCLUDING AFTER A FAILURE.
            #
            # This kept every workspace "for inspection". Four runs later the sandbox was out
            # of disk, `git clone` died with "No space left on device", and the run recorded a
            # verifier-resource failure that looked exactly like a product result. An
            # instrument that consumes the bench it stands on eventually measures nothing.
            #
            # The diagnostic evidence a kept workspace was meant to provide is already in the
            # run record - every check carries its own detail - and that record is written
            # OUTSIDE the workspace, so reclaiming loses nothing that was being read anyway.
            # `--keep-workspace` remains for deliberate debugging; ordinary certification
            # never needs it.
            #
            # THE CLEAN-CLONE INVARIANT IS UNTOUCHED. Reclaiming is not reuse: every
            # authoritative run still clones fresh into a new workspace. Solving the disk
            # problem by keeping a clone around would trade a resource bug for an evidence
            # bug, which is the worse of the two.
            if ns.keep_workspace:
                print(f"workspace KEPT for debugging: {work}")
            elif reclaim(work):
                print(f"workspace reclaimed: {work}", flush=True)
            else:
                print(f"workspace NOT fully reclaimed: {work} - the hygiene check "
                      "below is the authority on this", flush=True)

        # THE LAST TWO CHECKS RUN BEFORE THE SUMMARY IS PRINTED, not after it. They used
        # to be appended once the report had already been rendered, so they counted
        # toward the exit status and toward the record while never appearing in the
        # output a human reads. A check nobody sees is not a check.
        leftovers = sorted(Path(tempfile.gettempdir()).glob("release-*"))
        check("0 hygiene", "the verifier leaves no workspace behind",
              ns.keep_workspace or not [d for d in leftovers if d.is_dir()],
              f"stale workspaces: {[d.name for d in leftovers][:6]} - each holds a full "
              "clone, and four of them exhausted the sandbox once already")
        stop_condition(Path(__file__).parent, ident)
    finally:
        write_record()

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
    print(f"record: {rec}")
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
