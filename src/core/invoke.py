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

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass

from src.core import event_log, policy, registry
from src.core.config import Paths
from src.lib.common import safe_json_dumps
from src.lib.logging_setup import get_logger

log = get_logger("core.invoke")

DEFAULT_TIMEOUT_S = 120

# Dirs never worth manifesting for the precept guard (regenerable / VCS / deps).
_GUARD_SKIP = {".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules", "__pycache__",
               ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build", "site-packages"}
_GUARD_MAX_FILES = 20000  # bound the stat cost; above this, skip the guard and say so


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


def _dispatch(paths: Paths, tool, tool_id: str, args: dict) -> InvokeResult:
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

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=DEFAULT_TIMEOUT_S, cwd=str(paths.project_root), env=env,
        )
    except subprocess.TimeoutExpired:
        return InvokeResult(False, tool_id, None, f"timeout after {DEFAULT_TIMEOUT_S}s", None)
    except OSError as e:
        return InvokeResult(False, tool_id, None, f"subprocess error: {e}", None)

    if proc.returncode != 0:
        err = (proc.stderr or "").strip() or (proc.stdout or "").strip() or f"exit code {proc.returncode}"
        log.warning("invoke tool=%s failed: %s", tool_id, err)
        return InvokeResult(False, tool_id, None, err, proc.returncode)

    try:
        output = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        output = {"raw_stdout": proc.stdout}
    # A produced result is a successful *invocation*; business success is carried in
    # output["ok"] (payload preserved either way). Reflect it on InvokeResult.ok.
    ok = bool(output.get("ok", True)) if isinstance(output, dict) else True
    error = output.get("error") if (isinstance(output, dict) and not ok) else None
    if not ok:
        log.info("invoke tool=%s returned ok=false: %s", tool_id, error)
    return InvokeResult(ok, tool_id, output, error, 0)


def invoke(paths: Paths, tool_id: str, args: dict, allow: str | None = None,
           client: str = event_log.UNKNOWN_CLIENT) -> InvokeResult:
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
        result = _dispatch(paths, tool, tool_id, args)
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
        result = _dispatch(paths, tool, tool_id, args)
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
