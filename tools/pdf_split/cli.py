"""
FILE:       tools/pdf_split/cli.py
ROLE:       PDF splitter.
DOMAIN:     tool
DOES:       Splits a PDF into page-count chunks; dry-run-first and confirm-gated.
DEPENDS ON: tools._toolkit, tools.pdf_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from NoStringsPDF smart split.
"""
from __future__ import annotations

from tools import pdf_shared as pdf
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        path = pdf.workspace_path(str(args.get("path") or ""))
        r = pdf.reader(path, password=str(args.get("password") or ""))
        max_pages = max(1, int(args.get("max_pages", 10)))
        out_dir = pdf.workspace_path(str(args.get("out_dir") or "_artifacts/pdf"))
        dry_run = bool(args.get("dry_run", True))
        confirm = bool(args.get("confirm", False))
        if not dry_run and not confirm:
            return {"ok": False, "error": "pdf_split requires confirm:true when dry_run is false"}
        chunks = []
        for start in range(0, len(r.pages), max_pages):
            end = min(start + max_pages, len(r.pages))
            out = out_dir / f"{path.stem}_part{len(chunks)+1}_{start+1}-{end}.pdf"
            row = {"pages": list(range(start + 1, end + 1)), "out": out.as_posix()}
            if not dry_run:
                row["written"] = pdf.write_pages(path, list(range(start, end)), out)
            chunks.append(row)
        return {"tool": "pdf_split", "dry_run": dry_run, "chunks": chunks,
                "summary": {"chunks": len(chunks), "pages": len(r.pages), "written": not dry_run}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
