"""
FILE:       tools/codebase_bundle/cli.py
ROLE:       Build AI-friendly codebase bundle artifacts.
DOMAIN:     tool
DOES:       Produces AI report text, codebase JSONL, and Python AST JSONL from workspace files.
DEPENDS ON: tools._toolkit, tools.packaging_more_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from TempServerMAKER export surfaces.
"""
from __future__ import annotations

from tools import packaging_more_shared as pm
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        root = pm.workspace_path(str(args.get("root") or "."), must_exist=True)
        if not root.is_dir():
            return {"ok": False, "error": "root must be a directory"}
        meta, records = pm.build_records(root, max_bytes=int(args.get("max_bytes", 20000)),
                                         include_binaries=bool(args.get("include_binaries", False)),
                                         include=args.get("include") or ["*"],
                                         exclude=args.get("exclude") or [],
                                         limit=int(args.get("limit", 500)))
        formats = args.get("formats") or ["report", "jsonl", "ast"]
        outputs = {}
        if "report" in formats:
            outputs["codebase_report.md"] = pm.ai_report(meta, records)
        if "jsonl" in formats:
            outputs["codebase.jsonl"] = pm.jsonl_bundle(meta, records)
        if "ast" in formats:
            outputs["ast.jsonl"] = pm.ast_jsonl(root, records)
        dry_run = bool(args.get("dry_run", True))
        written = []
        out_dir = pm.workspace_path(str(args.get("out_dir") or "_artifacts/codebase_bundles/bundle"))
        if not dry_run:
            if not args.get("confirm"):
                return {"ok": False, "error": "writing bundles requires confirm:true"}
            written = pm.write_outputs(out_dir, outputs, overwrite=bool(args.get("overwrite", False)))
        return {"tool": "codebase_bundle", "root": root.as_posix(), "dry_run": dry_run,
                "out_dir": out_dir.as_posix(), "outputs": [{"name": k, "bytes": len(v.encode("utf-8"))}
                                                           for k, v in outputs.items()],
                "written": written, "summary": meta}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
