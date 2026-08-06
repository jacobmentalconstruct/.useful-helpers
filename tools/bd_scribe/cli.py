"""
FILE:       tools/bd_scribe/cli.py
ROLE:       BD SQLite scribe.
DOMAIN:     tool
DOES:       Dry-run-first ingestion of emitted BD nodes into a workspace-local SQLite graph DB.
DEPENDS ON: tools._toolkit, tools.bd_graph_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      REHOME/PATTERN from BDSqlDbSCRIBE.
"""
from __future__ import annotations

from tools import bd_graph_shared as bd
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    action = str(args.get("action") or "ingest")
    db = bd.db_path_from_args(args)
    if action == "status":
        return {"tool": "bd_scribe", "db": db.as_posix(), "status": bd.db_status(db)}
    if action != "ingest":
        return {"ok": False, "error": "action must be ingest or status"}
    nodes = args.get("nodes")
    if nodes is None and args.get("nodes_path"):
        nodes = bd.read_jsonl(bd.workspace_path(str(args.get("nodes_path"))))
    if not isinstance(nodes, list):
        return {"ok": False, "error": "bd_scribe ingest requires nodes array or nodes_path"}
    dry_run = bool(args.get("dry_run", True))
    confirm = bool(args.get("confirm", False))
    if not dry_run and not confirm:
        return {"ok": False, "error": "bd_scribe requires confirm:true when dry_run is false"}
    if dry_run:
        return {"tool": "bd_scribe", "db": db.as_posix(), "dry_run": True,
                "summary": {"planned_nodes": len(nodes), "written": False}}
    status = bd.ingest_nodes(db, nodes)
    return {"tool": "bd_scribe", "db": db.as_posix(), "dry_run": False,
            "status": status, "summary": {"planned_nodes": len(nodes), "written": True}}
