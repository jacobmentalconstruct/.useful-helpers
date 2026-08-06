"""
FILE:       tools/read_file/cli.py
ROLE:       Read a file's contents through the governed seam (the sidecar's `Read`).
DOMAIN:     tool
DOES:       Return the text of a path, optionally a 1-based line range (offset/limit), byte-capped.
            Refuses paths outside the work target / toolkit home. Pure Observe.
DEPENDS ON: tools._toolkit, (stdlib) pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      The single most-used verb an agent has. Without it every file read left the seam.
            Line-addressable so an agent can pull just the range a `report`/`bd_query` citation
            points at, keeping context small.
"""
from __future__ import annotations

from tools._toolkit import resolve_within_roots, tool_main

_MAX_BYTES = 1_000_000


@tool_main
def run(args: dict) -> dict:
    path, err = resolve_within_roots(args.get("path", ""))
    if err:
        return {"ok": False, "error": err}
    if not path.is_file():
        return {"ok": False, "error": f"not a file: {path}"}

    max_bytes = max(1, min(int(args.get("max_bytes", _MAX_BYTES)), _MAX_BYTES))
    size = path.stat().st_size
    raw = path.read_text(encoding="utf-8", errors="replace")
    byte_truncated = size > max_bytes
    if byte_truncated:
        raw = raw[:max_bytes]

    lines = raw.splitlines()
    total_lines = len(lines)
    offset = args.get("offset")
    limit = args.get("limit")
    start = max(1, int(offset)) if offset is not None else 1
    if limit is not None:
        end = min(total_lines, start + max(0, int(limit)) - 1)
    else:
        end = total_lines
    sliced = lines[start - 1:end] if total_lines else []
    line_truncated = (start > 1) or (end < total_lines)

    return {
        "tool": "read_file",
        "path": path.as_posix(),
        "content": "\n".join(sliced),
        "start_line": start if total_lines else 0,
        "end_line": end,
        "total_lines": total_lines,
        "bytes": size,
        "truncated": byte_truncated or line_truncated,
    }
