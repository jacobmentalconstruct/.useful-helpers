"""
FILE:       tools/snapshot_diff/cli.py
ROLE:       ProjectMapper snapshot differ.
DOMAIN:     tool
DOES:       Compares two ProjectMapper SQLite snapshots by captured project_files paths and
            content hashes, reporting added/removed/changed/unchanged files.
DEPENDS ON: tools._toolkit, (stdlib) hashlib, sqlite3, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from ProjectMapper snapshot artifact model.
"""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from tools._toolkit import tool_main


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _files(db: Path) -> dict[str, dict]:
    out = {}
    with sqlite3.connect(str(db)) as conn:
        for rel, size, content in conn.execute("SELECT relative_path, size_bytes, content FROM project_files"):
            digest = hashlib.sha256(str(content).encode("utf-8", errors="ignore")).hexdigest()
            out[str(rel)] = {"size_bytes": int(size), "sha256": digest}
    return out


@tool_main
def run(args: dict) -> dict:
    workspace = Path.cwd().resolve()
    left = (workspace / str(args.get("left") or "")).resolve()
    right = (workspace / str(args.get("right") or "")).resolve()
    for label, path in [("left", left), ("right", right)]:
        if not path.is_file():
            return {"ok": False, "error": f"{label} snapshot not found: {path}"}
        if not _inside(workspace, path):
            return {"ok": False, "error": f"{label} snapshot must stay inside the workspace"}

    lfiles = _files(left)
    rfiles = _files(right)
    lset = set(lfiles)
    rset = set(rfiles)
    added = sorted(rset - lset)
    removed = sorted(lset - rset)
    changed = sorted(path for path in (lset & rset) if lfiles[path]["sha256"] != rfiles[path]["sha256"])
    unchanged = len((lset & rset) - set(changed))
    limit = max(1, min(int(args.get("limit", 200)), 2000))
    return {
        "tool": "snapshot_diff",
        "left": left.as_posix(),
        "right": right.as_posix(),
        "changed": bool(added or removed or changed),
        "added": [{"path": p, **rfiles[p]} for p in added[:limit]],
        "removed": [{"path": p, **lfiles[p]} for p in removed[:limit]],
        "modified": [{"path": p, "left": lfiles[p], "right": rfiles[p]} for p in changed[:limit]],
        "summary": {
            "left_files": len(lfiles),
            "right_files": len(rfiles),
            "added": len(added),
            "removed": len(removed),
            "modified": len(changed),
            "unchanged": unchanged,
            "truncated": len(added) > limit or len(removed) > limit or len(changed) > limit,
        },
    }

