"""
FILE:       tools/workspace_audit/cli.py
ROLE:       Workspace boundary and runtime-shape audit.
DOMAIN:     tool
DOES:       Report project root facts, donor/runtime folders, ignored/generated surfaces,
            git presence, and current write-safety assumptions.
DEPENDS ON: tools._toolkit, (stdlib) pathlib, os
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Subject is the toolkit itself, not the project  -  it defaults to SUITE_HOME.
            See _design/CHARTER.md sec 5.
"""
from __future__ import annotations

import os
from pathlib import Path

from tools._toolkit import suite_home, tool_main

_SURFACES = ["src", "tools", "apps", "config", "_docs", "_state", "_artifacts", "logs"]
_GENERATED = ["logs", "config/registry.json", "_artifacts", "__pycache__"]


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


@tool_main
def run(args: dict) -> dict:
    # This audits the TOOLKIT's own control plane (src/tools/apps/config/_docs/...), so it defaults
    # to the toolkit home, not the work-target cwd (which is the host project under a sidecar
    # install). An explicit `root` still resolves against the work target.
    root_arg = args.get("root")
    root = (Path.cwd() / str(root_arg)).resolve() if root_arg else suite_home()
    if not root.exists() or not root.is_dir():
        return {"ok": False, "error": f"root is not a directory: {root}"}
    project = Path.cwd().resolve()
    project_root = Path(os.environ.get("SUITE_PROJECT_ROOT") or project).resolve()
    try:
        root.relative_to(project)
    except ValueError:
        return {"ok": False, "error": "root must stay inside the project workspace"}

    surfaces = []
    for name in _SURFACES:
        p = root / name
        surfaces.append({"path": name, "exists": p.exists(), "kind": "directory" if p.is_dir() else "file" if p.is_file() else "missing"})

    generated = [{"path": name, "exists": (root / name).exists()} for name in _GENERATED]

    return {
        "tool": "workspace_audit",
        "root": root.as_posix(),
        "toolkit_home": suite_home().as_posix(),
        "project_root": project_root.as_posix(),
        "relative_root": _rel(project, root),
        "is_git_repo": (root / ".git").exists(),
        "has_gitignore": (root / ".gitignore").exists(),
        "control_plane": {
            "src": (root / "src").is_dir(),
            "tools": (root / "tools").is_dir(),
            "apps": (root / "apps").is_dir(),
            "registry": (root / "config" / "registry.json").exists(),
        },
        "surfaces": surfaces,
        "generated_surfaces": generated,
        "notes": [
            "Apply tools should default to preview/dry-run and write only inside the workspace",
        ],
    }
