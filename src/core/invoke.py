"""
FILE:       src/core/invoke.py
ROLE:       The invoke() seam  -  the ONE chokepoint every tool call passes through.
DOMAIN:     core
DOES:       Given (tool_id, args), resolve the tool from the registry, run its headless CLI as
            a subprocess (`<interpreter> <entry> --args-json <json>`), capture a structured
            JSON result, log it, and RECORD a governance event (T-gov slice 1).
DEPENDS ON: src.core.{registry,event_log,config}, src.lib.{logging_setup,common}, (stdlib) subprocess, os, json, sys, time
WIRES TO:   called by interfaces.mcp_server (tools/call), interfaces.cli, ui.registry_view
NOTES:      THE GOVERNANCE SEAM. Every call is gated by authority policy (slice 2) and appended
            to the append-only event log (slice 1), uniformly, HERE. Dispatch logic lives in
            _dispatch (all return paths); invoke() wraps it with timing + one event record, so
            the audit trail is complete regardless of which path a call takes. Subprocess-only  -
            never import tool code (adapters are subprocesses, not imports). A missing or
            failing tool returns InvokeResult(ok=False),
            never crashes (sec 9).
"""
from __future__ import annotations

import atexit
import json
import os
import signal
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field

from src.core import event_log, policy, presence, proctree, registry
from src.core.config import Paths
from src.lib.common import relativize_paths, safe_json_dumps
from src.lib.logging_setup import get_logger

log = get_logger("core.invoke")

DEFAULT_TIMEOUT_S = 120

# Cancellation is not failure. A distinct code so a deliberate stop is never confused
# with a crash - in the ledger, in the UI, or by an agent reading either.
CANCELLED_EXIT = -2

# Operations currently in flight, so something outside the calling thread can stop
# them. Process-lifetime by design: a cancel can only reach a child of THIS process.
_RUNNING: dict[str, "_Running"] = {}
_RUNNING_LOCK = threading.Lock()


@dataclass
class _Running:
    """A dispatch in flight, and the process TREE it owns.

    `tree` is the durable ownership handle (src/core/proctree.py). Holding it is what
    lets the descendants be stopped as a unit, and - on Windows - what makes them die
    with this process even when it is terminated abruptly.
    """
    proc: "subprocess.Popen"
    tool_id: str
    started: float
    tree: "proctree.ProcessTree | None" = None
    cancelled: bool = False
    op_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])


def _clean(paths: Paths, text: str) -> str:
    """Strip host paths from anything handed back to a caller."""
    try:
        roots = [(str(paths.root), "<toolkit>")]
        if getattr(paths, "project_root", None) is not None:
            roots.insert(0, (str(paths.project_root), "<project>"))
        return relativize_paths(str(text), roots=tuple(roots))
    except Exception:
        return str(text)


def _terminate(proc: "subprocess.Popen",
               tree: "proctree.ProcessTree | None" = None) -> None:
    """Stop a child and everything it spawned, then confirm it is gone.

    Delegates to the process-tree handle when there is one. The escalation is
    UNCONDITIONAL there: this function used to return as soon as the direct child
    exited, which skipped tree teardown exactly when the child behaved well.
    """
    (tree or proctree.ProcessTree(proc)).terminate()


def running() -> list[dict]:
    """What is in flight right now, for a caller deciding what to cancel."""
    with _RUNNING_LOCK:
        return [{"op_id": h.op_id, "tool_id": h.tool_id,
                 "elapsed_s": round(time.time() - h.started, 2)}
                for h in _RUNNING.values()]


def cancel(op_id: str) -> bool:
    """Stop an operation in flight. True if one was found and signalled."""
    with _RUNNING_LOCK:
        handle = _RUNNING.get(op_id)
    if handle is None:
        return False
    handle.cancelled = True
    _terminate(handle.proc, handle.tree)
    log.info("invoke CANCELLED op=%s tool=%s", op_id, handle.tool_id)
    return True


def reap_all() -> int:
    """Stop everything this process started. Returns how many were reaped.

    Necessary because children run in their OWN process group - which is what lets
    cancel() kill a tool AND its grandchildren, but also means they no longer die
    with the parent. Detaching to gain reach costs the automatic cascade, so the
    cascade has to be put back deliberately.

    Without this, killing the seam leaves its tools running: a sleep(120) fixture
    survived its parent and was still there afterwards. In use that is a worker
    holding a file lock, or a server holding a port, long after the thing that
    started it is gone.
    """
    with _RUNNING_LOCK:
        handles = list(_RUNNING.values())
    for handle in handles:
        handle.cancelled = True
        try:
            _terminate(handle.proc, handle.tree)
        except Exception:
            pass
    if handles:
        log.info("invoke reaped %d in-flight operation(s) on shutdown", len(handles))
    return len(handles)


atexit.register(reap_all)


def install_shutdown_handlers() -> None:
    """Reap in-flight work on SIGTERM/SIGINT as well as on a normal exit.

    atexit alone is not enough: the default disposition for SIGTERM ends the process
    without running exit handlers, which is exactly the case that orphaned a tool.

    Called from the composition root rather than on import - installing signal
    handlers is a process-level decision, and a library that does it behind the
    caller's back will surprise anything embedding it.
    """
    # Windows first: containment must exist BEFORE any tool is launched, because job
    # membership is not retroactive. Signals are the POSIX half of the same job.
    #
    # Logged when it degrades. A silently weaker guarantee is how "we fixed that"
    # survives past the point where it is true - and this whole repair exists because
    # a lifecycle claim went four tranches without being exercised.
    if os.name == "nt" and not proctree.contain_self():
        log.warning("invoke: process containment unavailable (%s) - tools may outlive "
                    "this process if it is terminated abruptly",
                    proctree.containment_error())

    def _handler(signum, _frame):
        reap_all()
        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _handler)
        except (ValueError, OSError, AttributeError):
            pass    # not the main thread, or unsupported on this platform


def _announce(paths: Paths, tool_id: str, op_id: str, phase: str, client: str) -> None:
    """Publish a lifecycle phase so work is visible WHILE it runs.

    Coarse by design. Tools emit one JSON envelope at completion, so per-tool
    progress would need every tool changed and would break the stdout contract the
    envelope depends on. Started/finished answers the real question - "is it stuck,
    and can I stop it" - without touching 95 tools. A per-tool channel stays open as
    an option if a long-running tool ever earns it.
    """
    try:
        presence.update(paths, active_step=f"{tool_id}:{phase}",
                        active_chain=op_id if phase == "started" else None)
    except Exception:
        pass    # visibility is an enrichment; it must never break a dispatch

# Dirs never worth manifesting for the precept guard (regenerable / VCS / deps).
_GUARD_SKIP = {".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules", "__pycache__",
               ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build", "site-packages"}
_GUARD_MAX_FILES = 20000  # bound the stat cost; above this, skip the guard and say so
_GUARD_DISABLED_LOGGED = False  # so the kill-switch warning fires once, not per dispatch


def _target_manifest(paths: Paths) -> tuple[dict, bool]:
    """Cheap (mtime+size) manifest of the WORK TARGET, excluding a nested toolkit home.

    This is the precept made mechanical at the seam: after a call that is not allowed to write to
    the target, this manifest must be identical. Uses stat only (no reads), skips regenerable
    noise, and excludes SUITE_HOME when it sits inside the target (the sidecar legitimately writes
    its own state). Returns (manifest, complete); complete=False means the target was too large
    to guard cheaply  -  the caller degrades to a note rather than a false verdict.
    """
    target = paths.project_root
    home = paths.root.resolve()
    manifest: dict[str, tuple[float, int]] = {}
    count = 0
    for current, dir_names, file_names in os.walk(target):
        cur = os.path.realpath(current)
        # prune noise and the toolkit's own home (state/artifacts are not "the target")
        dir_names[:] = [d for d in dir_names
                        if d not in _GUARD_SKIP and os.path.realpath(os.path.join(cur, d)) != str(home)]
        for name in file_names:
            p = os.path.join(current, name)
            try:
                st = os.stat(p)
            except OSError:
                continue
            manifest[p] = (st.st_mtime, st.st_size)
            count += 1
            if count > _GUARD_MAX_FILES:
                return manifest, False
    return manifest, True


def _manifest_diff(before: dict, after: dict) -> list[str]:
    """Paths added, removed, or changed (mtime/size) between two target manifests."""
    changed = [p for p in after if p not in before or after[p] != before[p]]
    changed += [p for p in before if p not in after]
    return sorted(set(changed))


def _guard_applies(paths: Paths, tool) -> bool:
    """Enforce the target-write guard only when it is meaningful and wanted.

    Gated on **Observe** authority: an Observe tool presents as read-only, so it must leave the
    target byte-identical  -  a silent write from one is the precept-violation risk this guard
    exists to catch. Sandbox tools (e.g. smoke_runner) run the PROJECT's own code, which
    legitimately creates `__pycache__`/build output in the target; Apply tools write by
    definition and are invoked deliberately. Neither is a sidecar leaving traces, so neither is
    guarded. Further conditions:
    - a TRUE sidecar install (target distinct from toolkit home); standalone/dev coincide, so
      there is no separate target to protect.
    - `writes: target` is a sanctioned opt-out (no shipped Observe tool uses it; it exists so an
      unusual one can declare its intent rather than trip the guard).
    - not disabled via SUITE_STRICT_OBSERVE=0.
    """
    if os.environ.get("SUITE_STRICT_OBSERVE", "1") == "0":
        # AUDIBLE, ONCE PER PROCESS. Charter 7.3 recorded that this "disables the guard
        # entirely and silently - verified, the same fixture returned ok: true". The
        # silence was the defect, not the switch: a precept violation is a DAMAGE event
        # (the write lands, then gets reported), so a run with the detector off can do
        # real harm and leave no trace that detection was even attempted.
        #
        # Once, not per call: _guard_applies runs on every dispatch, and a warning per
        # invocation would train the reader to ignore it.
        global _GUARD_DISABLED_LOGGED
        if not _GUARD_DISABLED_LOGGED:
            _GUARD_DISABLED_LOGGED = True
            log.warning("invoke: SUITE_STRICT_OBSERVE=0 - the precept guard is OFF for "
                        "this process. Observe tools that write to the target will not "
                        "be detected or reported")
        return False
    if paths.project_root is None:
        return False  # no target to protect; _dispatch refuses the call anyway
    if paths.project_root.resolve() == paths.root.resolve():
        return False
    if getattr(tool, "writes", "none") == "target":
        return False
    return tool.authority == "Observe"


@dataclass(frozen=True)
class InvokeResult:
    """Structured outcome of a tool invocation."""
    ok: bool
    tool_id: str
    output: dict | None
    error: str | None
    exit_code: int | None


def _resolve_interpreter(paths: Paths, declared: str) -> str:
    """Prefer the shared root .venv python; fall back to the current interpreter."""
    if declared and declared not in ("${ROOT_VENV_PYTHON}", ""):
        return declared
    if paths.venv_python.is_file():
        return str(paths.venv_python)
    return sys.executable


def _dispatch(paths: Paths, tool, tool_id: str, args: dict,
              timeout: int | None = None, client: str = "unknown") -> InvokeResult:
    """Resolve + run + capture. All the failure/success return paths live here."""
    if tool is None:
        log.warning("invoke: unknown tool %r", tool_id)
        return InvokeResult(False, tool_id, None, f"unknown tool: {tool_id}", None)

    # No target bound: a sidecar in development has nothing to operate on. Refusing
    # is the correct outcome  -  inferring one is how a call lands on the wrong tree.
    if paths.project_root is None:
        return InvokeResult(
            False, tool_id, None,
            "no work target bound: this sidecar has not been vended into a project. "
            "Supply an explicit SUITE_PROJECT_ROOT, or install the sidecar into a target.",
            None)

    entry_rel = tool.invocation.get("entry", "")
    entry = (paths.root / entry_rel).resolve()
    if not entry.is_file():
        return InvokeResult(False, tool_id, None, f"entry not found: {entry_rel}", None)

    interpreter = _resolve_interpreter(paths, tool.invocation.get("interpreter", ""))
    cmd = [interpreter, str(entry), "--args-json", safe_json_dumps(args or {})]
    log.info("invoke tool=%s authority=%s category=%s", tool_id, tool.authority, tool.category)

    # Put the TOOLKIT HOME on the child's PYTHONPATH so tools can import the shared substrate
    # (`tools._toolkit`) regardless of cwd. Tools run with cwd = the WORK TARGET (project_root),
    # so path-defaulting analysis tools see the whole project (the sidecar's parent when
    # installed), while SUITE_HOME lets state tools keep their storage in the toolkit home.
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(paths.root) + (os.pathsep + existing if existing else "")
    env["SUITE_HOME"] = str(paths.root)
    env["SUITE_PROJECT_ROOT"] = str(paths.project_root)

    limit = DEFAULT_TIMEOUT_S if timeout is None else max(1, int(timeout))

    # Popen rather than subprocess.run: run() gives back no handle, so nothing could
    # stop a running tool and the only exit was to wait out the timeout. The envelope
    # contract is unchanged - stdout is still read whole, once, at the end.
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", errors="replace",
            cwd=str(paths.project_root), env=env,
            # Its own controllable tree, so cancellation reaches grandchildren.
            # Killing only the direct child leaves anything it spawned running, and an
            # orphan is invisible to any check that merely confirms the call returned.
            **proctree.spawn_kwargs(),
        )
    except OSError as e:
        return InvokeResult(False, tool_id, None, f"subprocess error: {e}", None)

    # Adopt BEFORE registering: a tree that is registered but unowned is exactly the
    # window in which a cancel would fall back to reconstructing the tree at kill time.
    handle = _Running(proc=proc, tool_id=tool_id, started=time.time(),
                      tree=proctree.ProcessTree(proc))
    with _RUNNING_LOCK:
        _RUNNING[handle.op_id] = handle
    _announce(paths, tool_id, handle.op_id, "started", client)

    try:
        out, err_text = proc.communicate(timeout=limit)
    except subprocess.TimeoutExpired:
        _terminate(proc)
        proc.communicate()
        _announce(paths, tool_id, handle.op_id, "timeout", client)
        return InvokeResult(False, tool_id, None,
                            _clean(paths, f"timeout after {limit}s"), None)
    finally:
        with _RUNNING_LOCK:
            _RUNNING.pop(handle.op_id, None)
        # Release the job handle. On Windows KILL_ON_JOB_CLOSE means this also ends
        # any descendant the tool left behind - a tool that spawns a server and exits
        # does not get to leave it holding a port.
        if handle.tree is not None:
            handle.tree.close()

    if handle.cancelled:
        # Cancellation is its OWN outcome. Reporting it as a generic failure would
        # make a deliberate stop indistinguishable from a crash in the ledger.
        _announce(paths, tool_id, handle.op_id, "cancelled", client)
        return InvokeResult(False, tool_id, None, "cancelled", CANCELLED_EXIT)

    _announce(paths, tool_id, handle.op_id, "finished", client)

    if proc.returncode != 0:
        err = ((err_text or "").strip() or (out or "").strip()
               or f"exit code {proc.returncode}")
        log.warning("invoke tool=%s failed: %s", tool_id, err)
        # Scrubbed on the RETURN path, not only when writing the ledger. The audit
        # trail was clean while the value handed to a GUI or an agent still carried
        # absolute build-machine paths.
        return InvokeResult(False, tool_id, None, _clean(paths, err), proc.returncode)

    try:
        output = json.loads(out) if out.strip() else {}
    except json.JSONDecodeError:
        output = {"raw_stdout": out}
    # A produced result is a successful *invocation*; business success is carried in
    # output["ok"] (payload preserved either way). Reflect it on InvokeResult.ok.
    ok = bool(output.get("ok", True)) if isinstance(output, dict) else True
    error = output.get("error") if (isinstance(output, dict) and not ok) else None
    if not ok:
        log.info("invoke tool=%s returned ok=false: %s", tool_id, error)
    return InvokeResult(ok, tool_id, output, error, 0)


def invoke(paths: Paths, tool_id: str, args: dict, allow: str | None = None,
           client: str = event_log.UNKNOWN_CLIENT,
           timeout: int | None = None) -> InvokeResult:
    """Resolve, ENFORCE authority, run, capture, log + record one governance event. The single
    dispatch chokepoint. `allow` (Observe|Sandbox|Apply) can only tighten the policy ceiling."""
    started = time.monotonic()
    tool = registry.get(paths, tool_id)
    authority = tool.authority if tool is not None else None
    allowed, ceiling = policy.decide(paths, authority, caller_allow=allow)
    if tool is not None and not allowed:
        log.warning("invoke DENIED tool=%s authority=%s ceiling=%s", tool_id, authority, ceiling)
        result = InvokeResult(
            False, tool_id, None,
            f"authority denied: '{tool_id}' requires {authority}, policy ceiling is {ceiling}", None)
    elif tool is not None and _guard_applies(paths, tool):
        # Precept guard: snapshot the target, dispatch, and if the tool modified the target
        # despite not declaring `writes: target`, FAIL the call and name what changed. The write
        # already happened (a subprocess we cannot sandbox on this OS), but no violation passes
        # the seam silently  -  it becomes a hard error the instant it occurs. See _design/PLAN.md
        # Phase 4 and _design/CHARTER.md sec 1.
        before, complete = _target_manifest(paths)
        result = _dispatch(paths, tool, tool_id, args, timeout, client)
        if complete:
            after, _ = _target_manifest(paths)
            changed = _manifest_diff(before, after)
            if changed:
                log.error("invoke PRECEPT-VIOLATION tool=%s writes=%s touched target: %s",
                          tool_id, getattr(tool, "writes", "none"), changed[:5])
                result = InvokeResult(
                    False, tool_id, result.output,
                    f"precept violation: '{tool_id}' (writes={getattr(tool, 'writes', 'none')}) "
                    f"modified the target it may not write to: {changed[:5]}"
                    + (f" (+{len(changed) - 5} more)" if len(changed) > 5 else ""),
                    result.exit_code)
    else:
        result = _dispatch(paths, tool, tool_id, args, timeout, client)
    duration_ms = int((time.monotonic() - started) * 1000)
    event_log.record(
        paths,
        tool_id=tool_id,
        authority=(authority or "unknown"),
        category=(tool.category if tool is not None else None),
        args=args or {},
        ok=result.ok,
        exit_code=result.exit_code,
        error=result.error,
        duration_ms=duration_ms,
        # Who caused this. Recorded, never used to grant privilege: a GUI click and an
        # agent call take the same path and meet the same authority ceiling. The point
        # is that each party can see what the other did, not that either is trusted more.
        client=client,
    )
    return result
