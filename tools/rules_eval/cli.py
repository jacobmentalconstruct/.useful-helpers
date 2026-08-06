"""
FILE:       tools/rules_eval/cli.py
ROLE:       Evaluate content/path against local safety rules.
DOMAIN:     tool
DOES:       Checks protected paths, content size, and forbidden patterns.
DEPENDS ON: tools._toolkit, tools.memory_workflow_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      REHOME (rewritten) from _theCELL RulesEngineMS.
"""
from __future__ import annotations

from tools import memory_workflow_shared as mw
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        content = str(args.get("content") or "")
        path = str(args.get("path") or "")
        if path and not content and args.get("read"):
            p = mw.workspace_path(path, must_exist=True)
            if p.is_file():
                content = p.read_text(encoding="utf-8", errors="replace")
        result = mw.evaluate_rules(path=path, content=content, rules=args.get("rules") or {})
        return {"tool": "rules_eval", **result,
                "summary": {"allowed": result["allowed"], "violations": len(result["violations"])}}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
