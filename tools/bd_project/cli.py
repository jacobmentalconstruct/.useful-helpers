"""
FILE:       tools/bd_project/cli.py
ROLE:       BD neighborhood projector.
DOMAIN:     tool
DOES:       Projects a neighborhood from a BD graph DB around one or more occurrence IDs.
DEPENDS ON: tools._toolkit, tools.bd_graph_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from BDGraphPROJECTOR.
"""
from __future__ import annotations

from tools import bd_graph_shared as bd
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    db = bd.db_path_from_args(args)
    if not db.is_file():
        return {"ok": False, "error": f"db not found: {db}"}
    occurrence_ids = args.get("occurrence_ids")
    if occurrence_ids is None and args.get("occurrence_id"):
        occurrence_ids = [args.get("occurrence_id")]
    if not isinstance(occurrence_ids, list) or not occurrence_ids:
        return {"ok": False, "error": "occurrence_id or occurrence_ids is required"}
    graph = bd.project_db(db, [str(x) for x in occurrence_ids], hops=int(args.get("hops", 2)),
                          include_content=bool(args.get("include_content", True)))
    return {"tool": "bd_project", "db": db.as_posix(), "graph": graph, "summary": graph["summary"]}
