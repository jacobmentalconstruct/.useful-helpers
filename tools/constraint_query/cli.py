"""
FILE:       tools/constraint_query/cli.py
ROLE:       Constraint query/filter tool.
DOMAIN:     tool
DOES:       Filters extracted constraints by query terms, tags, and severity.
DEPENDS ON: tools._toolkit, tools.prompt_eval_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Read-only constraint search surface.
"""
from __future__ import annotations

from tools import prompt_eval_shared as pe
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    constraints = args.get("constraints")
    if constraints is None:
        try:
            constraints = pe.build_constraints(args)["constraints"]
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
    if not isinstance(constraints, list):
        return {"ok": False, "error": "constraints must be an array"}
    matches = pe.query_constraints(constraints, query=str(args.get("query") or ""),
                                   tags=args.get("tags") or [],
                                   severity=str(args.get("severity") or ""),
                                   limit=int(args.get("limit", 50)))
    return {"tool": "constraint_query", "matches": matches,
            "summary": {"constraints": len(constraints), "matches": len(matches)}}
