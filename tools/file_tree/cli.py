"""
FILE:       tools/file_tree/cli.py
ROLE:       Snapshot the project file tree (directories/files) with filters and ignores.
DOMAIN:     tool
DOES:       Walks a root (default cwd = project root), pruning noisy dirs (.git, .venv,
            __pycache__, node_modules, logs, ...), and returns rows (path, kind,
            size, ext) + by_kind counts, capped at `limit`. Pure Observe.
DEPENDS ON: tools._toolkit, (stdlib) os, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Walks the real filesystem. Ignore rules are hardcoded; they belong in the
            per-project profile. See _design/CHARTER.md sec 3.
"""
from __future__ import annotations

import os
from pathlib import Path

from tools._toolkit import is_instance_path, tool_main

_DEFAULT_IGNORES = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",     "logs", ".mypy_cache", ".pytest_cache", "build", "dist", ".idea", ".vscode",
}


def _entry(root: Path, path: Path, kind: str) -> dict:
    size = None
    if kind == "file":
        try:
            size = path.stat().st_size
        except OSError:
            size = None
    return {
        "path": str(path.relative_to(root)).replace("\\", "/"),
        "kind": kind,
        "size_bytes": size,
        "ext": path.suffix if kind == "file" else "",
    }


@tool_main
def run(args: dict) -> dict:
    root = Path(args.get("root") or ".").resolve()
    if not root.is_dir():
        return {"ok": False, "error": f"not a directory: {root}"}

    kind_filter = args.get("kind")  # "file" | "directory" | None
    ext = args.get("ext")
    norm_ext = (ext if ext.startswith(".") else f".{ext}") if ext else None
    limit = int(args.get("limit", 1000))
    ignores = set(_DEFAULT_IGNORES)
    extra = args.get("ignore")
    if isinstance(extra, list):
        ignores |= {str(x) for x in extra}

    entries: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune the sidecar by PATH, never by name: the installed folder may have
        # been renamed, and an unrelated target directory may share the default name.
        dirnames[:] = sorted(d for d in dirnames if d not in ignores
                             and not is_instance_path(Path(dirpath) / d))
        here = Path(dirpath)
        if kind_filter in (None, "directory"):
            for d in dirnames:
                entries.append(_entry(root, here / d, "directory"))
        if kind_filter in (None, "file"):
            for f in sorted(filenames):
                if norm_ext and not f.endswith(norm_ext):
                    continue
                entries.append(_entry(root, here / f, "file"))

    truncated = len(entries) > limit
    rows = entries[:limit]
    by_kind: dict[str, int] = {}
    for r in rows:
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1

    return {
        "tool": "file_tree",
        "root": str(root).replace("\\", "/"),
        "total_returned": len(rows),
        "truncated": truncated,
        "by_kind": by_kind,
        "rows": rows,
    }
