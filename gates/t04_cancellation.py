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

# Machine-visible, printed by gates/run.py beneath the verdict. Declared because one
# assertion name covers two different mechanisms, so a green on one platform is not
# evidence about the other. Kept CURRENT: an over-cautious stale limitation is still
# a false statement - and so is a limitation that claims MORE verification than was
# achieved. This block has now been corrected in both directions.
KNOWN_LIMITATIONS = (
    {
        "assertion": "explicit cancel reaps the GRANDCHILD too",
        "coverage": "platform-partial",
        "limitation": "cannot discriminate on POSIX. terminate() signals the whole "
                      "process group first, so the grandchild dies from that signal "
                      "regardless of whether the tree escalation runs. Mutation-tested: "
                      "restoring the old skipped-escalation defect leaves this PASSING "
                      "on Linux. The defect it guards is Windows-only, because "
                      "CTRL_BREAK_EVENT reaches only console-attached processes",
        "contributes_to_E11_completion": False,
        "disposition": "only a Windows run can prove this assertion; treat a Linux "
                       "green as silence, not evidence",
    },
    {
        "assertion": "seam shutdown reaps the GRANDCHILD too",
        "coverage": "platform-partial",
        "limitation": "two DIFFERENT mechanisms wear one assertion name. POSIX proves "
                      "process groups; Windows proves contain_self()'s kill-on-close "
                      "job. A green on either platform says nothing about the other, "
                      "so this needs BOTH to mean what it says. POSIX is verified. "
                      "WINDOWS IS NOT: two runs reported this PASS while contain_self() "
                      "was returning False - untyped ctypes truncated the 64-bit HANDLE, "
                      "every job call failed, and honest degradation made it silent. "
                      "Whatever reaped the grandchild on Windows, it was not this",
        "contributes_to_E11_completion": False,
        "disposition": "signatures now declared and containment ASSERTED rather than "
                       "inferred, so a silent failure becomes a red. Windows result "
                       "pending; until then the cause of the passing kill is unknown",
    },
)


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

    # --- containment is IN FORCE, not merely attempted -----------------------
    # Asserted rather than inferred. Two Windows runs reported the grandchild reaped
    # while `contain_self()` was silently returning False - the mechanism was
    # credited with a result it had no part in, because a passing kill was read as
    # evidence that the thing meant to cause it had worked.
    #
    # ctypes defaults restype to c_int; a 64-bit HANDLE was being truncated, so every
    # job call failed and the module's honest degradation turned that into silence.
    if os.name == "nt":
        pt = _load(root, "src.core.proctree")
        r.check("process containment is in force on Windows",
                pt is not None and pt.contain_self(),
                f"contain_self() says: {pt.containment_error() if pt else 'module missing'}"
                " - without it nothing guarantees a tool dies with the seam, and the "
                "orphan assertions below would be passing for some other reason")

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
    # The fixture SPAWNS A GRANDCHILD and records both pids.
    #
    # An earlier revision slept in one process, so "leaving no orphan" asserted only
    # that the direct child died - one level, not a tree. The defect it is named for
    # is a DESCENDANT surviving, and that was untestable by construction: on POSIX a
    # single killpg covers depth one trivially, so a mutation restoring the old
    # skipped-escalation bug could not make it fail.
    #
    # The grandchild is what a real tool leaves behind - a dev server, a watcher, a
    # worker holding a lock.
    (tools / "cli.py").write_text(
        "import json, os, subprocess, sys, time\n"
        "here = os.path.dirname(os.path.abspath(__file__))\n"
        "kid = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(300)'])\n"
        "open(os.path.join(here, 'pid'), 'w').write(str(os.getpid()))\n"
        "open(os.path.join(here, 'gpid'), 'w').write(str(kid.pid))\n"
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
            r.check("seam shutdown reaps the child, leaving no orphan",
                    not _pid_alive(child_pid),
                    f"pid {child_pid} survived the parent - a detached child "
                    "holding a lock or a port after the seam is gone")
        gpidfile = tools / "gpid"
        if gpidfile.is_file():
            gp = int(gpidfile.read_text(encoding="utf-8").strip())
            r.check("seam shutdown reaps the GRANDCHILD too", not _pid_alive(gp),
                    f"pid {gp} survived - killing the direct child is not tearing "
                    "down the tree; this is the failure the whole tranche is about")

        # --- PATH 2: EXPLICIT CANCEL -----------------------------------------
        # A DIFFERENT path from the one above, and it has to be asserted separately.
        #
        # Above, the seam process is killed from outside: on Windows that is
        # TerminateProcess, which runs no handler and no atexit, so nothing in
        # invoke.py executes. Here the seam stays alive and cancel() runs its own
        # termination logic.
        #
        # Only this path reaches the escalation that used to be skipped: _terminate()
        # returned as soon as the direct child exited, so `taskkill /T` never ran when
        # the child behaved well. A gate asserting only the shutdown path would have
        # reported PASS over that defect indefinitely - which is what happened.
        pidfile.unlink(missing_ok=True)
        (tools / "gpid").unlink(missing_ok=True)
        driver = tools / "driver.py"
        driver.write_text(
            "import json, sys, threading, time\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "from src.core.config import resolve_paths\n"
            "from src.core import invoke as inv\n"
            "from pathlib import Path\n"
            "paths = resolve_paths(Path(sys.argv[1]))\n"
            "def go():\n"
            "    inv.invoke(paths, 't04slowprobe', {}, client='test')\n"
            "t = threading.Thread(target=go, daemon=True); t.start()\n"
            "time.sleep(4)\n"
            "ops = inv.running()\n"
            "ok = bool(ops) and inv.cancel(ops[0]['op_id'])\n"
            "t.join(timeout=20)\n"
            "print(json.dumps({'cancelled': ok}))\n", encoding="utf-8")
        drv = subprocess.run(
            [sys.executable, str(driver), str(root)],
            cwd=root, capture_output=True, text=True, timeout=180,
            env={**os.environ, "SUITE_STATE_ROOT": str(state),
                 "SUITE_PROJECT_ROOT": str(state)})
        r.check("an in-flight operation is cancellable through the seam",
                '"cancelled": true' in (drv.stdout or "").lower(),
                f"driver said {(drv.stdout or drv.stderr or '')[-200:]!r}")

        if pidfile.is_file():
            cancelled_pid = int(pidfile.read_text(encoding="utf-8").strip())
            r.check("explicit cancel reaps the child, leaving no orphan",
                    not _pid_alive(cancelled_pid),
                    f"pid {cancelled_pid} survived cancel() - the tree escalation "
                    "was skipped, or the tree was never owned")
            g2 = tools / "gpid"
            if g2.is_file():
                gp2 = int(g2.read_text(encoding="utf-8").strip())
                r.check("explicit cancel reaps the GRANDCHILD too", not _pid_alive(gp2),
                        f"pid {gp2} survived cancel() - _terminate() used to return "
                        "as soon as the direct child exited, skipping tree teardown "
                        "exactly when the child behaved well")
        else:
            r.check("explicit cancel reaps the child, leaving no orphan", False,
                    "the cancelled run never recorded a pid")
    finally:
        for f in ("tool.json", "cli.py", "pid", "gpid", "driver.py"):
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
