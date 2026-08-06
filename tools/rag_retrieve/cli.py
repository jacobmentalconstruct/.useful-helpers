"""
FILE:       tools/rag_retrieve/cli.py
ROLE:       Deterministic local retrieval over semantic chunks.
DOMAIN:     tool
DOES:       Scores chunks against a query and returns ranked anchors plus formatted context.
DEPENDS ON: tools._toolkit, tools.memory_workflow_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from _theCELL RAGRetrievalMS, replacing vector search with local lexical scoring.
"""
from __future__ import annotations

from tools import memory_workflow_shared as mw
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        query = str(args.get("query") or "")
        if not query:
            return {"ok": False, "error": "query is required"}
        chunks, sources = mw.chunks_from_args(args)
        results = mw.retrieve(query, chunks, top_k=int(args.get("top_k", 5)))
        context = mw.format_context(results, chunks) if args.get("context", True) else ""
        return {"tool": "rag_retrieve", "query": query, "sources": sources, "results": results,
                "context": context,
                "summary": {"chunks_scanned": len(chunks), "matches": len(results)}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
