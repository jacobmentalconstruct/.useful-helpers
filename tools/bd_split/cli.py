"""
FILE:       tools/bd_split/cli.py
ROLE:       BD HyperHunk splitter.
DOMAIN:     tool
DOES:       Splits workspace-local text/code into deterministic HyperHunk-like records.
DEPENDS ON: tools._toolkit, tools.bd_graph_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from BDHyperNodeSPLITTER.
"""
from __future__ import annotations

from tools import bd_graph_shared as bd
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    max_size = int(args.get("max_size", 1000))
    limit = max(1, min(int(args.get("limit", 200)), 5000))
    if args.get("text") is not None:
        origin_id = str(args.get("origin_id") or "inline.txt")
        hunks = bd.split_text(str(args.get("text") or ""), origin_id, max_size=max_size)[:limit]
    else:
        path = bd.workspace_path(str(args.get("path") or args.get("root") or "."))
        if not path.exists():
            return {"ok": False, "error": f"path not found: {path}"}
        hunks = bd.split_path(path, max_size=max_size, max_files=int(args.get("max_files", 250)),
                              limit=limit)
    return {"tool": "bd_split", "hunks": hunks,
            "summary": {"hunks": len(hunks), "truncated": len(hunks) >= limit,
                        "max_size": max_size}}
