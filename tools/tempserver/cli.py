"""
FILE:       tools/tempserver/cli.py
ROLE:       Build a self-contained temporary static project viewer.
DOMAIN:     tool
DOES:       Creates an HTML file with embedded file metadata/content and returns a serve command.
DEPENDS ON: tools._toolkit, tools.packaging_more_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from TempServerMAKER, without unmanaged background server lifecycle.
"""
from __future__ import annotations

from tools import packaging_more_shared as pm
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        root = pm.workspace_path(str(args.get("root") or "."), must_exist=True)
        meta, records = pm.build_records(root, max_bytes=int(args.get("max_bytes", 12000)),
                                         include_binaries=False,
                                         include=args.get("include") or ["*"],
                                         exclude=args.get("exclude") or [],
                                         limit=int(args.get("limit", 300)))
        html = pm.viewer_html(meta, records)
        dry_run = bool(args.get("dry_run", True))
        name = pm.slug(str(args.get("name") or root.name or "viewer"))
        out_dir = pm.workspace_path(str(args.get("out_dir") or f"_artifacts/tempserver/{name}"))
        written = []
        if not dry_run:
            if not args.get("confirm"):
                return {"ok": False, "error": "writing tempserver viewer requires confirm:true"}
            written = pm.write_outputs(out_dir, {"index.html": html}, overwrite=bool(args.get("overwrite", False)))
        port = int(args.get("port", 8765))
        return {"tool": "tempserver", "root": root.as_posix(), "dry_run": dry_run,
                "out_dir": out_dir.as_posix(), "written": written,
                "serve_command": f"python -m http.server {port} -d {out_dir.as_posix()}",
                "url": f"http://127.0.0.1:{port}/index.html",
                "summary": meta}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
