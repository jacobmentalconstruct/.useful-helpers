"""
FILE:       tools/host_probe/cli.py
ROLE:       Probe the host environment  -  Python, platform, and common-tool availability.
DOMAIN:     tool
DOES:       Reads sys/platform info and runs `<tool> --version` for a small allowlist
            (shell=False). Pure Observe; no mutation. Redacts user paths from version output.
DEPENDS ON: tools._toolkit, (stdlib) os, platform, re, shutil, subprocess, sys
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Observe-only, with an allowlist + user-path redaction.
"""
from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

from tools._toolkit import tool_main

_PROBE_TOOLS = (
    "git", "python", "python3", "pip", "pip3", "node", "npm", "go",
    "cargo", "rustc", "docker", "make", "uv",
)


def _sanitize_version_text(text: str) -> str:
    text = re.sub(r"[A-Za-z]:\\Users\\[^\s)]+", "<redacted-user-path>", text)
    text = re.sub(r"[A-Za-z]:/Users/[^\s)]+", "<redacted-user-path>", text)
    return text


def _version_of(executable_path: str) -> str:
    try:
        cp = subprocess.run([executable_path, "--version"], capture_output=True,
                            text=True, timeout=5.0, shell=False)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    out = ((cp.stdout or "") + (cp.stderr or "")).strip()
    first_line = out.splitlines()[0] if out else ""
    return _sanitize_version_text(first_line)


@tool_main
def run(args: dict) -> dict:
    tools_present: dict[str, dict] = {}
    for name in _PROBE_TOOLS:
        path = shutil.which(name)
        if path is None:
            tools_present[name] = {"present": False}
            continue
        tools_present[name] = {"present": True, "command": Path(path).name,
                               "version": _version_of(path)}
    return {
        "tool": "host_probe",
        "python": {
            "version": platform.python_version(),
            "version_info": list(sys.version_info[:5]),
            "implementation": platform.python_implementation(),
            "executable_name": Path(sys.executable).name,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "env": {
            "cwd": os.getcwd(),
            "path_count": len(os.environ.get("PATH", "").split(os.pathsep)),
        },
        "tools_present": tools_present,
    }
