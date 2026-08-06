"""
FILE:       tools/pdf_interleave/cli.py
ROLE:       PDF interleaver.
DOMAIN:     tool
DOES:       Alternates pages from two PDFs; dry-run-first and confirm-gated.
DEPENDS ON: tools._toolkit, tools.pdf_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      REHOME/PATTERN from NoStringsPDF scanner interleave.
"""
from __future__ import annotations

from tools import pdf_shared as pdf
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        a = pdf.workspace_path(str(args.get("a") or args.get("first") or ""))
        b = pdf.workspace_path(str(args.get("b") or args.get("second") or ""))
        ra = pdf.reader(a)
        rb = pdf.reader(b)
        dry_run = bool(args.get("dry_run", True))
        confirm = bool(args.get("confirm", False))
        if not dry_run and not confirm:
            return {"ok": False, "error": "pdf_interleave requires confirm:true when dry_run is false"}
        reverse_b = bool(args.get("reverse_second", False))
        b_indices = list(range(len(rb.pages)))
        if reverse_b:
            b_indices.reverse()
        _, PdfWriter = pdf.require_pypdf()
        writer = PdfWriter()
        order = []
        for i in range(max(len(ra.pages), len(rb.pages))):
            if i < len(ra.pages):
                order.append({"source": "a", "page": i + 1})
                if not dry_run:
                    writer.add_page(ra.pages[i])
            if i < len(b_indices):
                order.append({"source": "b", "page": b_indices[i] + 1})
                if not dry_run:
                    writer.add_page(rb.pages[b_indices[i]])
        out = pdf.workspace_path(str(args.get("out") or "_artifacts/pdf/interleaved.pdf"))
        if not dry_run:
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("wb") as fh:
                writer.write(fh)
        return {"tool": "pdf_interleave", "dry_run": dry_run, "order": order, "out": out.as_posix(),
                "summary": {"pages": len(order), "written": not dry_run}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
