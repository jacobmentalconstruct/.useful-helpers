"""
FILE:       tools/pdf_info/cli.py
ROLE:       PDF metadata reader.
DOMAIN:     tool
DOES:       Reports page count, encryption state, metadata, page boxes, rotations, and size.
DEPENDS ON: tools._toolkit, tools.pdf_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from NoStringsPDF load/get_metadata/page navigation features.
"""
from __future__ import annotations

from tools import pdf_shared as pdf
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        path = pdf.workspace_path(str(args.get("path") or ""))
        if not path.is_file():
            return {"ok": False, "error": f"PDF not found: {path}"}
        r = pdf.reader(path, password=str(args.get("password") or ""))
        sizes = pdf.page_sizes(r)
        return {"tool": "pdf_info", "path": path.as_posix(), "page_count": len(r.pages),
                "encrypted": bool(r.is_encrypted), "metadata": dict(r.metadata or {}),
                "pages": sizes[:int(args.get("limit", 20))],
                "summary": {"pages": len(r.pages), "size_bytes": path.stat().st_size,
                            "truncated": len(sizes) > int(args.get("limit", 20))}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
