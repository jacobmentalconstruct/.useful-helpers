"""
FILE:       tools/artifact_catalog/cli.py
ROLE:       Generated artifact cataloger.
DOMAIN:     tool
DOES:       Scans a workspace-local artifact root, classifies generated files, computes sizes
            and optional hashes, and returns a compact inventory.
DEPENDS ON: tools._toolkit, (stdlib) hashlib, os, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from ProjectMapper and MicroserviceLIBRARY catalog/export tools.
"""
from __future__ import annotations

import hashlib
import os
from collections import Counter
from pathlib import Path

from tools._toolkit import suite_home, tool_main


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".sqlite", ".sqlite3", ".db"}:
        return "sqlite"
    if suffix == ".json":
        return "json"
    if suffix in {".md", ".txt"}:
        return "text"
    if suffix in {".sha256", ".hash"}:
        return "checksum"
    if suffix in {".zip", ".7z", ".gz"}:
        return "archive"
    return suffix.lstrip(".") or "file"


def _sha(path: Path, max_bytes: int) -> str:
    try:
        if path.stat().st_size > max_bytes:
            return ""
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


@tool_main
def run(args: dict) -> dict:
    workspace = Path.cwd().resolve()
    # Generated artifacts default under the toolkit home (SUITE_HOME/_artifacts), so catalog there
    # by default; an explicit `root` resolves against the work target for opt-in project scans.
    root_arg = args.get("root")
    root = (workspace / str(root_arg)).resolve() if root_arg else (suite_home() / "_artifacts")
    if not root.exists():
        return {"tool": "artifact_catalog", "root": root.as_posix(), "artifacts": [],
                "summary": {"count": 0, "total_bytes": 0, "by_kind": {}}}
    if not root.is_dir():
        return {"ok": False, "error": f"root is not a directory: {root}"}
    if not _inside(workspace, root):
        return {"ok": False, "error": "root must stay inside the workspace"}

    limit = max(1, min(int(args.get("limit", 500)), 5000))
    hash_files = bool(args.get("hash", False))
    max_hash_bytes = max(1, min(int(args.get("max_hash_bytes", 2_000_000)), 50_000_000))
    rows = []
    total = 0
    by_kind = Counter()
    for current, dir_names, file_names in os.walk(root):
        dir_names[:] = sorted(d for d in dir_names if d not in {"__pycache__"})
        for name in sorted(file_names):
            path = Path(current) / name
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            kind = _kind(path)
            total += size
            by_kind[kind] += 1
            row = {"path": path.relative_to(workspace).as_posix(), "kind": kind, "size_bytes": size}
            if hash_files:
                row["sha256"] = _sha(path, max_hash_bytes)
            rows.append(row)
            if len(rows) >= limit:
                return {"tool": "artifact_catalog", "root": root.as_posix(), "artifacts": rows,
                        "summary": {"count": len(rows), "total_bytes": total,
                                    "by_kind": dict(sorted(by_kind.items())), "truncated": True}}
    return {"tool": "artifact_catalog", "root": root.as_posix(), "artifacts": rows,
            "summary": {"count": len(rows), "total_bytes": total,
                        "by_kind": dict(sorted(by_kind.items())), "truncated": False}}

