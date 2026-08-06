"""
FILE:       tools/process_port_inspector/cli.py
ROLE:       Read-only process and port inspector.
DOMAIN:     tool
DOES:       Report relevant running processes and occupied/listening ports using platform
            command fallbacks. Never starts, stops, or kills processes.
DEPENDS ON: tools._toolkit, (stdlib) csv, platform, subprocess
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Degrades usefully when tasklist is unavailable: netstat evidence still
            identifies listeners.
"""
from __future__ import annotations

import csv
import platform
import subprocess
from io import StringIO

from tools._toolkit import tool_main

_DEFAULT_NAMES = ["python", "node", "npm", "uvicorn", "flask", "django", "vite", "docker"]


def _run_cmd(args: list[str], timeout: float) -> dict:
    try:
        completed = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=timeout, check=False)
        return {"ok": completed.returncode == 0, "code": completed.returncode,
                "stdout": completed.stdout or "", "stderr": completed.stderr or ""}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"ok": False, "code": -1, "stdout": "", "stderr": str(e)}


def _windows_processes(timeout: float, names: list[str], limit: int) -> tuple[list[dict], dict]:
    raw = _run_cmd(["tasklist", "/fo", "csv"], timeout)
    if not raw["ok"]:
        return [], {"engine": "tasklist", "ok": False, "error": raw["stderr"][:300]}
    wanted = [n.lower() for n in names]
    rows = []
    for row in csv.DictReader(StringIO(raw["stdout"])):
        image = row.get("Image Name", "")
        if wanted and not any(n in image.lower() for n in wanted):
            continue
        rows.append({"pid": row.get("PID", ""), "name": image,
                     "session_name": row.get("Session Name", ""),
                     "memory_usage": row.get("Mem Usage", "")})
        if len(rows) >= limit:
            break
    return rows, {"engine": "tasklist", "ok": True}


def _posix_processes(timeout: float, names: list[str], limit: int) -> tuple[list[dict], dict]:
    raw = _run_cmd(["ps", "-eo", "pid=,comm=,args="], timeout)
    if not raw["ok"]:
        return [], {"engine": "ps", "ok": False, "error": raw["stderr"][:300]}
    wanted = [n.lower() for n in names]
    rows = []
    for line in raw["stdout"].splitlines():
        text = line.strip()
        if not text or (wanted and not any(n in text.lower() for n in wanted)):
            continue
        parts = text.split(None, 2)
        rows.append({"pid": parts[0] if len(parts) > 0 else "",
                     "name": parts[1] if len(parts) > 1 else "",
                     "command": parts[2][:500] if len(parts) > 2 else ""})
        if len(rows) >= limit:
            break
    return rows, {"engine": "ps", "ok": True}


def _parse_netstat(stdout: str, wanted: set[int]) -> list[dict]:
    rows = []
    for line in stdout.splitlines():
        text = line.strip()
        if not text or not text.lower().startswith(("tcp", "udp")):
            continue
        parts = text.split()
        if len(parts) < 4:
            continue
        proto = parts[0]
        local = parts[1]
        try:
            port = int(local.rsplit(":", 1)[1])
        except (IndexError, ValueError):
            continue
        if wanted and port not in wanted:
            continue
        state = parts[3] if proto.lower().startswith("tcp") and len(parts) > 3 else ""
        pid = parts[4] if proto.lower().startswith("tcp") and len(parts) > 4 else parts[3] if len(parts) > 3 else ""
        rows.append({"protocol": proto, "local_address": local, "port": port, "state": state, "pid": pid})
    return rows


def _ports(timeout: float, wanted: set[int], limit: int) -> tuple[list[dict], dict]:
    if platform.system().lower() == "windows":
        raw = _run_cmd(["netstat", "-ano"], timeout)
        engine = "netstat -ano"
    else:
        raw = _run_cmd(["ss", "-ltnp"], timeout)
        engine = "ss -ltnp"
        if not raw["ok"]:
            raw = _run_cmd(["netstat", "-an"], timeout)
            engine = "netstat -an"
    if not raw["ok"]:
        return [], {"engine": engine, "ok": False, "error": raw["stderr"][:300]}
    rows = _parse_netstat(raw["stdout"], wanted)
    return rows[:limit], {"engine": engine, "ok": True, "truncated": len(rows) > limit,
                          "total_before_limit": len(rows)}


@tool_main
def run(args: dict) -> dict:
    timeout = float(args.get("timeout_seconds", 5))
    names = [str(x) for x in args.get("process_name_contains", _DEFAULT_NAMES)]
    wanted_ports = {int(x) for x in args.get("ports", [])}
    max_processes = max(1, min(int(args.get("max_processes", 80)), 1000))
    max_ports = max(1, min(int(args.get("max_ports", 200)), 2000))

    if platform.system().lower() == "windows":
        processes, process_source = _windows_processes(timeout, names, max_processes)
    else:
        processes, process_source = _posix_processes(timeout, names, max_processes)
    ports, port_source = _ports(timeout, wanted_ports, max_ports)

    return {
        "tool": "process_port_inspector",
        "filters": {"ports": sorted(wanted_ports), "process_name_contains": names},
        "processes": processes,
        "ports": ports,
        "summary": {
            "process_count": len(processes),
            "port_count": len(ports),
            "process_source": process_source,
            "port_source": port_source,
        },
        "warnings": ["Visibility depends on host permissions and available OS commands."],
    }
