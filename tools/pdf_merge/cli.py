"""
FILE:       tools/pdf_merge/cli.py
ROLE:       PDF merger.
DOMAIN:     tool
DOES:       Merges PDFs into one output; dry-run-first and confirm-gated.
DEPENDS ON: tools._toolkit, tools.pdf_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from NoStringsPDF insert/merge operations.
"""
from __future__ import annotations

from tools import pdf_shared as pdf
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        files = [pdf.workspace_path(str(p)) for p in (args.get("files") or [])]
        if not files:
            return {"ok": False, "error": "files array is required"}
        dry_run = bool(args.get("dry_run", True))
        confirm = bool(args.get("confirm", False))
        if not dry_run and not confirm:
            return {"ok": False, "error": "pdf_merge requires confirm:true when dry_run is false"}
        _, PdfWriter = pdf.require_pypdf()
        plan = []
        writer = PdfWriter()
        for file in files:
            r = pdf.reader(file)
            plan.append({"path": file.as_posix(), "pages": len(r.pages)})
            if not dry_run:
                for page in r.pages:
                    writer.add_page(page)
        out = pdf.workspace_path(str(args.get("out") or "_artifacts/pdf/merged.pdf"))
        if not dry_run:
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("wb") as fh:
                writer.write(fh)
        return {"tool": "pdf_merge", "dry_run": dry_run, "files": plan, "out": out.as_posix(),
                "summary": {"input_files": len(files), "pages": sum(p["pages"] for p in plan),
                            "written": not dry_run}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
