"""
FILE:       tools/project_run/cli.py
ROLE:       THE governed executor  -  run any command through the seam (the sidecar's `Bash`).
DOMAIN:     tool
DOES:       Dry-run-first. Run one command  -  an explicit `command` string (arbitrary), or a
            `profile` id detected by tools/command_profile  -  with cwd confined to the work
            target / toolkit home, a bounded timeout, size-capped stdout/stderr, and a failure
            CLASSIFICATION. Optional `evidence:true` attaches the full result to the Bag of
            Evidence (the seam already audit-logs the invocation regardless).
DEPENDS ON: tools._toolkit, tools.command_profile.cli (detection), (stdlib) subprocess, json
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Apply authority)
            has to leave it  -  closes the largest governance blind spot)
NOTES:      shell=True by design  -  its purpose is operator-confirmed arbitrary commands, governed
            + audit-logged at the seam. cwd is confined to the roots (a command may run in a
            target subdir, never an arbitrary host dir). Declares writes:target because commands
            legitimately produce build/test artifacts in the target.
"""
from __future__ import annotations

import json
import subprocess
import time

from tools._toolkit import attach_evidence, confirmed, resolve_within_roots, tool_main

_CAP = 50_000          # chars kept from each stream
_DEFAULT_TIMEOUT = 120
_MAX_TIMEOUT = 600


def _classify(returncode: int) -> str:
    """A coarse failure class so a caller can react without parsing stderr (field report F5).
    127 is the shell's 'command not found'; 126 is 'not executable'."""
    if returncode == 0:
        return "ok"
    if returncode == 127:
        return "command_not_found"
    if returncode == 126:
        return "not_executable"
    return "nonzero_exit"


def _resolve_command(args: dict):
    """Return (command, source) or an error dict. `command` wins; else `profile` is looked
    up in command_profile's detection for the work target."""
    command = str(args.get("command") or "").strip()
    if command:
        return command, "explicit"
    profile = str(args.get("profile") or "").strip()
    if not profile:
        return {"ok": False, "error": "provide 'command' (string) or 'profile' (a command id "
                "from the command_profile tool)"}
    from tools.command_profile.cli import run as _detect
    found = _detect({"root": str(args.get("cwd") or ".")})
    for c in found.get("commands", []):
        if c.get("id") == profile or c.get("kind") == profile:
            return str(c["command"]), f"profile:{c.get('id')}"
    ids = [c.get("id") for c in found.get("commands", [])]
    return {"ok": False, "error": f"no detected command matches profile {profile!r}",
            "available_profiles": ids}


def _attach_evidence(result: dict):
    """Record the run outcome in the Bag of Evidence (shared helper; see tools._toolkit)."""
    body = json.dumps({k: result.get(k) for k in
                       ("command", "cwd", "exit_code", "ok", "duration_ms",
                        "stdout_tail", "stderr_tail")}, ensure_ascii=False)
    return attach_evidence(f"project_run: {result.get('command', '')[:80]}", body)


@tool_main
def run(args: dict) -> dict:
    resolved = _resolve_command(args)
    if isinstance(resolved, dict):
        return resolved
    command, source = resolved
    cwd, err = resolve_within_roots(args.get("cwd", "."))
    if err:
        return {"ok": False, "error": err}
    if not cwd.is_dir():
        return {"ok": False, "error": f"cwd is not a directory: {cwd}"}
    timeout = min(int(args.get("timeout_s", _DEFAULT_TIMEOUT)), _MAX_TIMEOUT)

    # Preview unless the caller confirmed (apply/confirm/write)  -  and an EXPLICIT dry_run:true
    # always wins. Robust whether called through the seam (which normalizes apply->dry_run:false)
    # or directly by a sibling/test, where that normalization has not run.
    if not confirmed(args) or args.get("dry_run") is True:
        return {"tool": "project_run", "dry_run": True, "would_run": command,
                "source": source, "cwd": cwd.as_posix(), "timeout_s": timeout,
                "apply_with": {"apply": True}}

    started = time.monotonic()
    try:
        proc = subprocess.run(command, shell=True, cwd=str(cwd), capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "tool": "project_run", "command": command, "cwd": cwd.as_posix(),
                "classification": "timeout", "error": f"timeout after {timeout}s"}
    duration_ms = int((time.monotonic() - started) * 1000)

    out, err_out = proc.stdout or "", proc.stderr or ""
    result = {
        "tool": "project_run", "dry_run": False, "command": command, "source": source,
        "cwd": cwd.as_posix(), "exit_code": proc.returncode, "ok": proc.returncode == 0,
        "classification": _classify(proc.returncode), "duration_ms": duration_ms,
        "stdout_tail": out[-_CAP:], "stderr_tail": err_out[-_CAP:],
        "stdout_truncated": len(out) > _CAP, "stderr_truncated": len(err_out) > _CAP,
    }
    if args.get("evidence"):
        result["evidence_id"] = _attach_evidence(result)
    return result
