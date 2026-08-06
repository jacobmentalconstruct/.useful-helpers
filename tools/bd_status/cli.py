"""
FILE:       tools/bd_status/cli.py
ROLE:       BD graph DB status reader.
DOMAIN:     tool
DOES:       Reports table presence and counts for a workspace-local BD graph SQLite DB.
DEPENDS ON: tools._toolkit, tools.bd_graph_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from BDSqlDbSCRIBE status.
"""
from __future__ import annotations

from tools import bd_graph_shared as bd
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    db = bd.db_path_from_args(args)
    return {"tool": "bd_status", "db": db.as_posix(), "status": bd.db_status(db)}
