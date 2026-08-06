"""
FILE:       tools/dependency_check/cli.py
ROLE:       Dependency readiness checker.
DOMAIN:     tool
DOES:       Report Python/Node dependency declaration surfaces and host tool availability
            without installing or mutating anything.
DEPENDS ON: tools._toolkit, (stdlib) pathlib, shutil, subprocess
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from tools._toolkit import tool_main


def _version(cmd: str) -> dict:
    exe = shutil.which(cmd)
    if not exe:
        return {"present": False}
    try:
        proc = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=5)
        version = (proc.stdout or proc.stderr).strip().splitlines()[0] if (proc.stdout or proc.stderr).strip() else ""
    except Exception as e:
        version = f"version check failed: {type(e).__name__}: {e}"
    return {"present": True, "command": Path(exe).name, "version": version}


@tool_main
def run(args: dict) -> dict:
    root = Path(args.get("root") or ".").resolve()
    project = Path.cwd().resolve()
    try:
        root.relative_to(project)
    except ValueError:
        return {"ok": False, "error": "root must stay inside the project workspace"}

    py_files = ["requirements.txt", "pyproject.toml", "setup.py", "setup.cfg"]
    node_files = ["package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"]
    declarations = {
        "python": [p for p in py_files if (root / p).exists()],
        "node": [p for p in node_files if (root / p).exists()],
    }
    envs = {
        "venv": (root / ".venv").exists(),
        "node_modules": (root / "node_modules").exists(),
    }
    host = {name: _version(name) for name in ("python", "pip", "node", "npm", "uv")}
    recommendations = []
    if declarations["python"] and not envs["venv"]:
        recommendations.append("Python dependencies are declared, but no root .venv is present.")
    if declarations["node"] and not envs["node_modules"]:
        recommendations.append("Node dependencies are declared, but node_modules is not present.")
    return {"tool": "dependency_check", "root": root.as_posix(), "declarations": declarations,
            "envs": envs, "host": host, "recommendations": recommendations}
