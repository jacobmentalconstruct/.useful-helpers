"""
FILE:       tools/workflow_templates/cli.py
ROLE:       List, show, or render built-in workflow templates.
DOMAIN:     tool
DOES:       Exposes suite-native workflow templates derived from _theCELL workflow JSON patterns.
DEPENDS ON: tools._toolkit, tools.memory_workflow_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from _theCELL/_workflows templates.
"""
from __future__ import annotations

from tools import memory_workflow_shared as mw
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    action = str(args.get("action") or "list")
    try:
        if action == "list":
            templates = [{"id": k, "label": v["label"], "description": v["description"],
                          "steps": len(v.get("steps", []))}
                         for k, v in sorted(mw.BUILTIN_TEMPLATES.items())]
            return {"tool": "workflow_templates", "action": action, "templates": templates,
                    "summary": {"templates": len(templates)}}
        template = mw.load_template(str(args.get("id") or args.get("template") or "code_review"),
                                    str(args.get("path") or ""))
        if action == "render":
            variables = args.get("variables") or {}
            rendered = str(template)
            for key, value in variables.items():
                rendered = rendered.replace("{{" + str(key) + "}}", str(value))
            return {"tool": "workflow_templates", "action": action, "template": template,
                    "rendered": rendered}
        return {"tool": "workflow_templates", "action": "show", "template": template,
                "summary": {"steps": len(template.get("steps", [])),
                            "fingerprint": mw.fingerprint(template)}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
