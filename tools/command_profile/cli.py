"""
FILE:       tools/command_profile/cli.py
ROLE:       Project command detector.
DOMAIN:     tool
DOES:       Inspect common project files and return stable command IDs for test/dev/build/run.
DEPENDS ON: tools._toolkit, (stdlib) json, pathlib, configparser
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Detects the project's commands; it does not run them. See tools/project_run.
"""
from __future__ import annotations

import json
from pathlib import Path

from tools._toolkit import tool_main


def _add(commands: list[dict], cid: str, kind: str, command: str, source: str) -> None:
    if not any(c["id"] == cid for c in commands):
        commands.append({"id": cid, "kind": kind, "command": command, "source": source})


@tool_main
def run(args: dict) -> dict:
    root = Path(args.get("root") or ".").resolve()
    project = Path.cwd().resolve()
    try:
        root.relative_to(project)
    except ValueError:
        return {"ok": False, "error": "root must stay inside the project workspace"}
    if not root.is_dir():
        return {"ok": False, "error": f"root is not a directory: {root}"}

    commands: list[dict] = []
    if (root / "smoke_test.py").exists():
        _add(commands, "smoke", "test", "python smoke_test.py", "smoke_test.py")
    if (root / "tests").is_dir():
        _add(commands, "unittest", "test", "python -m unittest discover -s tests -t .", "tests/")
    if (root / "run.bat").exists():
        _add(commands, "run_bat", "run", "run.bat", "run.bat")

    # Lint. A project carrying a linter config obviously has a lint command, but this
    # detected none - so `project_run` could not reach linting either, and the only
    # path to it was a single test that skips silently when the linter is absent.
    # Until a dedicated lint tool exists this is what makes it reachable through the
    # seam at all. Recorded as corollary 2 of the lint capability gap.
    for cfg, cmd in (
        ("ruff.toml", "python -m ruff check ."),
        (".ruff.toml", "python -m ruff check ."),
        ("setup.cfg", "python -m flake8"),
        (".flake8", "python -m flake8"),
    ):
        if (root / cfg).exists():
            _add(commands, "lint", "lint", cmd, cfg)
            break
    if (root / "pyproject.toml").exists():
        try:
            body = (root / "pyproject.toml").read_text(encoding="utf-8", errors="replace")
        except OSError:
            body = ""
        if "[tool.ruff" in body:
            _add(commands, "lint", "lint", "python -m ruff check .", "pyproject.toml")
    if (root / "setup_env.bat").exists():
        _add(commands, "setup_env", "setup", "setup_env.bat", "setup_env.bat")

    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            for name in sorted((data.get("scripts") or {}).keys()):
                kind = "test" if "test" in name else "dev" if name in {"dev", "start"} else "build" if "build" in name else "script"
                _add(commands, f"npm_{name}", kind, f"npm run {name}", "package.json")
        except (OSError, json.JSONDecodeError):
            pass

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8", errors="replace")
        if "[tool.pytest" in text or "pytest" in text:
            _add(commands, "pytest", "test", "python -m pytest", "pyproject.toml")
        if "[project.scripts]" in text:
            _add(commands, "python_project_scripts", "run", "python -m <declared script>", "pyproject.toml")

    return {"tool": "command_profile", "root": root.as_posix(), "count": len(commands), "commands": commands}
