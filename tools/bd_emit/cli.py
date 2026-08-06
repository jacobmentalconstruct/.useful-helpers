"""
FILE:       tools/bd_emit/cli.py
ROLE:       BD HyperNode emitter.
DOMAIN:     tool
DOES:       Converts HyperHunk-like records into deterministic HyperNode-like records.
DEPENDS ON: tools._toolkit, tools.bd_graph_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from BDHyperNeuronEMITTER.
"""
from __future__ import annotations

from tools import bd_graph_shared as bd
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    hunks = args.get("hunks")
    if hunks is None and args.get("hunks_path"):
        path = bd.workspace_path(str(args.get("hunks_path")))
        hunks = bd.read_jsonl(path)
    if not isinstance(hunks, list):
        return {"ok": False, "error": "bd_emit requires hunks array or hunks_path"}
    dimensions = int(args.get("dimensions", 16))
    limit = max(1, min(int(args.get("limit", 200)), 5000))
    nodes = bd.emit_nodes(hunks, dimensions=dimensions, limit=limit)
    return {"tool": "bd_emit", "nodes": nodes,
            "summary": {"nodes": len(nodes), "dimensions": dimensions,
                        "truncated": len(hunks) > len(nodes)}}
