"""
FILE:       tools/workflow_decompose/cli.py
ROLE:       Decompose goals, text, or templates into ordered workflow steps.
DOMAIN:     tool
DOES:       Produces deterministic task records and a playbook-style skeleton.
DEPENDS ON: tools._toolkit, tools.memory_workflow_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from _theCELL recursive workflow/task queue behavior.
"""
from __future__ import annotations

from tools import memory_workflow_shared as mw
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        goal = str(args.get("goal") or "")
        text, sources = mw.read_text_sources(args) if (args.get("text") is not None or args.get("path") or args.get("paths")) else ("", [])
        template = None
        if args.get("template") or args.get("template_path"):
            template = mw.load_template(str(args.get("template") or ""), str(args.get("template_path") or ""))
        steps = mw.decompose(goal, text=text, template=template, max_steps=int(args.get("max_steps", 8)))
        playbook = [{"id": s["id"], "tool": "prompt_eval", "args": {"response": "", "suite_name": s["title"]}}
                    for s in steps]
        return {"tool": "workflow_decompose", "goal": goal, "sources": sources, "steps": steps,
                "playbook_skeleton": playbook,
                "summary": {"steps": len(steps), "fingerprint": mw.fingerprint(steps)}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
