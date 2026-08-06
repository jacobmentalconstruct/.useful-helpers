"""
FILE:       tools/smoke_runner/cli.py
ROLE:       Structured smoke-test runner.
DOMAIN:     tool
DOES:       Discover or run selected smoke_test.py files in subprocesses and aggregate
            pass/fail, timing, stdout/stderr tails, and failure details.
DEPENDS ON: tools._toolkit, (stdlib) pathlib, subprocess, sys, time
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Sandbox authority because it executes test code.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from tools._toolkit import tool_main


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _discover(root: Path, limit: int) -> list[dict]:
    tests = []
    for path in sorted(root.rglob("smoke_test.py")):
        rel_parts = path.relative_to(root).parts
        if ".git" in rel_parts:
            continue
        tests.append({"path": str(path), "cwd": str(path.parent), "label": path.relative_to(root).as_posix()})
        if len(tests) >= limit:
            break
    return tests


def _run_one(test: dict, timeout: int) -> dict:
    started = time.perf_counter()
    try:
        completed = subprocess.run([sys.executable, test["path"]], cwd=test["cwd"],
                                   capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=timeout, check=False)
        duration = round(time.perf_counter() - started, 3)
        result = {"label": test["label"], "path": test["path"], "passed": completed.returncode == 0,
                  "returncode": completed.returncode, "duration_seconds": duration}
        if completed.stdout.strip():
            result["stdout_tail"] = completed.stdout.strip()[-1200:]
        if completed.stderr.strip():
            result["stderr_tail"] = completed.stderr.strip()[-1200:]
        return result
    except subprocess.TimeoutExpired:
        return {"label": test["label"], "path": test["path"], "passed": False, "returncode": -1,
                "duration_seconds": round(time.perf_counter() - started, 3),
                "error": f"timed out after {timeout}s"}


@tool_main
def run(args: dict) -> dict:
    root = Path(args.get("root") or ".").resolve()
    project = Path.cwd().resolve()
    if not root.is_dir():
        return {"ok": False, "error": f"root is not a directory: {root}"}
    if not _inside(project, root):
        return {"ok": False, "error": "root must stay inside the project workspace"}

    timeout = max(1, min(int(args.get("timeout_seconds", 30)), 600))
    stop_on_failure = bool(args.get("stop_on_failure", False))
    discovery_limit = max(1, min(int(args.get("discovery_limit", 25)), 200))
    targets = args.get("targets") or []

    tests = []
    if targets:
        for target in targets:
            p = (root / str(target)).resolve()
            if not p.exists() or not p.is_file():
                return {"ok": False, "error": f"target not found: {target}"}
            if not _inside(project, p):
                return {"ok": False, "error": "targets must stay inside the project workspace"}
            tests.append({"path": str(p), "cwd": str(p.parent), "label": p.relative_to(root).as_posix()})
    else:
        tests = _discover(root, discovery_limit)

    results = []
    for test in tests:
        result = _run_one(test, timeout)
        results.append(result)
        if stop_on_failure and not result["passed"]:
            break

    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    summary = {
        "tests_found": len(tests),
        "tests_run": len(results),
        "passed": passed,
        "failed": failed,
        "all_passed": failed == 0,
    }
    return {
        "ok": failed == 0,
        "tool": "smoke_runner",
        "root": root.as_posix(),
        "tests_found": len(tests),
        "tests_run": len(results),
        "passed": passed,
        "failed": failed,
        "all_passed": failed == 0,
        "total_duration_seconds": round(sum(r.get("duration_seconds", 0) for r in results), 3),
        "summary": summary,
        "results": results,
        "failures": [r for r in results if not r["passed"]],
    }
