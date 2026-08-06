"""
FILE:       _harness/harness.py
ROLE:       The proving ground — point the sidecar at a target and record what actually happened.
DOMAIN:     factory (never ships; see _design/CHARTER.md §7)
DOES:       scaffold/adopt a target; install the sidecar into it; exercise the front door and every
            mounted Observe tool; take sha256 manifests before/after so ANY trace left in the target
            is caught mechanically; score the run against CHARTER §8; record run.json + report.md.
DEPENDS ON: (stdlib only) argparse, hashlib, json, shutil, subprocess, sys, time, pathlib
WIRES TO:   reads ../toolkit (the product under test); writes _harness/{targets,runs}/
NOTES:      Observe-only by design: the instrument is what is under test, so it is never allowed
            to modify the evidence. Scaffolded targets carry planted ground truth (bait from the
            field report's Part C) — see _ground_truth.json in each scaffold.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:      # so `import ro_mount` works however harness.py is invoked
    sys.path.insert(0, str(HERE))
FACTORY = HERE.parent
# The sidecar IS the repository root. There is no nested `toolkit/` folder: the
# ship boundary is the payload manifest below, not a directory.
TOOLKIT = FACTORY

# What must NEVER be copied into a target. The first group is regenerable noise;
# the second is development scaffolding that does not ship; `_harness` is also a
# RECURSION GUARD  -  targets live under `_harness/targets/`, so copying the root
# into one without excluding `_harness` would copy the target into itself.
_PAYLOAD_EXCLUDE = (
    "__pycache__", "*.pyc", "_artifacts", "logs", "workbench", ".venv", "_state",
    ".ruff_cache", ".pytest_cache", ".git", ".useful-helpers", ".useful-helpers-test-tmp",
    "_harness",                                # recursion guard - must stay
    ".bcc", "_docs", "gates", "_trash",        # development scaffolding
    ".plans-and-parts_FOR-REFERENCE-ONLY",     # parts bin
)
TARGETS = HERE / "targets"
RUNS = HERE / "runs"
SIDECAR_NAME = ".useful-helpers"

LINEAGE = ["mindshard", "parts-bin", "uimapper", "appfoundry", "bdneural", "legacy-helpers"]
SNAPSHOT_SKIP = {"__pycache__", ".git", ".venv", "venv", "node_modules", ".pytest_cache"}


# ---------------------------------------------------------------- snapshots / precept

def _rmtree(path: Path, tries: int = 5) -> None:
    """rmtree with backoff. On Windows a tool subprocess (e.g. a registry-refresh that touched the
    sqlite state) can briefly hold a handle, so the first rmtree raises 'Device or resource busy'.
    Retry a few times before giving up rather than crashing a run."""
    for i in range(tries):
        try:
            shutil.rmtree(path)
            return
        except FileNotFoundError:
            return
        except OSError:
            if i == tries - 1:
                raise
            time.sleep(0.3 * (i + 1))


def snapshot(root: Path, exclude_dir: str | None = None) -> dict[str, str]:
    """sha256 of every file under root, keyed by relative posix path.

    `exclude_dir` is the sidecar's own folder — everything else is the TARGET, and the target
    must not change. This is the precept check, and it is mechanical on purpose: we do not get
    to *notice* a violation, we get to *measure* one.
    """
    out: dict[str, str] = {}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        parts = set(rel.parts)
        if parts & SNAPSHOT_SKIP:
            continue
        if exclude_dir and rel.parts and rel.parts[0] == exclude_dir:
            continue
        try:
            out[rel.as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
        except OSError:
            out[rel.as_posix()] = "UNREADABLE"
    return out


def diff_snapshots(before: dict, after: dict) -> dict:
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    modified = sorted(k for k in set(before) & set(after) if before[k] != after[k])
    return {"added": added, "removed": removed, "modified": modified,
            "total": len(added) + len(removed) + len(modified)}


# ---------------------------------------------------------------- scaffolds

def _python_app(dest: Path) -> dict:
    """A small Typer-ish CLI + a service, carrying deliberate false-positive bait."""
    (dest / "app").mkdir(parents=True, exist_ok=True)
    (dest / "tests").mkdir(parents=True, exist_ok=True)

    (dest / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "0.1.0"\n'
        '[project.scripts]\ndemo = "app.cli:main"\n', encoding="utf-8")
    (dest / "requirements.txt").write_text("typer\n", encoding="utf-8")
    (dest / "README.md").write_text("# demo\n\nA scaffolded harness target.\n", encoding="utf-8")
    (dest / "app" / "__init__.py").write_text("", encoding="utf-8")

    # BAIT 1: decorator-registered commands. No static caller. They are LIVE.
    (dest / "app" / "cli.py").write_text(
        '"""CLI entrypoints. Registered by decorator — nothing calls these in-process."""\n'
        "import subprocess\n\n"
        "from app.service import Store, build_store\n\n\n"
        "class _App:\n"
        "    def __init__(self):\n"
        "        self.commands = {}\n\n"
        "    def command(self, fn):\n"
        "        self.commands[fn.__name__] = fn\n"
        "        return fn\n\n\n"
        "app = _App()\n\n\n"
        "@app.command\n"
        "def plan_list():\n"
        '    """BAIT: live command, zero static callers."""\n'
        "    return sorted(build_store().keys())\n\n\n"
        "@app.command\n"
        "def sync_repo():\n"
        '    """BAIT: subprocess in a SYNC function — correct, not blocking."""\n'
        '    return subprocess.run(["git", "status"], capture_output=True, text=True).returncode\n\n\n'
        "def main():\n"
        "    for name in app.commands:\n"
        "        print(name)\n",
        encoding="utf-8")

    # BAIT 3 (cartridge-only): a CUSTOM framework decorator not in dead_code's built-in list.
    # With naive args it reads HIGH-confidence dead; only a cartridge-supplied root ('schedule')
    # rescues it to a low lead. This is the bait that proves the policy layer changes behavior,
    # not just decorates it — the built-in Typer/ABC defaults cannot catch it.
    (dest / "app" / "jobs.py").write_text(
        '"""A tiny custom scheduler — its @schedule decorator is project-specific."""\n\n\n'
        "class _Scheduler:\n"
        "    def __init__(self):\n"
        "        self.jobs = {}\n\n"
        "    def schedule(self, fn):\n"
        "        self.jobs[fn.__name__] = fn\n"
        "        return fn\n\n\n"
        "scheduler = _Scheduler()\n\n\n"
        "@scheduler.schedule\n"
        "def nightly_cleanup():\n"
        '    """BAIT: live via @scheduler.schedule; \'schedule\' is not a built-in entrypoint."""\n'
        "    return True\n",
        encoding="utf-8")

    # BAIT 2: an interface method implemented but never directly called.
    (dest / "app" / "service.py").write_text(
        '"""Domain service + a provider interface."""\n'
        "import abc\n\n\n"
        "class Provider(abc.ABC):\n"
        "    @abc.abstractmethod\n"
        "    def normalize_name(self, raw: str) -> str:\n"
        '        """BAIT: implementations are live via the ABC, never called by name."""\n\n\n'
        "class LocalProvider(Provider):\n"
        "    def normalize_name(self, raw: str) -> str:\n"
        "        return raw.strip().lower()\n\n\n"
        "class Store(dict):\n"
        "    pass\n\n\n"
        "def build_store() -> Store:\n"
        "    s = Store()\n"
        "    s['alpha'] = 1\n"
        "    return s\n\n\n"
        "def genuinely_unused(x):\n"
        '    """NOT bait: this really is dead. A correct tool SHOULD flag it."""\n'
        "    return x * 2\n",
        encoding="utf-8")

    (dest / "tests" / "test_service.py").write_text(
        "from app.service import build_store\n\n\n"
        "def test_store():\n"
        "    assert build_store()['alpha'] == 1\n",
        encoding="utf-8")

    return {
        "kind": "python-app",
        "expected_domain": "python-app",
        "false_positive_bait": [
            {"symbol": "plan_list", "file": "app/cli.py", "tool": "dead_code",
             "why": "decorator-registered command; live with no static caller",
             "caught_by": "defaults"},
            {"symbol": "sync_repo", "file": "app/cli.py", "tool": "dead_code",
             "why": "decorator-registered command; live with no static caller",
             "caught_by": "defaults"},
            {"symbol": "sync_repo", "file": "app/cli.py", "tool": "blocking_call_scan",
             "why": "subprocess in a SYNC function is correct, not blocking",
             "caught_by": "not-mounted"},
            {"symbol": "normalize_name", "file": "app/service.py", "tool": "dead_code",
             "why": "interface method; live via the ABC",
             "caught_by": "defaults"},
            {"symbol": "nightly_cleanup", "file": "app/jobs.py", "tool": "dead_code",
             "why": "live via custom @scheduler.schedule; only a cartridge root rescues it",
             "caught_by": "cartridge"},
        ],
        "true_positives": [
            {"symbol": "genuinely_unused", "file": "app/service.py", "tool": "dead_code",
             "why": "actually dead; a correct tool should find this"},
        ],
    }


def _data_curation(dest: Path) -> dict:
    import csv
    import sqlite3
    (dest / "raw").mkdir(parents=True, exist_ok=True)
    for name, rows in (("people.csv", [("id", "name"), ("1", "ada"), ("2", "grace")]),
                       ("events.csv", [("id", "kind"), ("1", "login"), ("2", "logout")])):
        with (dest / "raw" / name).open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(rows)
    con = sqlite3.connect(dest / "warehouse.sqlite3")
    con.execute("CREATE TABLE person (id INTEGER PRIMARY KEY, name TEXT)")
    con.execute("INSERT INTO person VALUES (1, 'ada')")
    con.commit()
    con.close()
    (dest / "README.md").write_text("# dataset\n", encoding="utf-8")
    return {"kind": "data-curation", "expected_domain": "data-curation",
            "false_positive_bait": [], "true_positives": []}


def _records_research(dest: Path) -> dict:
    (dest / "case-files").mkdir(parents=True, exist_ok=True)
    for i in range(1, 4):
        (dest / "case-files" / f"memo-{i:02d}.txt").write_text(
            f"MEMO {i}\n\nRecord body for harness testing.\n", encoding="utf-8")
    (dest / "case-files" / "exhibit-a.pdf").write_bytes(
        b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n")
    (dest / "README.md").write_text("# case\n", encoding="utf-8")
    return {"kind": "records-research", "expected_domain": "records-research",
            "false_positive_bait": [], "true_positives": []}


def _web_app(dest: Path) -> dict:
    (dest / "src").mkdir(parents=True, exist_ok=True)
    (dest / "package.json").write_text(
        '{"name":"web","version":"0.1.0","scripts":{"dev":"vite"}}\n', encoding="utf-8")
    (dest / "tsconfig.json").write_text('{"compilerOptions":{"strict":true}}\n', encoding="utf-8")
    (dest / "index.html").write_text("<!doctype html><div id=app></div>\n", encoding="utf-8")
    for n in ("main.ts", "app.ts", "store.ts", "api.ts"):
        (dest / "src" / n).write_text(f"export const {n[:-3]} = () => null;\n", encoding="utf-8")
    (dest / "src" / "style.css").write_text("#app{color:red}\n", encoding="utf-8")
    return {"kind": "web-app", "expected_domain": "web-app",
            "false_positive_bait": [], "true_positives": []}


def _composite(dest: Path) -> dict:
    """A genuinely mixed target: a Python service, a TS front-end, and a records folder.

    The real monorepo we had to hand turned out to be 13 Python apps — homogeneous, so it
    exercised the per-subsystem machinery but never proved composite detection fires. This
    scaffold is that proof: three subsystems that must classify as three different domains.
    """
    _python_app(dest / "backend")
    (dest / "backend" / "_ground_truth.json").unlink(missing_ok=True)
    _web_app(dest / "frontend")
    _records_research(dest / "archive")
    (dest / "README.md").write_text("# composite\n\nbackend + frontend + archive\n", encoding="utf-8")
    return {
        "kind": "composite",
        # No expected_domain on purpose. A composite target HAS no meaningful whole-target
        # domain — whichever subsystem happens to carry a few more files wins, which is noise,
        # not signal. Asserting one would be scoring the instrument against a category error.
        # `expected_subsystem_domains` is the real contract here.
        "expected_domain": None,
        "expected_composite": True,
        "expected_subsystem_domains": {
            "backend": "python-app",
            "frontend": "web-app",
            "archive": "records-research",
        },
        "false_positive_bait": [],
        "true_positives": [],
    }


def _workspace(dest: Path) -> dict:
    """A declared monorepo whose members NEST under packages/ — not top-level dirs.

    This is the proof that declaration beats heuristic. The top-level-directory heuristic would
    see a single `packages` bucket of mixed files and classify it as one thing; only reading the
    pnpm-workspace.yaml recovers the two real members and their distinct domains.
    """
    (dest / "pnpm-workspace.yaml").write_text(
        "packages:\n  - 'packages/*'\n", encoding="utf-8")
    (dest / "package.json").write_text(
        '{"name":"root","private":true}\n', encoding="utf-8")
    _web_app(dest / "packages" / "web")
    _python_app(dest / "packages" / "api")
    (dest / "packages" / "api" / "_ground_truth.json").unlink(missing_ok=True)
    return {
        "kind": "workspace",
        "expected_domain": None,
        "expected_composite": True,
        "expected_subsystem_source": "workspace-manifest",
        "expected_subsystem_domains": {
            "packages/web": "web-app",
            "packages/api": "python-app",
        },
        "false_positive_bait": [],
        "true_positives": [],
    }


SCAFFOLDS = {"python-app": _python_app, "data-curation": _data_curation,
             "records-research": _records_research, "web-app": _web_app,
             "composite": _composite, "workspace": _workspace}


# ---------------------------------------------------------------- sidecar drive

def _call(sidecar: Path, tool: str, args: dict, timeout: int = 120) -> dict:
    """Drive one governed call. Uses --args-file to sidestep shell escaping entirely
    (field report F0 — hand-escaped JSON breaks the moment args get real)."""
    t0 = time.time()
    tmp = sidecar / "_harness_args.json"
    try:
        tmp.write_text(json.dumps(args), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-m", "src.app", "cli", "tool-call", "--tool", tool,
             "--args-file", str(tmp)],
            cwd=str(sidecar), capture_output=True, text=True, timeout=timeout)
        dt = round(time.time() - t0, 3)
        try:
            env = json.loads(proc.stdout)
            # The governed CLI envelope is {ok, tool_id, output, error, exit_code}. Its top-level
            # `ok` is AUTHORITATIVE — the seam can set it false (e.g. a precept-guard rejection)
            # even when the tool's own output.ok is true. Reading the inner ok would miss exactly
            # the enforcement case this harness exists to measure.
            if isinstance(env, dict) and "output" in env and "ok" in env:
                out = env.get("output") or {}
                ok = bool(env.get("ok"))
                error = env.get("error") or (out.get("error") if isinstance(out, dict) else None)
            else:
                out = env
                ok = bool(out.get("ok")) if isinstance(out, dict) else False
                error = out.get("error") if isinstance(out, dict) else None
            return {"tool": tool, "args": args, "ok": ok, "seconds": dt,
                    "output": out, "error": error}
        except json.JSONDecodeError:
            return {"tool": tool, "args": args, "ok": False, "seconds": dt, "output": None,
                    "error": f"unparseable envelope: {(proc.stdout or proc.stderr)[:300]}"}
    except subprocess.TimeoutExpired:
        return {"tool": tool, "args": args, "ok": False, "seconds": timeout, "output": None,
                "error": f"timeout after {timeout}s"}
    finally:
        tmp.unlink(missing_ok=True)


def _default_args(schema: dict, sample_file: str | None = None) -> dict | None:
    """Safe default args from a tool's input_schema. None = cannot call safely.

    A `root`-tool scans a directory, so `.` is right. A `path`-tool that isn't a directory scanner
    (e.g. read_file) needs a real FILE — use `sample_file` when the tool takes `path` but not
    `root`; skip if we have none."""
    props = (schema or {}).get("properties") or {}
    required = set((schema or {}).get("required") or [])
    if required - {"root", "path"}:
        return None  # needs something we cannot invent
    if "root" in props:
        return {"root": "."}
    if "path" in props:
        if sample_file is None:
            return None  # a file-taking tool with no directory scan and no sample file to feed
        return {"path": sample_file}
    if not props:
        return {}  # a pure no-arg tool (e.g. ping)
    return None  # has its own params but none we can safely invent (e.g. diff needs a/b) — skip


def _registry(sidecar: Path) -> list[dict]:
    p = sidecar / "config" / "registry.json"
    if not p.exists():
        subprocess.run([sys.executable, "-m", "src.app", "cli", "registry-refresh"],
                       cwd=str(sidecar), capture_output=True, text=True)
    return json.loads(p.read_text(encoding="utf-8"))["tools"]


_EVIL_TOOL = "harnessevilprobe"
_EVIL_MARK = "HARNESS_PRECEPT_PROBE.txt"


def _probe_enforcement(sidecar: Path, target: Path) -> dict:
    """The Phase 4 acceptance, measured: inject an Observe tool that WRITES to the target and
    confirm the governed seam REJECTS the call. Detection, not prevention (no OS sandbox here) —
    so we also confirm the write happened, proving the guard caught a real violation, then clean
    up entirely. Fully reverted: the fixture and its write are removed before returning.
    """
    tdir = sidecar / "tools" / _EVIL_TOOL
    mark = target / _EVIL_MARK
    try:
        tdir.mkdir(parents=True, exist_ok=True)
        (tdir / "tool.json").write_text(json.dumps({
            "id": _EVIL_TOOL, "summary": "harness precept probe (writes to the target)",
            "category": "introspection", "authority": "Observe", "operates_on": "project",
            "invocation": {"interpreter": "${ROOT_VENV_PYTHON}",
                           "entry": f"tools/{_EVIL_TOOL}/cli.py"},
            "input_schema": {"type": "object", "properties": {}},
        }), encoding="utf-8")
        (tdir / "cli.py").write_text(
            "from __future__ import annotations\n"
            "from pathlib import Path\n"
            "from tools._toolkit import tool_main\n\n\n"
            "@tool_main\n"
            "def run(args: dict) -> dict:\n"
            f"    # An Observe tool has no business writing the target. Do it anyway.\n"
            f"    Path('{_EVIL_MARK}').write_text('i should not exist', encoding='utf-8')\n"
            "    return {'ok': True, 'did': 'wrote to the target'}\n",
            encoding="utf-8")
        subprocess.run([sys.executable, "-m", "src.app", "cli", "registry-refresh"],
                       cwd=str(sidecar), capture_output=True, text=True)
        r = _call(sidecar, _EVIL_TOOL, {})
        wrote = mark.exists()
        rejected = (not r.get("ok")) and ("precept" in (r.get("error") or "").lower())
        return {"tested": True, "rejected": rejected, "detected_write": wrote,
                "error": r.get("error")}
    finally:
        shutil.rmtree(tdir, ignore_errors=True)
        mark.unlink(missing_ok=True)
        subprocess.run([sys.executable, "-m", "src.app", "cli", "registry-refresh"],
                       cwd=str(sidecar), capture_output=True, text=True)


def install(target: Path, method: str) -> dict:
    sidecar = target / SIDECAR_NAME
    if sidecar.exists():
        _rmtree(sidecar)
    if method == "copy":
        shutil.copytree(TOOLKIT, sidecar, ignore=shutil.ignore_patterns(
            *_PAYLOAD_EXCLUDE))
        # A vended sidecar is defined by its marker: that is the evidence it was
        # installed, and the only thing binding it to its parent as its target.
        # Copy mode deliberately skips the installer TOOL, but must still produce a
        # faithfully installed sidecar - without the marker the copy has no target
        # and every tool call correctly refuses. See src/core/config.py.
        (sidecar / ".suite_sidecar").write_text(
            "installed by _harness (copy mode)\n", encoding="utf-8")
        return {"method": "copy", "ok": True}
    # method == "tool": exercise the real installer. Expected to violate the precept today.
    staging = FACTORY / "_harness" / ".staging"
    if staging.exists():
        _rmtree(staging)
    shutil.copytree(TOOLKIT, staging, ignore=shutil.ignore_patterns(
        *_PAYLOAD_EXCLUDE))
    res = _call(staging, "sidecar_install",
                {"target": str(target), "dry_run": False, "confirm": True}, timeout=300)
    shutil.rmtree(staging, ignore_errors=True)
    return {"method": "tool", "ok": res["ok"], "detail": res.get("error"),
            "output": res.get("output")}


# ---------------------------------------------------------------- scoring

def _lineage_hits(sidecar: Path) -> int:
    """Count prior-project lineage in the toolkit's own CODE.

    Scans code, shipped config, AND docs. Deliberately skips `_state/` (and `_artifacts/`): those
    hold engagement data that *describes the target*, and a target may legitimately contain a
    directory named e.g. `_UiMAPPER`. Counting the target's own names as toolkit lineage is the
    instrument mistaking what it observes for what it is — the exact class of bug this whole
    effort is about. (`_docs/` used to be exempt; Phase 5 regenerated it clean, so it is now scanned.)
    """
    skip_roots = {"_state", "_artifacts", "_exports", "logs", "__pycache__"}
    hits = 0
    for p in sidecar.rglob("*"):
        if not p.is_file() or p.suffix not in {".py", ".json", ".md", ".toml", ".bat", ".txt"}:
            continue
        if set(p.relative_to(sidecar).parts) & skip_roots:
            continue
        try:
            low = p.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        hits += sum(low.count(term) for term in LINEAGE)
    return hits


_SEVERITY = {"low": 1, "medium": 2, "high": 3}


def _dead_code_confidence(sidecar: Path, args: dict):
    """Run dead_code and return {symbol -> most-severe confidence reported}, plus the raw run."""
    r = _call(sidecar, "dead_code", args)
    if not r.get("ok"):
        return None, r
    worst: dict[str, str] = {}
    for c in (r.get("output") or {}).get("candidates") or []:
        name, conf = c.get("name"), c.get("confidence", "low")
        if name and (name not in worst or _SEVERITY.get(conf, 0) > _SEVERITY.get(worst[name], 0)):
            worst[name] = conf
    return worst, r


def _verdict(worst: dict | None, symbol: str) -> str:
    """A finding is a FALSE_POSITIVE only if live code is reported at HIGH/MEDIUM confidence — a
    call an agent would act on. A LOW-confidence lead with a correct note is not a lie; it is the
    signal the charter (§4) asks for. Absent entirely = correctly_ignored."""
    if worst is None:
        return "not_run"
    conf = worst.get(symbol)
    if conf is None:
        return "correctly_ignored"
    return "FALSE_POSITIVE" if conf in ("high", "medium") else "labeled_lead"


def _score_bait(ground: dict, sidecar: Path, policy: dict) -> dict:
    """Score planted bait by CONFIDENCE, and MEASURE what the cartridge policy adds.

    dead_code is run twice — naive (`{"root":"."}`) and policy (naive + the cartridge's
    pre-bound `tool_args`) — so the delta between them is the measured value of the policy layer,
    not an assertion about it. Bait for tools the cartridge does not mount (e.g. blocking_call_scan)
    is `not-mounted`, which is itself the correct outcome: the cartridge declined to mount a liar.
    """
    dc_policy_args = dict((policy.get("dead_code") or {}).get("tool_args") or {})
    naive, _ = _dead_code_confidence(sidecar, {"root": "."})
    pol, pol_run = _dead_code_confidence(sidecar, {"root": ".", **dc_policy_args})

    findings = []
    for bait in ground.get("false_positive_bait", []):
        if bait["tool"] != "dead_code":
            findings.append({**bait, "naive_verdict": "not-mounted", "policy_verdict": "not-mounted"})
            continue
        findings.append({**bait,
                         "naive_verdict": _verdict(naive, bait["symbol"]),
                         "policy_verdict": _verdict(pol, bait["symbol"])})
    tps = []
    for tp in ground.get("true_positives", []):
        if tp["tool"] != "dead_code":
            tps.append({**tp, "verdict": "not_run"})
            continue
        conf = (pol or {}).get(tp["symbol"])
        tps.append({**tp, "verdict": "found" if conf else "MISSED", "confidence": conf})

    naive_fp = sum(1 for f in findings if f.get("naive_verdict") == "FALSE_POSITIVE")
    policy_fp = sum(1 for f in findings if f.get("policy_verdict") == "FALSE_POSITIVE")
    return {
        "findings": findings + tps,
        "naive_false_positives": naive_fp,
        "policy_false_positives": policy_fp,
        "policy_prevented": naive_fp - policy_fp,
        "false_positives": policy_fp,  # headline: the faithful (policy-applied) number
        "missed_true_positives": sum(1 for t in tps if t["verdict"] == "MISSED"),
        "dead_code_ran": pol is not None,
    }


def score(run: dict) -> dict:
    inst = run["precept"]["install"]
    rt = run["precept"]["runtime"]
    precept_ok = inst["total"] == 0 and rt["total"] == 0

    at = run.get("attach") or {}
    ao = at.get("output") or {}
    front_ok = bool(at.get("ok")) and bool(ao.get("project_map")) and \
        bool((ao.get("workbench") or {}).get("mounted")) and bool(ao.get("next"))

    runs = run.get("tool_runs") or []
    ran = [r for r in runs if not r.get("skipped")]
    ok = [r for r in ran if r.get("ok")]
    bait = run.get("bait") or {}
    enf = run.get("enforcement") or {}

    ground = run.get("ground_truth") or {}
    pmap = ao.get("project_map") or {}
    domain_ok = None
    exp = ground.get("expected_domain")
    if exp:
        domain_ok = pmap.get("domain") == exp

    # Composition: did it notice the target is more than one thing, and place each part?
    comp = None
    if "expected_composite" in ground or ground.get("expected_subsystem_domains"):
        got_subs = {s["name"]: s.get("domain") for s in pmap.get("subsystems") or []}
        want_subs = ground.get("expected_subsystem_domains") or {}
        wrong = {k: {"expected": v, "got": got_subs.get(k)}
                 for k, v in want_subs.items() if got_subs.get(k) != v}
        want_source = ground.get("expected_subsystem_source")
        got_source = pmap.get("subsystem_source")
        comp = {
            "composite": pmap.get("composite"),
            "composite_expected": ground.get("expected_composite"),
            "composite_correct": pmap.get("composite") == ground.get("expected_composite")
            if "expected_composite" in ground else None,
            "subsystems_correct": len(want_subs) - len(wrong),
            "subsystems_expected": len(want_subs),
            "source": got_source,
            "source_expected": want_source,
            "source_correct": (got_source == want_source) if want_source else None,
            "mismatches": wrong,
        }

    return {
        "precept": {"pass": precept_ok,
                    "install_violations": inst["total"], "runtime_violations": rt["total"]},
        "front_door": {"pass": front_ok, "mode": ao.get("mode"),
                       "domain": pmap.get("domain"),
                       "domain_expected": exp, "domain_correct": domain_ok,
                       "mounted": len((ao.get("workbench") or {}).get("mounted") or [])},
        "composition": comp,
        "tool_health": {"ran": len(ran), "ok": len(ok), "failed": len(ran) - len(ok),
                        "skipped": len(runs) - len(ran),
                        "rate": round(len(ok) / len(ran), 3) if ran else None,
                        "failures": [{"tool": r["tool"], "error": (r.get("error") or "")[:160]}
                                     for r in ran if not r.get("ok")]},
        "truthfulness": {"false_positives": bait.get("false_positives"),
                         "naive_false_positives": bait.get("naive_false_positives"),
                         "policy_prevented": bait.get("policy_prevented"),
                         "missed_true_positives": bait.get("missed_true_positives")},
        "enforcement": {"pass": bool(enf.get("rejected")), "rejected": enf.get("rejected"),
                        "detected_write": enf.get("detected_write")} if enf else None,
        "cleanliness": {"pass": run["lineage_hits"] == 0, "hits": run["lineage_hits"]},
    }


# ---------------------------------------------------------------- seam-completeness (C0)
# The ruler for the completion plan: can an agent do everything THROUGH the sidecar, or must it
# reach for its own hands? Two measures — a static capability checklist and a live self-hosting
# scenario. Both read low today and burn down as COMPLETION_PLAN phases land.

# Each capability an agent needs -> the tool id(s) that satisfy it. Present if any is registered.
CAPABILITIES = {
    "orient":       ["attach"],
    "grep":         ["repo_search"],
    "read-file":    ["read_file"],
    "glob":         ["glob"],
    "edit-exact":   ["edit"],
    "patch":        ["patch"],
    "write-file":   ["write_file"],
    "fs-mutate":    ["fs_op"],
    "exec":         ["project_run"],
    "diff":         ["diff"],
    "sqlite-read":  ["sqlite_inspect"],
    "sqlite-write": ["sqlite_exec"],
    "dep-install":  ["dep_install"],
    "web-search":   ["web_search"],
    "http":         ["http_probe", "fetch"],
    "git":          ["git_inspect", "git"],
    "remember":     ["journal", "evidence"],
    "delegate":     ["delegate"],
}


def _capability_coverage(reg_ids: set) -> dict:
    rows = []
    for cap, tools in CAPABILITIES.items():
        hit = next((t for t in tools if t in reg_ids), None)
        rows.append({"capability": cap, "tool": hit, "present": hit is not None,
                     "candidates": tools})
    present = sum(1 for r in rows if r["present"])
    return {"present": present, "total": len(rows),
            "pct": round(present / len(rows), 3),
            "missing": [r["capability"] for r in rows if not r["present"]],
            "rows": rows}


# The canonical engagement: read -> search -> edit -> create -> run -> test -> inspect-data ->
# dep(dry) -> discover -> remember -> commit. Each step names the capability + a concrete call.
def _scenario_steps() -> list[dict]:
    return [
        {"cap": "orient",       "tool": "attach",         "args": {}},
        {"cap": "grep",         "tool": "repo_search",    "args": {"root": ".", "query": "def"}},
        {"cap": "read-file",    "tool": "read_file",      "args": {"path": "README.md"}},
        {"cap": "glob",         "tool": "glob",           "args": {"pattern": "**/*.py"}},
        {"cap": "edit-exact",   "tool": "edit",           "args": {"path": "README.md",
                                                                   "pattern": "demo",
                                                                   "replacement": "demo"}},
        {"cap": "write-file",   "tool": "write_file",     "args": {"path": "_seam_probe.txt",
                                                                   "content": "probe"}},
        {"cap": "fs-mutate",    "tool": "fs_op",          "args": {"op": "mkdir",
                                                                   "path": "_seam_dir",
                                                                   "apply": True}},
        {"cap": "exec",         "tool": "project_run",    "args": {"command": "python --version",
                                                                   "apply": True}},
        {"cap": "sqlite-read",  "tool": "sqlite_inspect", "args": {"db": "seam.sqlite3"}},
        {"cap": "sqlite-write", "tool": "sqlite_exec",    "args": {"db": "seam.sqlite3",
                                                                   "sql": "INSERT INTO t VALUES (1)"}},
        {"cap": "diff",         "tool": "diff",           "args": {"a": "README.md", "b": "README.md"}},
        # preview only (no apply): lists the whole batch; create_venv makes the plan resolvable
        # without touching the system interpreter.
        {"cap": "dep-install",  "tool": "dep_install",    "args": {"create_venv": True}},
        {"cap": "web-search",   "tool": "web_search",     "args": {"query": "python packaging"}},
        {"cap": "remember",     "tool": "journal",        "args": {"action": "add",
                                                                   "title": "seam probe",
                                                                   "summary": "self-hosting scenario"}},
        {"cap": "git",          "tool": "git_inspect",    "args": {"action": "status"}},
    ]


def _run_scenario(sidecar: Path, reg_ids: set) -> dict:
    """Drive the canonical engagement through the seam. Each step is: blocked (no such tool yet),
    ok (ran, ok:true), or failed (ran, ok:false — usually environmental, still IN the seam)."""
    steps = []
    for st in _scenario_steps():
        if st["tool"] not in reg_ids:
            steps.append({**st, "outcome": "blocked"})
            continue
        r = _call(sidecar, st["tool"], st["args"])
        steps.append({**st, "outcome": "ok" if r.get("ok") else "failed",
                      "error": None if r.get("ok") else (r.get("error") or "")[:120]})
    blocked = [s for s in steps if s["outcome"] == "blocked"]
    failed = [s for s in steps if s["outcome"] == "failed"]
    return {"total": len(steps), "ok": sum(1 for s in steps if s["outcome"] == "ok"),
            "blocked": len(blocked), "failed": len(failed),
            "seam_complete": len(blocked) == 0,
            "blocking_tools": sorted({s["tool"] for s in blocked}),
            "steps": steps}


def cmd_mount(a):
    """M1: prove the precept by PREVENTION, not detection.

    Phase 4 detects a violation after it lands. This mounts the target read-only so the OS
    refuses the write outright, and then asks the question that actually matters: with the
    target sealed, does the sidecar still WORK? Prevention that breaks the instrument proves
    nothing worth having.

    DEPLOYMENT NOTE (found by building this): a read-only target forces the sidecar OUT of the
    target directory. The normal `<target>/.useful-helpers/` layout cannot work against a sealed
    target because the sidecar must write its own state. So this models the audit posture -
    external sidecar, SUITE_PROJECT_ROOT pointed at a read-only target - which is exactly the
    shape a CI check or a forensic review wants. It does not model in-target deployment, and
    saying so is the point.
    """
    import ro_mount

    target = TARGETS / a.name
    if not target.is_dir():
        sys.exit(f"no such target: {target}  (scaffold or adopt it first)")

    print(f"M1 read-only mount probe\n  target: {target}")
    cap = ro_mount.capability()
    print(f"  capability: available={cap['available']} strategy={cap['strategy']}")
    print(f"    {cap['reason']}")

    if not cap["available"]:
        # An unavailable dimension is UNAVAILABLE, never a pass. Exit 0 (nothing failed) but
        # the word `unavailable` is the whole report - no green light is implied anywhere.
        print("\n  MOUNT       UNAVAILABLE - dimension not measured on this host")
        print("  (run under Linux, or in CI, to exercise it)")
        return {"available": False, **cap}

    st = ro_mount.self_test()
    print(f"  rig self-test: readable={st.get('readable')} write_refused={st.get('write_refused')}")
    if not st.get("ok"):
        print("\n  MOUNT       FAIL - the rig itself is not read-only; no result is trustworthy")
        print(f"    {st.get('raw')} / {st.get('stderr')}")
        sys.exit(1)

    staging = Path(tempfile.mkdtemp(prefix="m1-sidecar-"))
    sidecar = staging / "sidecar"
    try:
        shutil.copytree(TOOLKIT, sidecar, ignore=shutil.ignore_patterns(
            *_PAYLOAD_EXCLUDE))
        inner = HERE / "ro_probe_inner.py"
        cmd = f'{sys.executable} {str(inner)!r} {str(sidecar)!r}'
        before = snapshot(target, exclude_dir=SIDECAR_NAME)
        r = ro_mount.run_under_read_only(str(target), cmd, strategy=cap["strategy"])
        after = snapshot(target, exclude_dir=SIDECAR_NAME)
        d = diff_snapshots(before, after)

        payload = {}
        for line in (r["stdout"] or "").splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    payload = json.loads(line)
                except ValueError:
                    continue
        if not payload:
            print("\n  MOUNT       FAIL - probe produced no result")
            print(f"    stdout: {(r['stdout'] or '')[:400]}")
            print(f"    stderr: {(r['stderr'] or '')[:400]}")
            sys.exit(1)

        sealed = payload.get("mount_sealed")
        prevented = payload.get("prevented")
        usable = payload.get("still_usable")
        print(f"\n  mount sealed:     {sealed}  ({payload.get('mount_note', '')[:70]})")
        print(f"  violation PREVENTED: {prevented}  "
              f"(call_ok={payload.get('violation_call_ok')} "
              f"file_created={payload.get('violation_file_exists')})")
        print("  sidecar still usable against a sealed target:")
        for tool, res in (payload.get("usable") or {}).items():
            flag = "OK " if res.get("ok") else "FAIL"
            print(f"    {flag} {tool}{'  ' + str(res.get('error'))[:60] if not res.get('ok') else ''}")
        print(f"  source target unchanged: delta={d['total']}")

        ok = bool(sealed and prevented and usable and d["total"] == 0)
        print(f"\n  MOUNT       {'PASS' if ok else 'FAIL'}  "
              f"(prevention={prevented}, usable={usable}, target delta={d['total']})")
        result = {"available": True, "strategy": cap["strategy"], "self_test": st,
                  "target_delta": d["total"], "ok": ok, **payload}
        if not ok:
            sys.exit(1)
        return result
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def cmd_seam(_a):
    import sqlite3
    import subprocess as sp
    # Give web_search a provider so its PREVIEW path is exercisable. Preview makes no network
    # call — it only reports what would be sent where — so this proves the capability is reachable
    # through the seam without depending on a live search service. setdefault: a real operator
    # configuration always wins.
    os.environ.setdefault("SUITE_SEARCH_PROVIDER", "searxng")
    os.environ.setdefault("SUITE_SEARCH_URL", "http://localhost:8888")
    target = TARGETS / "_seam"
    if target.exists():
        _rmtree(target)
    _python_app(target)
    (target / "_ground_truth.json").unlink(missing_ok=True)
    con = sqlite3.connect(target / "seam.sqlite3")
    con.execute("CREATE TABLE t (id INTEGER)")
    con.commit()
    con.close()
    try:
        sp.run(["git", "init"], cwd=str(target), capture_output=True, text=True, timeout=30)
    except (OSError, sp.SubprocessError):
        pass

    install(target, "copy")
    sidecar = target / SIDECAR_NAME
    reg_ids = {t["id"] for t in _registry(sidecar)}
    cov = _capability_coverage(reg_ids)
    scenario = _run_scenario(sidecar, reg_ids)

    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}-seam"
    out_dir = RUNS / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "seam.json").write_text(
        json.dumps({"coverage": cov, "scenario": scenario}, indent=2) + "\n", encoding="utf-8")
    _rmtree(target)

    print(f"SEAM-COMPLETENESS  (run {run_id})\n")
    print(f"  CAPABILITY COVERAGE  {cov['present']}/{cov['total']}  ({int(cov['pct'] * 100)}%)")
    for r in cov["rows"]:
        mark = "OK " if r["present"] else "-- "
        print(f"    {mark} {r['capability']:<13} {r['tool'] or '(missing: ' + '/'.join(r['candidates']) + ')'}")
    print(f"\n  SELF-HOSTING SCENARIO  seam_complete={scenario['seam_complete']}  "
          f"(ok={scenario['ok']} blocked={scenario['blocked']} failed={scenario['failed']})")
    for s in scenario["steps"]:
        mark = {"ok": "OK ", "blocked": "XX ", "failed": "!! "}[s["outcome"]]
        extra = f"  <- {s['tool']}" if s["outcome"] == "blocked" else (
            f"  ({s.get('error')})" if s["outcome"] == "failed" else "")
        print(f"    {mark} {s['cap']:<13} {s['tool']}{extra}")
    print(f"\n  recorded: {out_dir}")


# ---------------------------------------------------------------- commands

def cmd_scaffold(a):
    dest = TARGETS / a.name
    if dest.exists() and not a.force:
        sys.exit(f"target exists: {dest} (use --force)")
    if dest.exists():
        _rmtree(dest)
    dest.mkdir(parents=True)
    ground = SCAFFOLDS[a.kind](dest)
    (dest / "_ground_truth.json").write_text(json.dumps(ground, indent=2) + "\n", encoding="utf-8")
    n = sum(1 for _ in dest.rglob("*") if _.is_file())
    print(f"scaffolded {a.kind} -> {dest}  ({n} files, "
          f"{len(ground['false_positive_bait'])} planted bait)")


def cmd_adopt(a):
    src = Path(a.path).expanduser().resolve()
    if not src.is_dir():
        sys.exit(f"not a directory: {src}")
    dest = TARGETS / (a.name or src.name)
    if dest.exists() and not a.force:
        sys.exit(f"target exists: {dest} (use --force)")
    if dest.exists():
        _rmtree(dest)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(
        "__pycache__", "*.pyc", ".venv", "venv", "node_modules", SIDECAR_NAME))
    n = sum(1 for _ in dest.rglob("*") if _.is_file())
    print(f"adopted {src} -> {dest}  ({n} files)")
    print("note: copied, not moved. The original is untouched.")


def cmd_list(_a):
    print("TARGETS")
    for d in sorted(TARGETS.glob("*")) if TARGETS.exists() else []:
        if d.is_dir():
            n = sum(1 for _ in d.rglob("*") if _.is_file())
            gt = "  (ground truth)" if (d / "_ground_truth.json").exists() else ""
            print(f"  {d.name:<28} {n:>5} files{gt}")
    print("\nRUNS")
    for d in sorted(RUNS.glob("*"), reverse=True) if RUNS.exists() else []:
        rj = d / "run.json"
        if rj.exists():
            r = json.loads(rj.read_text(encoding="utf-8"))
            s = r.get("score", {})
            p = "PASS" if s.get("precept", {}).get("pass") else "FAIL"
            print(f"  {d.name:<28} target={r.get('target'):<18} precept={p} "
                  f"tools={s.get('tool_health', {}).get('ok')}/{s.get('tool_health', {}).get('ran')}")


def cmd_run(a):
    target = TARGETS / a.name
    if not target.is_dir():
        sys.exit(f"no such target: {target}  (scaffold or adopt it first)")

    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{a.name}"
    out_dir = RUNS / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"run {run_id}\n  target: {target}")

    ground = {}
    gt = target / "_ground_truth.json"
    if gt.exists():
        ground = json.loads(gt.read_text(encoding="utf-8"))

    # 1. the target, before the instrument ever touches it
    before = snapshot(target, exclude_dir=SIDECAR_NAME)
    print(f"  snapshot: {len(before)} target files")

    # 2. install
    inst = install(target, a.install)
    after_install = snapshot(target, exclude_dir=SIDECAR_NAME)
    d_install = diff_snapshots(before, after_install)
    print(f"  install ({inst['method']}): ok={inst['ok']}  precept delta={d_install['total']}")
    for f in (d_install["added"] + d_install["modified"])[:5]:
        print(f"    !! {f}")

    sidecar = target / SIDECAR_NAME

    # 3. front door
    at = _call(sidecar, "attach", {})
    ao = at.get("output") or {}
    print(f"  attach: ok={at['ok']} mode={ao.get('mode')} "
          f"domain={(ao.get('project_map') or {}).get('domain')}")

    # 4. exercise the mounted Observe tools — AS THE WORKBENCH DIRECTS: the cartridge's pre-bound
    #    tool_args are merged in, so the harness tests the tool the way an agent following `next`
    #    would call it, not with naive defaults.
    workbench = ao.get("workbench") or {}
    policy = workbench.get("policy") or {}
    mounted = workbench.get("mounted") or []
    reg = {t["id"]: t for t in _registry(sidecar)}
    # A real file in the target (relative), to feed file-taking tools like read_file. Exclude the
    # installed sidecar via the path RELATIVE to the target — an absolute-parts check would also
    # match the sandbox root when it happens to be named `.useful-helpers`.
    sample_file = next(
        (rel.as_posix() for rel in
         (p.relative_to(target) for p in sorted(target.rglob("*")) if p.is_file())
         if SIDECAR_NAME not in rel.parts
         and rel.suffix in {".py", ".md", ".txt", ".json", ".toml"}),
        None)
    tool_runs = []
    for tid in mounted:
        meta = reg.get(tid)
        if not meta:
            tool_runs.append({"tool": tid, "skipped": True, "reason": "not in registry"})
            continue
        if meta.get("authority") != "Observe":
            tool_runs.append({"tool": tid, "skipped": True,
                              "reason": f"authority={meta.get('authority')} (harness is Observe-only)"})
            continue
        args = _default_args(meta.get("input_schema"), sample_file=sample_file)
        if args is None:
            tool_runs.append({"tool": tid, "skipped": True, "reason": "requires args"})
            continue
        args = {**args, **((policy.get(tid) or {}).get("tool_args") or {})}
        tool_runs.append(_call(sidecar, tid, args))
        r = tool_runs[-1]
        print(f"    {tid:<22} ok={str(r['ok']):<5} {r['seconds']:>6.2f}s"
              f"{'  ' + (r.get('error') or '')[:60] if not r['ok'] else ''}")

    # 5. the target, after everything
    after_run = snapshot(target, exclude_dir=SIDECAR_NAME)
    d_runtime = diff_snapshots(after_install, after_run)
    print(f"  runtime precept delta: {d_runtime['total']}")
    for f in (d_runtime["added"] + d_runtime["modified"])[:5]:
        print(f"    !! {f}")

    # 6. enforcement: does the seam REJECT an Observe tool that writes to the target? (isolated,
    #    fully cleaned up — runs after the runtime snapshot so its transient write is invisible.)
    enforcement = _probe_enforcement(sidecar, target)
    print(f"  enforcement: rejected={enforcement['rejected']} "
          f"(detected_write={enforcement['detected_write']})")

    run = {
        "run_id": run_id, "target": a.name, "target_path": str(target),
        "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "install": inst,
        "ground_truth": ground,
        "target_census": {"file_count": len(before)},
        "precept": {"install": d_install, "runtime": d_runtime},
        "attach": at, "tool_runs": tool_runs,
        "bait": _score_bait(ground, sidecar, policy) if ground.get("false_positive_bait") else {},
        "enforcement": enforcement,
        "lineage_hits": _lineage_hits(sidecar),
    }
    run["score"] = score(run)

    (out_dir / "run.json").write_text(json.dumps(run, indent=2, default=str) + "\n", encoding="utf-8")
    (out_dir / "report.md").write_text(render(run), encoding="utf-8")
    print(f"\n{render_summary(run)}")
    print(f"  recorded: {out_dir}")


def render_summary(run: dict) -> str:
    s = run["score"]
    lines = [
        f"  PRECEPT      {'PASS' if s['precept']['pass'] else 'FAIL'}  "
        f"(install={s['precept']['install_violations']} runtime={s['precept']['runtime_violations']})",
        f"  FRONT DOOR   {'PASS' if s['front_door']['pass'] else 'FAIL'}  "
        f"domain={s['front_door']['domain']} expected={s['front_door']['domain_expected']} "
        f"correct={s['front_door']['domain_correct']} mounted={s['front_door']['mounted']}",
        f"  TOOL HEALTH  {s['tool_health']['ok']}/{s['tool_health']['ran']} ok "
        f"({s['tool_health']['skipped']} skipped)",
        f"  TRUTHFULNESS false_positives={s['truthfulness']['false_positives']} "
        f"(naive {s['truthfulness']['naive_false_positives']}, "
        f"policy prevented {s['truthfulness']['policy_prevented']}) "
        f"missed={s['truthfulness']['missed_true_positives']}",
        f"  CLEANLINESS  {'PASS' if s['cleanliness']['pass'] else 'FAIL'} "
        f"({s['cleanliness']['hits']} lineage hits)",
    ]
    e = s.get("enforcement")
    if e:
        lines.append(f"  ENFORCEMENT  {'PASS' if e['pass'] else 'FAIL'}  "
                     f"(seam rejected a target-writing Observe tool = {e['rejected']}, "
                     f"write detected = {e['detected_write']})")
    c = s.get("composition")
    if c:
        src = f" src={c['source']}" + ("" if c["source_correct"] is None
                                        else f"({c['source_correct']})")
        lines.insert(2, f"  COMPOSITION  composite={c['composite']} "
                        f"(expected {c['composite_expected']}) -> {c['composite_correct']}  "
                        f"subsystems {c['subsystems_correct']}/{c['subsystems_expected']} placed{src}")
    return "\n".join(lines)


def render(run: dict) -> str:
    s = run["score"]
    L = [f"# Harness run — {run['run_id']}", "",
         f"**Target:** `{run['target']}` ({run['target_census']['file_count']} files) · "
         f"**Install:** {run['install']['method']} · **At:** {run['at']}", "",
         "## Scorecard", "", "| Dimension | Result |", "|---|---|",
         f"| Precept (charter §1) | **{'PASS' if s['precept']['pass'] else 'FAIL'}** — "
         f"install {s['precept']['install_violations']}, runtime {s['precept']['runtime_violations']} |",
         f"| Front door (§8.2) | **{'PASS' if s['front_door']['pass'] else 'FAIL'}** — "
         f"mode {s['front_door']['mode']}, {s['front_door']['mounted']} tools mounted |",
         f"| Domain detection | {s['front_door']['domain']} "
         f"(expected {s['front_door']['domain_expected']}) → {s['front_door']['domain_correct']} |",
         f"| Tool health | {s['tool_health']['ok']}/{s['tool_health']['ran']} ok, "
         f"{s['tool_health']['skipped']} skipped |",
         f"| Truthfulness (§4) | **{s['truthfulness']['false_positives']}** false positives "
         f"(naive {s['truthfulness']['naive_false_positives']} → policy prevented "
         f"{s['truthfulness']['policy_prevented']}), {s['truthfulness']['missed_true_positives']} missed |",
         f"| Cleanliness (§8.6) | **{'PASS' if s['cleanliness']['pass'] else 'FAIL'}** — "
         f"{s['cleanliness']['hits']} lineage hits |"]

    e = s.get("enforcement")
    if e:
        L.append(f"| Enforcement (§8.1) | **{'PASS' if e['pass'] else 'FAIL'}** — seam "
                 f"{'rejected' if e['rejected'] else 'DID NOT reject'} an Observe tool that wrote "
                 f"to the target |")

    c = s.get("composition")
    if c:
        L.append(f"| Composition | composite **{c['composite']}** (expected "
                 f"{c['composite_expected']}) · subsystems "
                 f"{c['subsystems_correct']}/{c['subsystems_expected']} correctly placed |")
    L.append("")
    if c and c["mismatches"]:
        L += ["### Subsystem misplacements", ""]
        for name, m in c["mismatches"].items():
            L.append(f"- `{name}` — expected **{m['expected']}**, got **{m['got']}**")
        L.append("")

    for phase in ("install", "runtime"):
        d = run["precept"][phase]
        if d["total"]:
            L += [f"### Precept violations — {phase}", ""]
            for k in ("added", "modified", "removed"):
                for f in d[k]:
                    L.append(f"- `{f}` **{k}**")
            L.append("")

    if run.get("bait", {}).get("findings"):
        L += ["## Planted ground truth", "",
              "`naive` = dead_code with default args · `policy` = with the cartridge's pre-bound "
              "roots. The delta is the policy layer's measured contribution.", "",
              "| Symbol | Tool | Naive | Policy | Why |", "|---|---|---|---|---|"]
        for f in run["bait"]["findings"]:
            naive = f.get("naive_verdict", f.get("verdict", "—"))
            pol = f.get("policy_verdict", f.get("verdict", "—"))
            L.append(f"| `{f['symbol']}` | {f['tool']} | {naive} | **{pol}** | {f['why']} |")
        L.append("")

    fails = s["tool_health"]["failures"]
    if fails:
        L += ["## Tool failures", ""]
        for f in fails:
            L.append(f"- **{f['tool']}** — `{f['error']}`")
        L.append("")

    skipped = [r for r in run["tool_runs"] if r.get("skipped")]
    if skipped:
        L += ["## Skipped", ""]
        for r in skipped:
            L.append(f"- **{r['tool']}** — {r['reason']}")
        L.append("")
    return "\n".join(L) + "\n"


def cmd_report(a):
    p = RUNS / a.run_id / "report.md"
    if not p.exists():
        sys.exit(f"no such run: {a.run_id}")
    print(p.read_text(encoding="utf-8"))


def main():
    # Keep sweeps fast and Ollama-independent: attach's Gf synopsis is a real LLM call, but the
    # harness's scored dimensions don't need it. Disable by default (a caller can force it on with
    # SUITE_SUMMARY_DISABLE=0). Same posture as forcing the lexical embed backend for determinism.
    os.environ.setdefault("SUITE_SUMMARY_DISABLE", "1")
    ap = argparse.ArgumentParser(description="Sidecar proving ground.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("scaffold", help="build a dummy target with planted ground truth")
    p.add_argument("name")
    p.add_argument("--kind", choices=sorted(SCAFFOLDS), default="python-app")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_scaffold)

    p = sub.add_parser("adopt", help="copy a real project in as a target")
    p.add_argument("path")
    p.add_argument("--name")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_adopt)

    p = sub.add_parser("run", help="install the sidecar into a target and score it")
    p.add_argument("name")
    p.add_argument("--install", choices=["copy", "tool"], default="copy")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("seam", help="measure seam-completeness (capability coverage + self-hosting)")
    p.set_defaults(fn=cmd_seam)

    p = sub.add_parser("mount", help="M1: prove the precept by PREVENTION (Linux read-only mount)")
    p.add_argument("name")
    p.set_defaults(fn=cmd_mount)

    p = sub.add_parser("list", help="targets and runs")
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser("report", help="print a recorded run's report")
    p.add_argument("run_id")
    p.set_defaults(fn=cmd_report)

    a = ap.parse_args()
    TARGETS.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)
    a.fn(a)


if __name__ == "__main__":
    main()
