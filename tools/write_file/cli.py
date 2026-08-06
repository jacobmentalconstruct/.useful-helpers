"""
FILE:       tools/write_file/cli.py
ROLE:       Create or overwrite a file through the governed seam (the sidecar's `Write`).
DOMAIN:     tool
DOES:       Preview-first: report what would be written (path, bytes, exists, overwrite). On
            write:true (or apply:true) it creates parent dirs and writes the content. Refuses
            paths outside the work target / toolkit home.
DEPENDS ON: tools._toolkit, (stdlib) pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Declares writes:target so writing into the work target is the SANCTIONED, audited
            path  -  not a Bash end-run around the precept. Preview-first; refuses to clobber an
            existing file unless overwrite is left on (default true)  -  pass overwrite:false to
            create-only.
"""
from __future__ import annotations

from tools._toolkit import apply_with, confirmed, resolve_within_roots, tool_main


@tool_main
def run(args: dict) -> dict:
    if "content" not in args:
        return {"ok": False, "error": "content is required"}
    path, err = resolve_within_roots(args.get("path", ""))
    if err:
        return {"ok": False, "error": err}
    content = str(args["content"])
    exists = path.is_file()
    overwrite = bool(args.get("overwrite", True))

    # Checked BEFORE the plan so a preview reports the refusal too, not just the apply.
    if path.exists() and path.is_dir():
        return {"ok": False, "error": f"path is a directory: {path}"}
    if exists and not overwrite:
        return {"ok": False, "error": f"file exists and overwrite is false: {path}"}

    plan = {
        "tool": "write_file",
        "path": path.as_posix(),
        "bytes": len(content.encode("utf-8")),
        "exists": exists,
        "would_overwrite": exists,
    }
    if not confirmed(args, legacy=("write", "confirm")):
        return {**plan, "dry_run": True, "written": False, "apply_with": apply_with()}

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {**plan, "dry_run": False, "written": True}
