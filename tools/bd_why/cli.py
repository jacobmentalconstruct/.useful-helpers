"""
FILE:       tools/bd_why/cli.py
ROLE:       The "why" query  -  from a code path/symbol to the decisions and evidence behind it.
DOMAIN:     tool
DOES:       Given a file path or symbol, traverse the KNOWLEDGE relates_to edges in a BD graph DB
            and return the journal entries / evidence items linked to that code.
DEPENDS ON: tools._toolkit, tools.bd_graph_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Read-only. Requires that bd_knowledge has ingested journal/evidence into the graph;
            absent that, code matches but returns no knowledge.
"""
from __future__ import annotations

from tools import bd_graph_shared as bd
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    target = str(args.get("target") or args.get("path") or args.get("symbol") or "").strip()
    if not target:
        return {"ok": False, "error": "target (a file path or symbol) is required"}
    db = bd.db_path_from_args(args)
    if not db.is_file():
        return {"ok": False, "error": f"db not found: {db}"}
    result = bd.why_db(db, target, limit=int(args.get("limit", 20)))
    return {"tool": "bd_why", "db": db.as_posix(), **result}
