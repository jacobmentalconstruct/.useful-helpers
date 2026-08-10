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


def _pid_alive(pid: int) -> bool:
    """Is this specific process still running? Cross-platform, no dependencies.

    `os.kill(pid, 0)` is the POSIX idiom for "does this exist" and is DELIBERATELY
    not used on Windows: CPython's os.kill there calls TerminateProcess for any
    signal other than CTRL_C_EVENT/CTRL_BREAK_EVENT - including 0. Asking "is it
    alive" would kill it, and the check would then pass by having caused the
    condition it tests for.

    Windows uses `tasklist /FI "PID eq N"`, the idiom already in
    tools/dev_server_manager/cli.py - reused rather than reinvented.
    """
    if os.name == "nt":
        try:
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=30).stdout
        except (OSError, subprocess.SubprocessError):
            return False
        return f'"{pid}"' in out or f",{pid}," in out
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True          # exists, owned by someone else
    return True


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
    # NOT underscore-prefixed: registry.discover() skips `_`-named directories
    # (that is how tools/_template stays unregistered). A fixture named with a
    # leading underscore is never registered, and the dispatch returns "unknown
    # tool" instantly - which looks exactly like "the operation already finished".
    tools = root / "tools" / "t04slowprobe"
    tools.mkdir(parents=True, exist_ok=True)
    (tools / "tool.json").write_text(
        '{"id":"t04slowprobe","summary":"T4 fixture: sleeps.","category":"introspection",'
        '"authority":"Observe","operates_on":"project","writes":"none",'
        '"invocation":{"interpreter":"","entry":"tools/t04slowprobe/cli.py"},'
        '"input_schema":{"type":"object","properties":{}}}', encoding="utf-8")
    # The fixture records its own PID BESIDE ITSELF, resolved from __file__.
    # Not into the state root: the gate points SUITE_PROJECT_ROOT and
    # SUITE_STATE_ROOT at the same temp dir, so a fixture writing to the state
    # root would be writing to the BOUND TARGET - and the precept guard would
    # correctly flag an Observe tool mutating it. tools/ is the sidecar's own home.
    (tools / "cli.py").write_text(
        "import json, os, time\n"
        "here = os.path.dirname(os.path.abspath(__file__))\n"
        "open(os.path.join(here, 'pid'), 'w').write(str(os.getpid()))\n"
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
             "--tool", "t04slowprobe", "--args-json", "{}"],
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
        #
        # Asked as "is THIS process alive", not "does any command line mention the
        # fixture". `pgrep -f` was POSIX-only and matched on command-line text, which
        # has no stable Windows equivalent - tasklist filters image names, wmic is
        # removed from current images, CIM is a third syntax. Porting the matching
        # strategy would mean three implementations of one question. Recording the
        # PID makes it one question with a two-line platform branch, and removes
        # substring collisions on both platforms.
        pidfile = tools / "pid"
        r.check("the fixture recorded its pid", pidfile.is_file(),
                "without it the orphan check cannot run, and a check that cannot "
                "run is absent rather than passing")
        if pidfile.is_file():
            child_pid = int(pidfile.read_text(encoding="utf-8").strip())
            r.check("cancelling reaps the child, leaving no orphan",
                    not _pid_alive(child_pid),
                    f"pid {child_pid} survived the parent - a detached grandchild "
                    "holding a lock or a port after the seam is gone")
    finally:
        for f in ("tool.json", "cli.py", "pid"):
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
