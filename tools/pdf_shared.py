"""
FILE:       tools/pdf_shared.py
ROLE:       Shared PDF helpers for the T-doc-pdf tool pack.
DOMAIN:     tool
DOES:       Opens workspace-local PDFs with pypdf, parses page ranges, writes selected pages,
            and performs simple PDF document assembly operations.
DEPENDS ON: (optional external) pypdf, (stdlib) pathlib, re
WIRES TO:   pdf_info, pdf_extract, pdf_split, pdf_compress, pdf_merge, pdf_interleave,
            pdf_rotate, pdf_thumbnails
NOTES:      REHOME/PATTERN from NoStringsPDF's PDF engine. Uses pypdf because it is available
            in this workspace; PyMuPDF thumbnail rendering is optional.
"""
from __future__ import annotations

import re
from pathlib import Path


def inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def workspace_path(value: str) -> Path:
    root = Path.cwd().resolve()
    path = (root / value).resolve()
    if not inside(root, path):
        raise ValueError("path must stay inside the workspace")
    return path


def require_pypdf():
    try:
        from pypdf import PdfReader, PdfWriter
        return PdfReader, PdfWriter
    except ImportError as exc:
        raise RuntimeError("pypdf is required for PDF tools; install dependencies first") from exc


def reader(path: Path, password: str = ""):
    PdfReader, _ = require_pypdf()
    r = PdfReader(str(path))
    if r.is_encrypted and password:
        r.decrypt(password)
    return r


def parse_pages(spec: str, page_count: int) -> list[int]:
    if not spec or spec.strip().lower() in {"all", "*"}:
        return list(range(page_count))
    out = []
    cleaned = re.sub(r"[;\s]+", ",", spec)
    for part in cleaned.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            try:
                s = int(start)
                e = int(end)
            except ValueError:
                continue
            step = 1 if e >= s else -1
            for item in range(s, e + step, step):
                idx = item - 1
                if 0 <= idx < page_count:
                    out.append(idx)
        else:
            try:
                idx = int(part) - 1
            except ValueError:
                continue
            if 0 <= idx < page_count:
                out.append(idx)
    seen = set()
    unique = []
    for idx in out:
        if idx not in seen:
            seen.add(idx)
            unique.append(idx)
    return unique


def page_sizes(r) -> list[dict]:
    rows = []
    for idx, page in enumerate(r.pages):
        box = page.mediabox
        width = float(box.width)
        height = float(box.height)
        rows.append({
            "page": idx + 1,
            "width": round(width, 2),
            "height": round(height, 2),
            "rotation": int(page.get("/Rotate", 0) or 0),
        })
    return rows


def write_pages(source: Path, pages: list[int], out: Path, password: str = "") -> dict:
    r = reader(source, password=password)
    _, PdfWriter = require_pypdf()
    w = PdfWriter()
    for idx in pages:
        w.add_page(r.pages[idx])
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as fh:
        w.write(fh)
    return {"out": out.as_posix(), "pages": len(pages), "size_bytes": out.stat().st_size}


def default_out(path: Path, suffix: str) -> Path:
    return Path.cwd().resolve() / "_artifacts" / "pdf" / f"{path.stem}{suffix}"
