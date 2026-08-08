"""
FILE:       gates/t04_cancellation.py
ROLE:       Gate for T4 - Cancellation and Progress.
DOMAIN:     factory
DOES:       Asserts long work is observable while it runs and can be stopped, that
            stopping it leaves nothing behind, and that diagnostics reaching a client
            carry no host paths.
NOTES:      Written during tranche declaration, BEFORE implementation, per
            .bcc/TRANCHE_PROTOCOL.md sec 3.2 rule 1.

            Rule 8: cancellation is asserted through a real dispatch, not by calling
            a helper. The defect this guards against - an orphaned grandchild - is
            invisible to anything that only checks the call returned.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

OUTCOME = "long work is observable while it runs, and can be stopped cleanly"


def _load(root: Path, dotted: str):
    sys.path.insert(0, str(root))
    try:
        return __import__(dotted, fromlist=["_"])
    except Exception:
        return None
    finally:
        if str(root) in sys.path:
            sys.path.remove(str(root))


def _paths(root: Path):
    sys.path.insert(0, str(root))
    try:
        from src.core.config import resolve_paths
        return resolve_paths(root)
    except Exception:
        return None
    finally:
        if str(root) in sys.path:
            sys.path.remove(str(root))


def check(r, root: Path) -> None:
    invoke = _load(root, "src.core.invoke")
    r.check("the seam exposes cancellation", invoke is not None
            and hasattr(invoke, "cancel"),
            "expected src/core/invoke.py::cancel - today dispatch blocks on "
            "subprocess.run with no handle and no way to stop it")

    src = (root / "src" / "core" / "invoke.py").read_text(encoding="utf-8", errors="replace")

    # --- per-call timeout ---------------------------------------------------
    # DEFAULT_TIMEOUT_S is module-level and unreachable per call. A snapshot compile
    # over a large tree needs longer; a health probe should not wait two minutes.
    r.check("a timeout can be supplied per call",
            "timeout" in src and "def invoke(" in src
            and "timeout" in src.split("def invoke(")[1][:400],
            "invoke() must accept a timeout, not only honour a module constant")

    # --- diagnostics are scrubbed on the RETURN path ------------------------
    # event_log scrubs before STORING, so the audit trail is clean while the value
    # handed to a GUI or an agent still carries absolute build-machine paths. The
    # machinery exists; it was simply not on this path.
    r.check("errors returned to a client are scrubbed",
            "relativize_paths" in src,
            "InvokeResult.error is handed straight to callers; the scrubber is "
            "applied when writing the ledger but not when returning")

    if not r.filesystem_permits_unlink(root):
        r.skip("a long operation can be cancelled",
               "this filesystem denies unlink, so the fixture tool cannot be "
               "created or cleaned up here")
        return
    if invoke is None or not hasattr(invoke, "cancel"):
        return

    paths = _paths(root)
    if paths is None:
        r.check("cancellation is exercisable", False, "could not resolve paths")
        return

    # --- a REAL long operation, cancelled -----------------------------------
    tools = root / "tools" / "_t04_slow_probe"
    tools.mkdir(parents=True, exist_ok=True)
    (tools / "tool.json").write_text(
        '{"id":"_t04_slow_probe","summary":"T4 fixture: sleeps.","category":"introspection",'
        '"authority":"Observe","operates_on":"project","writes":"none",'
        '"invocation":{"interpreter":"","entry":"tools/_t04_slow_probe/cli.py"},'
        '"input_schema":{"type":"object","properties":{}}}', encoding="utf-8")
    (tools / "cli.py").write_text(
        "import json, time\n"
        "time.sleep(120)\n"
        "print(json.dumps({'ok': True}))\n", encoding="utf-8")
    try:
        subprocess.run([sys.executable, "-m", "src.app", "cli", "registry-refresh"],
                       cwd=root, capture_output=True, timeout=180)

        state = Path(tempfile.mkdtemp(prefix="t04-"))
        env = {**os.environ, "SUITE_STATE_ROOT": str(state),
               "SUITE_PROJECT_ROOT": str(state)}

        started = time.perf_counter()
        proc = subprocess.Popen(
            [sys.executable, "-m", "src.app", "cli", "tool-call",
             "--tool", "_t04_slow_probe", "--args-json", "{}"],
            cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        time.sleep(3)

        # observable WHILE running - the whole point of "observable", not "reported"
        alive = proc.poll() is None
        r.check("a long operation is observable while it is still running", alive,
                "the operation must be visible before it completes, not only after")

        proc.terminate()
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
        elapsed = time.perf_counter() - started
        r.check("cancellation returns promptly", elapsed < 60,
                f"took {elapsed:.1f}s - a cancel that waits for the timeout is not a cancel")

        # --- nothing survives ------------------------------------------------
        # Killing the parent can leave a grandchild running. This is the failure that
        # anything checking only "the call returned" cannot see.
        leftover = subprocess.run(
            ["pgrep", "-f", "_t04_slow_probe/cli.py"],
            capture_output=True, text=True).stdout.strip()
        r.check("cancelling reaps the child, leaving no orphan",
                not leftover, f"surviving pids: {leftover.splitlines()[:3]}")
    finally:
        for f in ("tool.json", "cli.py"):
            try:
                (tools / f).unlink()
            except OSError:
                pass
        try:
            tools.rmdir()
        except OSError:
            pass
        subprocess.run([sys.executable, "-m", "src.app", "cli", "registry-refresh"],
                       cwd=root, capture_output=True, timeout=180)
