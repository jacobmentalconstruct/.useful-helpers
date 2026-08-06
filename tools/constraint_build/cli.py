"""
FILE:       tools/constraint_build/cli.py
ROLE:       Constraint extractor.
DOMAIN:     tool
DOES:       Extracts stable constraint statements from text or workspace-local docs.
DEPENDS ON: tools._toolkit, tools.prompt_eval_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Deterministic constraint extraction for eval inputs.
"""
from __future__ import annotations

from tools import prompt_eval_shared as pe
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        out = pe.build_constraints(args)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    return {"tool": "constraint_build", **out}
