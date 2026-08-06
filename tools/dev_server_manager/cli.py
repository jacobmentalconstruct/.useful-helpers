"""
FILE:       tools/dev_server_manager/cli.py
ROLE:       Guarded dev-server lifecycle manager.
DOMAIN:     tool
DOES:       Starts only profiled dev/run commands, records launched process ownership, reports
            status/tails logs/health, and stops only registered processes with confirmation.
DEPENDS ON: tools._toolkit, tools.command_profile.cli, (stdlib) json, subprocess, platform
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Narrowed to explicit registered commands; start reports process creation,
            which is not the same as a successful bind. Check health separately.
"""
from __future__ import annotations

import json
import os
import platform
import shlex
import signal
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from tools._toolkit import tool_main
from tools.command_profile.cli import run as command_profile_run

ALLOWED_KINDS = {"dev", "run"}
RUNTIME_DIR = Path("_artifacts") / "dev_servers"
STATE_FILE = "servers.json"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value)[:80] or "server"


def _runtime_root(project_root: Path) -> Path:
    return project_root / RUNTIME_DIR


def _state_path(project_root: Path) -> Path:
    return _runtime_root(project_root) / STATE_FILE


def _logs_dir(project_root: Path) -> Path:
    path = _runtime_root(project_root) / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_state(project_root: Path) -> dict:
    path = _state_path(project_root)
    if not path.exists():
        return {"version": "1.0", "servers": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": "1.0", "servers": {}}
    if not isinstance(data, dict):
        return {"version": "1.0", "servers": {}}
    data.setdefault("version", "1.0")
    data.setdefault("servers", {})
    return data


def _save_state(project_root: Path, state: dict) -> None:
    _runtime_root(project_root).mkdir(parents=True, exist_ok=True)
    _state_path(project_root).write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if platform.system().lower() == "windows":
        try:
            completed = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV"],
                                       capture_output=True, text=True, encoding="utf-8",
                                       errors="replace", timeout=5, check=False)
            return completed.returncode == 0 and str(pid) in completed.stdout
        except (OSError, subprocess.TimeoutExpired):
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _profile(project_root: Path) -> list[dict]:
    result = command_profile_run({"root": str(project_root)})
    return list(result.get("commands", [])) if result.get("ok", True) else []


def _find_command(project_root: Path, command_id: str) -> dict | None:
    for command in _profile(project_root):
        if command.get("id") == command_id:
            return command
    return None


def _argv(command: str) -> list[str]:
    if platform.system().lower() == "windows":
        return command
    return shlex.split(command)


def _refresh_entries(project_root: Path, command_id: str = "") -> list[dict]:
    state = _load_state(project_root)
    changed = False
    rows = []
    for cid, entry in list(state.get("servers", {}).items()):
        if command_id and cid != command_id:
            continue
        if not isinstance(entry, dict):
            continue
        pid = int(entry.get("pid", 0) or 0)
        alive = _is_alive(pid)
        if entry.get("alive") != alive:
            entry["alive"] = alive
            entry["last_checked_at"] = _now()
            changed = True
        row = dict(entry)
        row["command_id"] = cid
        rows.append(row)
    if changed:
        _save_state(project_root, state)
    return rows


def _tail(path: Path, lines: int) -> list[str]:
    if not path.exists():
        return []
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()[-max(1, lines):]
    except OSError:
        return []


def _health(url: str, timeout: float) -> dict:
    started = time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=timeout) as response:
            body = response.read(200)
            return {"ok": 200 <= response.status < 500, "url": url, "status_code": response.status,
                    "elapsed_ms": int((time.time() - started) * 1000),
                    "body_preview": body.decode("utf-8", errors="replace")}
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        return {"ok": False, "url": url, "status_code": None,
                "elapsed_ms": int((time.time() - started) * 1000), "error": str(exc)}


@tool_main
def run(args: dict) -> dict:
    workspace = Path.cwd().resolve()
    project_root = (workspace / str(args.get("root") or args.get("project_root") or ".")).resolve()
    if not project_root.is_dir():
        return {"ok": False, "error": f"root is not a directory: {project_root}"}
    if not _inside(workspace, project_root):
        return {"ok": False, "error": "root must stay inside the project workspace"}

    action = str(args.get("action", "status"))
    command_id = str(args.get("command_id") or "")
    timeout = max(1.0, min(float(args.get("timeout_seconds", 5)), 60.0))

    if action == "status":
        entries = _refresh_entries(project_root, command_id)
        return {"tool": "dev_server_manager", "action": action, "root": project_root.as_posix(),
                "state_path": _state_path(project_root).as_posix(), "servers": entries,
                "summary": {"registered": len(entries), "alive": sum(1 for e in entries if e.get("alive"))},
                "warnings": ["Only processes launched and registered by this tool are managed."]}

    if action == "tail":
        if not command_id:
            return {"ok": False, "error": "tail requires command_id"}
        entries = _refresh_entries(project_root, command_id)
        if not entries:
            return {"ok": False, "error": f"no registered server for command_id: {command_id}"}
        log_path = Path(str(entries[0].get("log_path", "")))
        lines = _tail(log_path, int(args.get("tail_lines", 80)))
        return {"tool": "dev_server_manager", "action": action, "command_id": command_id,
                "log_path": log_path.as_posix(), "line_count": len(lines), "lines": lines}

    if action == "health":
        entries = _refresh_entries(project_root, command_id) if command_id else []
        url = str(args.get("health_url") or (entries[0].get("health_url") if entries else "") or "")
        if not url and args.get("port"):
            url = f"http://127.0.0.1:{int(args['port'])}/"
        if not url:
            return {"ok": False, "error": "health requires health_url or port"}
        check = _health(url, timeout)
        return {"ok": check["ok"], "tool": "dev_server_manager", "action": action,
                "command_id": command_id, "health": check}

    if action not in {"start", "stop", "restart"}:
        return {"ok": False, "error": f"unknown action: {action}"}
    if not bool(args.get("confirm", False)):
        return {"ok": False, "error": f"{action} requires confirm:true"}
    if not command_id:
        return {"ok": False, "error": f"{action} requires command_id"}

    if action in {"stop", "restart"}:
        state = _load_state(project_root)
        entry = state.get("servers", {}).get(command_id)
        if not isinstance(entry, dict):
            return {"ok": False, "error": f"no registered server for command_id: {command_id}"}
        pid = int(entry.get("pid", 0) or 0)
        was_alive = _is_alive(pid)
        method = "not_alive"
        if was_alive:
            if platform.system().lower() == "windows":
                completed = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                                           capture_output=True, text=True, encoding="utf-8",
                                           errors="replace", timeout=timeout, check=False)
                method = f"taskkill:{completed.returncode}"
            else:
                os.kill(pid, signal.SIGTERM)
                method = "sigterm"
        entry["alive"] = _is_alive(pid)
        entry["stopped_at"] = _now()
        entry["last_checked_at"] = _now()
        state["servers"][command_id] = entry
        _save_state(project_root, state)
        if action == "stop":
            return {"tool": "dev_server_manager", "action": action, "command_id": command_id,
                    "was_alive": was_alive, "alive": entry["alive"], "stop_method": method}

    command = _find_command(project_root, command_id)
    if not command:
        return {"ok": False, "error": f"unknown command_id: {command_id}"}
    if command.get("kind") not in ALLOWED_KINDS:
        return {"ok": False, "error": f"command kind is not allowed for dev servers: {command.get('kind')}"}

    state = _load_state(project_root)
    existing = state.get("servers", {}).get(command_id)
    if isinstance(existing, dict) and _is_alive(int(existing.get("pid", 0) or 0)):
        return {"tool": "dev_server_manager", "action": "start", "command_id": command_id,
                "already_running": True, "server": existing}

    log_path = _logs_dir(project_root) / f"{_safe_id(command_id)}.log"
    log_handle = log_path.open("ab")
    cmd = str(command.get("command", ""))
    shell = platform.system().lower() == "windows"
    try:
        process = subprocess.Popen(_argv(cmd), cwd=str(project_root), stdout=log_handle,
                                   stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                   shell=shell,
                                   creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if shell else 0)
    except (OSError, ValueError) as exc:
        log_handle.close()
        return {"ok": False, "error": f"failed to start command: {exc}"}
    log_handle.close()

    entry = {"pid": process.pid, "alive": True, "started_at": _now(), "last_checked_at": _now(),
             "command": command, "log_path": log_path.as_posix(),
             "health_url": str(args.get("health_url") or ""), "port": args.get("port")}
    state.setdefault("servers", {})[command_id] = entry
    _save_state(project_root, state)
    return {"tool": "dev_server_manager", "action": "start", "command_id": command_id,
            "started": True, "server": entry}

