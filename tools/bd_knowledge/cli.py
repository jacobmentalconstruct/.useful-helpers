"""
FILE:       tools/bd_knowledge/cli.py
ROLE:       Ingest project memory (journal + evidence) into the BD graph as KNOWLEDGE nodes.
DOMAIN:     tool
DOES:       Reads the state-root journal/evidence DBs (or explicit paths), creates a knowledge
            node per entry/item, and links each to the code it references (relates_to edges), so
            bd_why can traverse from code to the decisions/proof behind it.
DEPENDS ON: tools._toolkit, tools.bd_graph_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Preview-first (dry_run default). Idempotent: content-hash dedup + edge de-dup, so
            re-running after new journal entries only adds the new knowledge and links.
"""
from __future__ import annotations

from pathlib import Path

from tools import bd_graph_shared as bd
from tools._toolkit import state_root, tool_main


@tool_main
def run(args: dict) -> dict:
    db = bd.db_path_from_args(args)
    if not db.is_file():
        return {"ok": False, "error": f"graph db not found: {db} (run bd_index first)"}

    home = state_root()
    journal_db = Path(args["journal_db"]) if args.get("journal_db") else home / "journal.sqlite3"
    evidence_db = Path(args["evidence_db"]) if args.get("evidence_db") else home / "evidence.sqlite3"
    journal = bd.read_state_journal(journal_db)
    evidence = bd.read_state_evidence(evidence_db)

    dry_run = bool(args.get("dry_run", True))
    confirm = bool(args.get("confirm", False)) or bool(args.get("apply", False))
    if dry_run or not confirm:
        return {"tool": "bd_knowledge", "db": db.as_posix(), "dry_run": True,
                "summary": {"journal_entries": len(journal), "evidence_items": len(evidence),
                            "written": False},
                "apply_with": {"apply": True}}

    result = bd.ingest_knowledge(db, journal, evidence, link_cap=int(args.get("link_cap", 50)))
    return {"tool": "bd_knowledge", "db": db.as_posix(), "dry_run": False,
            "summary": {"journal_entries": len(journal), "evidence_items": len(evidence),
                        "knowledge_nodes": result["knowledge_nodes"],
                        "relations_added": result["relations_added"], "written": True},
            "status": result["status"]}
