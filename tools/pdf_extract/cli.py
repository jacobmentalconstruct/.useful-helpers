"""
FILE:       tools/pdf_extract/cli.py
ROLE:       PDF page/text extractor.
DOMAIN:     tool
DOES:       Extracts selected pages to PDF or text; writes only with write:true.
DEPENDS ON: tools._toolkit, tools.pdf_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      REHOME/PATTERN from NoStringsPDF precision extract.
"""
from __future__ import annotations

from tools import pdf_shared as pdf
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        path = pdf.workspace_path(str(args.get("path") or ""))
        r = pdf.reader(path, password=str(args.get("password") or ""))
        pages = pdf.parse_pages(str(args.get("pages") or "all"), len(r.pages))
        if not pages:
            return {"ok": False, "error": "no valid pages selected"}
        mode = str(args.get("mode") or "pdf").lower()
        write = bool(args.get("write", False))
        if mode == "text":
            text = "\n\n".join((r.pages[i].extract_text() or "") for i in pages)
            written = ""
            if write:
                out = pdf.workspace_path(str(args.get("out") or pdf.default_out(path, "_extract.txt").relative_to(pdf.Path.cwd())))
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(text, encoding="utf-8")
                written = out.as_posix()
            return {"tool": "pdf_extract", "mode": "text", "pages": [i + 1 for i in pages],
                    "text": text[:int(args.get("text_limit", 4000))], "written": written,
                    "summary": {"selected_pages": len(pages), "chars": len(text)}}
        out = pdf.workspace_path(str(args.get("out") or pdf.default_out(path, "_extract.pdf").relative_to(pdf.Path.cwd())))
        if not write:
            return {"tool": "pdf_extract", "mode": "pdf", "pages": [i + 1 for i in pages],
                    "out": out.as_posix(), "written": False,
                    "summary": {"selected_pages": len(pages)}}
        result = pdf.write_pages(path, pages, out, password=str(args.get("password") or ""))
        return {"tool": "pdf_extract", "mode": "pdf", "pages": [i + 1 for i in pages],
                "written": True, "output": result, "summary": {"selected_pages": len(pages)}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
