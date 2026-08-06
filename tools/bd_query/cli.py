"""
FILE:       tools/bd_query/cli.py
ROLE:       BD graph query tool.
DOMAIN:     tool
DOES:       Finds lexical/vector anchors in a BD graph DB and returns a projected subgraph.
DEPENDS ON: tools._toolkit, tools.bd_graph_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from BDQueryENGINE.
"""
from __future__ import annotations

from tools import bd_graph_shared as bd
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    query = str(args.get("query") or "").strip()
    if not query:
        return {"ok": False, "error": "query is required"}
    db = bd.db_path_from_args(args)
    if not db.is_file():
        return {"ok": False, "error": f"db not found: {db}"}
    result = bd.query_db(db, query, top_k=int(args.get("top_k", 8)), hops=int(args.get("hops", 1)))
    return {"tool": "bd_query", "db": db.as_posix(), "query": query, **result}
