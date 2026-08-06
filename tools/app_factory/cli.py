"""
FILE:       tools/app_factory/cli.py
ROLE:       Stamp small starter app skeletons.
DOMAIN:     tool
DOES:       Lists templates, previews generated files, and writes confirmed starter apps.
DEPENDS ON: tools._toolkit, tools.packaging_more_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
"""
from __future__ import annotations

from tools import packaging_more_shared as pm
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        action = str(args.get("action") or "list_templates")
        if action == "list_templates":
            templates = [{"id": k, **v} for k, v in sorted(pm.APP_TEMPLATES.items())]
            return {"tool": "app_factory", "action": action, "templates": templates,
                    "summary": {"templates": len(templates)}}
        if action not in {"plan", "stamp"}:
            return {"ok": False, "error": f"unknown action: {action}"}
        template = str(args.get("template") or "headless_cli")
        name = str(args.get("name") or "Stamped App")
        dest = pm.workspace_path(str(args.get("destination") or f"_artifacts/app_factory/{pm.slug(name)}"))
        manifest, planned, files = pm.plan_app(dest, template, name)
        collisions = [p for p in planned if p["exists"]]
        if action == "plan" or bool(args.get("dry_run", action != "stamp")):
            return {"tool": "app_factory", "action": "plan", "template": template,
                    "destination": dest.as_posix(), "manifest": manifest, "planned_files": planned,
                    "collisions": collisions, "summary": {"files": len(planned), "collisions": len(collisions)}}
        if not args.get("confirm"):
            return {"ok": False, "error": "stamping an app requires confirm:true"}
        if collisions and not args.get("overwrite"):
            return {"ok": False, "error": "destination has collisions; pass overwrite:true to replace",
                    "collisions": collisions}
        dest.mkdir(parents=True, exist_ok=True)
        written = pm.write_outputs(dest, files, overwrite=bool(args.get("overwrite", False)))
        return {"tool": "app_factory", "action": "stamp", "template": template,
                "destination": dest.as_posix(), "manifest": manifest, "written": written,
                "summary": {"files": len(written), "collisions": len(collisions)}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
