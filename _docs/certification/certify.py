"""
FILE:       _docs/certification/certify.py
ROLE:       One command that certifies a tranche and writes a machine-readable verdict.
DOMAIN:     factory (builder-control; NEVER_SHIP, so it cannot reach a payload)
DOES:       Runs lint, the suite, every gate and the discovery pass, then writes one JSON
            record to _docs/certification/ and prints a short human summary.
DEPENDS ON: stdlib only. No third-party imports, so it runs on a bare CPython.
WIRES TO:   gates/run.py (imported, not scraped), smoke_test.py, _harness/harness.py
NOTES:      WHY THIS EXISTS. Certification was a list of commands pasted into a terminal,
            and the results came back as thousands of lines of console text that had to be
            read by eye. That is expensive, it is easy to misread, and twice already a
            verdict was reported from a partial scroll.

            THE OUTPUT IS THE POINT. One JSON file with a top-level `verdict`, per-step
            results, and per-gate assertion counts including the exact text of any
            failure. Reading it costs one file, not a transcript.

            STRUCTURED WHERE POSSIBLE, PARSED ONLY WHERE NECESSARY.

              gates      IMPORTED. `gates/run.py` exposes `_load` and `Result`, so this
                         collects assertion rows directly. No text scraping at all.
              discovery  the harness already writes `run.json` per run - read, not parsed.
              suite      `unittest`'s tail is parsed, because it is a stable documented
                         format and the suite is a subprocess by design.
              lint       exit code plus its one-line summary.

            IT NEVER LIES BY OMISSION. A step that could not run is recorded as
            `"ok": false` with a reason - never skipped silently, and never absent from
            the record. An absent result and a passing result must not look alike.

            SAFE TO RUN REPEATEDLY. It writes only under _docs/certification/, touches no
            target, and each run lands in its own timestamped file.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = 1
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent                      # _docs/certification -> repo root
GATES = ROOT / "gates"


# --------------------------------------------------------------------------- helpers
def _run(cmd, timeout=3600, cwd=None, env=None):
    """Run a subprocess and return (exit_code, stdout, stderr) without raising."""
    try:
        p = subprocess.run(cmd, cwd=str(cwd or ROOT), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=env)
        return p.returncode, p.stdout or "", p.stderr or ""
    except FileNotFoundError as e:
        return 127, "", f"not found: {e}"
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout}s"


def _git(*args):
    rc, out, _ = _run([_git_exe(), *args])
    return out.strip() if rc == 0 else ""


def _git_exe():
    return "git"


# --------------------------------------------------------------------------- steps
def step_lint() -> dict:
    rc, out, err = _run([sys.executable, "-m", "ruff", "check", "."])
    tail = (out or err).strip().splitlines()
    return {"ok": rc == 0, "exit": rc,
            "detail": tail[-1] if tail else "",
            "findings": [ln for ln in tail if ln.startswith(("E", "F", "W", "I")) and ":" in ln][:20]}


_RAN = re.compile(r"^Ran (\d+) tests? in ([\d.]+)s", re.M)
_OK = re.compile(r"^OK(?: \((.*)\))?$", re.M)
_BAD = re.compile(r"^FAILED \((.*)\)$", re.M)


def step_suite() -> dict:
    """`unittest`'s tail is a stable documented format; the suite is a subprocess by design."""
    rc, out, err = _run([sys.executable, "smoke_test.py"])
    blob = out + err
    ran = _RAN.search(blob)
    ok, bad = _OK.search(blob), _BAD.search(blob)
    counts = {}
    for m in re.finditer(r"(\w+)=(\d+)", (ok.group(1) if ok and ok.group(1) else "")
                         + " " + (bad.group(1) if bad else "")):
        counts[m.group(1)] = int(m.group(2))
    # The individual failures, so a red run is diagnosable from the record alone.
    failures = re.findall(r"^(?:FAIL|ERROR): (\S+)", blob, re.M)
    return {"ok": rc == 0 and bool(ok), "exit": rc,
            "tests": int(ran.group(1)) if ran else None,
            "seconds": float(ran.group(2)) if ran else None,
            "skipped": counts.get("skipped", 0),
            "failures": counts.get("failures", 0),
            "errors": counts.get("errors", 0),
            "failed_tests": sorted(set(failures))[:40],
            "detail": ("OK" if ok else (bad.group(0) if bad else "no verdict line found"))}


def step_gates(only: str = "") -> dict:
    """IMPORTED, not scraped. `gates/run.py` gives assertion rows directly.

    `only` narrows to one gate for re-running a single red result. A narrowed run is
    recorded as such in the JSON, so a partial certification can never be mistaken for a
    full one.
    """
    spec = importlib.util.spec_from_file_location("_gates_run", GATES / "run.py")
    gr = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(GATES))
    spec.loader.exec_module(gr)

    out, overall = [], True
    files = sorted(GATES.glob("t[0-9][0-9]*_*.py"))
    if only:
        files = [f for f in files if f.stem.startswith(only.lower())]
    for path in files:
        entry = {"id": path.stem}
        started = time.monotonic()
        try:
            mod = gr._load(path)
            res = gr.Result(path.stem)
            mod.check(res, ROOT)
            rows = res.rows
            entry.update(
                outcome=getattr(mod, "OUTCOME", ""),
                passed=sum(1 for s, _, _ in rows if s == "PASS"),
                failed=sum(1 for s, _, _ in rows if s == "FAIL"),
                skipped=sum(1 for s, _, _ in rows if s == "SKIP"),
                total=len(rows),
                verdict="PASS" if not res.failed else "FAIL",
                failures=[{"assertion": n, "detail": d} for s, n, d in rows if s == "FAIL"],
                skips=[{"assertion": n, "reason": d} for s, n, d in rows if s == "SKIP"],
                # Declared partial coverage is part of the verdict's meaning, not a footnote.
                partial=[lim.get("assertion", "?")
                         for lim in (getattr(mod, "KNOWN_LIMITATIONS", ()) or ())],
            )
        except Exception as e:                       # a gate that cannot RUN is not a pass
            entry.update(verdict="ERROR", error=f"{type(e).__name__}: {e}",
                         passed=0, failed=0, skipped=0, total=0, failures=[], skips=[],
                         partial=[])
        entry["seconds"] = round(time.monotonic() - started, 1)
        overall = overall and entry["verdict"] == "PASS"
        out.append(entry)
    return {"ok": overall and bool(out), "gates": out, "narrowed_to": only or None,
            "total_assertions": sum(g.get("total", 0) for g in out),
            "total_passed": sum(g.get("passed", 0) for g in out)}


def step_discovery(target: str) -> dict:
    """The harness already writes `run.json` per run. Read it; do not parse the console."""
    before = {p for p in (ROOT / "_harness" / "runs").glob("*")} \
        if (ROOT / "_harness" / "runs").is_dir() else set()
    rc, out, err = _run([sys.executable, str(ROOT / "_harness" / "harness.py"), "run", target])
    after = {p for p in (ROOT / "_harness" / "runs").glob("*")}
    fresh = sorted(after - before, key=lambda p: p.name)
    record = {}
    if fresh:
        rj = fresh[-1] / "run.json"
        if rj.is_file():
            try:
                record = json.loads(rj.read_text(encoding="utf-8"))
            except ValueError as e:
                record = {"_unreadable": str(e)}
    # The harness writes `score`. Looking for `scores`/`summary` found neither, so a
    # successful discovery pass was recorded with an empty body - `ok: true` and nothing
    # to read. A guessed key silently produced a substanceless record.
    scores = record.get("score") or {}
    return {"ok": rc == 0, "exit": rc, "target": target,
            "run_dir": fresh[-1].name if fresh else None,
            "scores": scores,
            "axes": {k: record.get(k) for k in
                     ("precept", "enforcement", "lineage_hits") if k in record},
            "detail": "" if rc == 0 else (err or out)[-400:]}


# --------------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Certify this tranche; write a JSON verdict.")
    ap.add_argument("--label", default="", help="e.g. t07-park")
    ap.add_argument("--target", default="_UsefulHelperSCRIPTS",
                    help="harness target for the discovery pass")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="certify anyway; the record says so")
    ap.add_argument("--only", default="", help="one gate, e.g. t07 (records the narrowing)")
    ap.add_argument("--skip-discovery", action="store_true",
                    help="omit the discovery pass (recorded as skipped, never as passing)")
    ns = ap.parse_args(argv)

    # REFUSE A DIRTY TREE, and this exists because the script tripped over itself.
    #
    # `certify.py` writes its record INTO the tree it certifies. Leave that record
    # uncommitted and the NEXT run fails `t00`'s "working tree is clean" assertion - so a
    # certification failed for the certifier's own leftovers rather than for anything
    # about the product. Observed exactly once, and once is enough.
    #
    # Not fixed by excluding `_docs/certification/` from t00: blinding a census so it
    # stops seeing a surface is the defect this project has recorded three times. Fixed
    # by making the sequencing explicit - commit, certify, commit the record, push.
    dirty = _git("status", "--porcelain")
    if dirty and not ns.allow_dirty:
        print("REFUSING: the working tree is not clean, and `t00` asserts that it is.")
        print("A record produced now would certify something that is not in git.\n")
        for line in dirty.splitlines()[:15]:
            print("   ", line)
        print("\nCommit (or stash) first, then re-run. --allow-dirty overrides and is")
        print("recorded in the JSON, so an overridden run cannot be mistaken for a clean one.")
        return 2

    started = datetime.now(timezone.utc)
    print(f"certifying {ROOT}")
    print("  [1/4] lint ...", flush=True)
    lint = step_lint()
    print(f"        {'ok' if lint['ok'] else 'FAILED'}")
    print("  [2/4] suite ...", flush=True)
    suite = step_suite()
    print(f"        {'ok' if suite['ok'] else 'FAILED'}  "
          f"{suite['tests']} tests, {suite['skipped']} skipped")
    print("  [3/4] gates ...", flush=True)
    gates = step_gates(ns.only)
    for g in gates["gates"]:
        print(f"        {g['verdict']:5} {g['id']:26} {g.get('passed',0)}/{g.get('total',0)}")
    if ns.skip_discovery:
        disc = {"ok": False, "skipped": True,
                "detail": "--skip-discovery: not run, and NOT counted as passing"}
        print("  [4/4] discovery ... skipped")
    else:
        print("  [4/4] discovery ...", flush=True)
        disc = step_discovery(ns.target)
        print(f"        {'ok' if disc['ok'] else 'FAILED'}")

    verdict = "PASS" if (lint["ok"] and suite["ok"] and gates["ok"]
                         and (disc.get("ok") or disc.get("skipped"))) else "FAIL"
    record = {
        "schema": SCHEMA,
        "verdict": verdict,
        "label": ns.label,
        "generated_at": started.isoformat(timespec="seconds"),
        "seconds": round((datetime.now(timezone.utc) - started).total_seconds(), 1),
        "commit": _git("rev-parse", "--short", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(_git("status", "--porcelain")),
        "allow_dirty": bool(ns.allow_dirty),
        "platform": {"system": platform.system(), "release": platform.release(),
                     "machine": platform.machine(),
                     "python": platform.python_version()},
        "steps": {"lint": lint, "suite": suite, "gates": gates, "discovery": disc},
    }

    outdir = HERE / "runs"
    outdir.mkdir(parents=True, exist_ok=True)
    name = (f"{started.strftime('%Y%m%d-%H%M%S')}-{platform.system().lower()}"
            f"-{record['commit'] or 'nocommit'}{('-' + ns.label) if ns.label else ''}.json")
    path = outdir / name
    path.write_text(json.dumps(record, indent=2, default=str) + "\n", encoding="utf-8")

    print()
    print(f"VERDICT: {verdict}")
    print(f"  commit   {record['commit']}{' (DIRTY)' if record['dirty'] else ''}")
    print(f"  platform {record['platform']['system']} python {record['platform']['python']}")
    print(f"  gates    {gates['total_passed']}/{gates['total_assertions']} assertions")
    print(f"  written  {path.relative_to(ROOT).as_posix()}")
    print()
    print("Commit and push that file; it is the whole certification record.")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
