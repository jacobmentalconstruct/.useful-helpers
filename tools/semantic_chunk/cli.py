"""
FILE:       tools/semantic_chunk/cli.py
ROLE:       Split text/code/docs into semantic chunks.
DOMAIN:     tool
DOES:       Chunks Python by top-level definitions, Markdown by headings, and other text by windows.
DEPENDS ON: tools._toolkit, tools.memory_workflow_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      REHOME (rewritten) from _theCELL SemanticChunkerMS/TextChunkerMS.
"""
from __future__ import annotations

from tools import memory_workflow_shared as mw
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        text, sources = mw.read_text_sources(args)
        filename = str(args.get("filename") or (sources[0]["source"] if sources else "inline.txt"))
        chunks = mw.chunk_text(text, filename, chunk_size=int(args.get("chunk_size", 1500)),
                               overlap=int(args.get("overlap", 0)))
        return {"tool": "semantic_chunk", "sources": sources, "chunks": chunks,
                "summary": {"chunks": len(chunks), "tokens": sum(c.get("tokens", 0) for c in chunks),
                            "fingerprint": mw.fingerprint(chunks)}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
