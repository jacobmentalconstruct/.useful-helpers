"""
FILE:       tools/pdf_thumbnails/cli.py
ROLE:       PDF thumbnail planner/renderer.
DOMAIN:     tool
DOES:       Plans thumbnail pages and optionally renders PNGs when PyMuPDF is installed.
DEPENDS ON: tools._toolkit, tools.pdf_shared, (optional) fitz/PyMuPDF
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from NoStringsPDF thumbnail grid. Rendering degrades gracefully.
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
        limit = max(1, min(int(args.get("limit", 12)), 200))
        pages = pages[:limit]
        write = bool(args.get("write", False))
        confirm = bool(args.get("confirm", False))
        out_dir = pdf.workspace_path(str(args.get("out_dir") or "_artifacts/pdf_thumbnails"))
        rows = [{"page": i + 1, "out": (out_dir / f"{path.stem}_p{i+1}.png").as_posix()} for i in pages]
        if write:
            if not confirm:
                return {"ok": False, "error": "pdf_thumbnails requires confirm:true when write is true"}
            try:
                import fitz
            except ImportError:
                return {"ok": False, "error": "PyMuPDF/fitz is not installed; thumbnail rendering unavailable"}
            out_dir.mkdir(parents=True, exist_ok=True)
            doc = fitz.open(str(path))
            zoom = float(args.get("zoom", 0.25))
            for row, idx in zip(rows, pages):
                pix = doc.load_page(idx).get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
                pix.save(row["out"])
                row["written"] = True
        return {"tool": "pdf_thumbnails", "path": path.as_posix(), "thumbnails": rows,
                "renderer": "fitz" if write else "plan",
                "summary": {"planned": len(rows), "written": write}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
