"""
FILE:       tools/pdf_rotate/cli.py
ROLE:       PDF page rotator.
DOMAIN:     tool
DOES:       Rotates selected pages by 90-degree increments; dry-run-first and confirm-gated.
DEPENDS ON: tools._toolkit, tools.pdf_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      REHOME/PATTERN from NoStringsPDF visual rotation.
"""
from __future__ import annotations

from tools import pdf_shared as pdf
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        path = pdf.workspace_path(str(args.get("path") or ""))
        r = pdf.reader(path)
        pages = pdf.parse_pages(str(args.get("pages") or "all"), len(r.pages))
        degrees = int(args.get("degrees", 90))
        if degrees % 90 != 0:
            return {"ok": False, "error": "degrees must be a multiple of 90"}
        dry_run = bool(args.get("dry_run", True))
        confirm = bool(args.get("confirm", False))
        if not dry_run and not confirm:
            return {"ok": False, "error": "pdf_rotate requires confirm:true when dry_run is false"}
        out = pdf.workspace_path(str(args.get("out") or pdf.default_out(path, "_rotated.pdf").relative_to(pdf.Path.cwd())))
        rotations = []
        _, PdfWriter = pdf.require_pypdf()
        writer = PdfWriter()
        for idx, page in enumerate(r.pages):
            new_page = page
            if idx in pages:
                rotations.append({"page": idx + 1, "degrees": degrees})
                if not dry_run:
                    new_page = page.rotate(degrees)
            if not dry_run:
                writer.add_page(new_page)
        if not dry_run:
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("wb") as fh:
                writer.write(fh)
        return {"tool": "pdf_rotate", "dry_run": dry_run, "out": out.as_posix(),
                "rotations": rotations, "summary": {"pages": len(rotations), "written": not dry_run}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
