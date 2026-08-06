"""
FILE:       tools/pdf_compress/cli.py
ROLE:       PDF stream compressor.
DOMAIN:     tool
DOES:       Rewrites a PDF with compressed page content streams; dry-run-first and confirm-gated.
DEPENDS ON: tools._toolkit, tools.pdf_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from NoStringsPDF pro compression; image downsampling is deferred.
"""
from __future__ import annotations

from tools import pdf_shared as pdf
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        path = pdf.workspace_path(str(args.get("path") or ""))
        r = pdf.reader(path)
        dry_run = bool(args.get("dry_run", True))
        confirm = bool(args.get("confirm", False))
        if not dry_run and not confirm:
            return {"ok": False, "error": "pdf_compress requires confirm:true when dry_run is false"}
        out = pdf.workspace_path(str(args.get("out") or pdf.default_out(path, "_compressed.pdf").relative_to(pdf.Path.cwd())))
        original = path.stat().st_size
        written_size = 0
        if not dry_run:
            _, PdfWriter = pdf.require_pypdf()
            writer = PdfWriter()
            for page in r.pages:
                try:
                    page.compress_content_streams()
                except Exception:
                    pass
                writer.add_page(page)
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("wb") as fh:
                writer.write(fh)
            written_size = out.stat().st_size
        return {"tool": "pdf_compress", "dry_run": dry_run, "out": out.as_posix(),
                "summary": {"pages": len(r.pages), "original_bytes": original,
                            "written_bytes": written_size, "written": not dry_run}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
