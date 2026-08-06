"""
FILE:       tools/bd_index/cli.py
ROLE:       End-to-end BD graph indexer.
DOMAIN:     tool
DOES:       Runs split -> emit -> scribe for a workspace-local source into a BD graph DB.
DEPENDS ON: tools._toolkit, tools.bd_graph_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Suite-native composition of the BD split/emit/scribe donor flow.
"""
from __future__ import annotations

from tools import bd_graph_shared as bd
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    source = bd.workspace_path(str(args.get("path") or args.get("root") or "."))
    if not source.exists():
        return {"ok": False, "error": f"path not found: {source}"}
    db = bd.db_path_from_args(args)
    dry_run = bool(args.get("dry_run", True))
    confirm = bool(args.get("confirm", False))
    if not dry_run and not confirm:
        return {"ok": False, "error": "bd_index requires confirm:true when dry_run is false"}
    hunks = bd.split_path(source, max_size=int(args.get("max_size", 1000)),
                          max_files=int(args.get("max_files", 250)),
                          limit=int(args.get("limit", 5000)))
    if dry_run:
        # A preview counts hunks; it must NOT embed the whole corpus (one node per hunk), which
        # would fire Ollama for nothing. emit is one-node-per-hunk, so the node count is len(hunks).
        return {"tool": "bd_index", "db": db.as_posix(), "dry_run": True,
                "summary": {"hunks": len(hunks), "nodes": len(hunks), "written": False}}
    # CAS reuse: skip re-embedding content already in this DB (same backend). Cheap re-index.
    cache = bd.load_reusable_vectors(db)
    reused = len({h.get("hunk_id") for h in hunks} & set(cache)) if cache else 0
    nodes = bd.emit_nodes(hunks, dimensions=int(args.get("dimensions", 16)),
                          limit=len(hunks), vector_cache=cache)
    status = bd.ingest_nodes(db, nodes)
    return {"tool": "bd_index", "db": db.as_posix(), "dry_run": False,
            "status": status,
            "summary": {"hunks": len(hunks), "nodes": len(nodes),
                        "reused_vectors": reused, "embedded": len(nodes) - reused,
                        "backend": bd.current_embed_backend(), "written": True}}
