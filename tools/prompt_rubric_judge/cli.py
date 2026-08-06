"""
FILE:       tools/prompt_rubric_judge/cli.py
ROLE:       Deterministic rubric judge.
DOMAIN:     tool
DOES:       Scores a supplied response against case checks, rubric checks, and constraints.
DEPENDS ON: tools._toolkit, tools.prompt_eval_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from Prompt Lab eval runs and review-judge diagnostics.
"""
from __future__ import annotations

from tools import prompt_eval_shared as pe
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    response = str(args.get("response") or "")
    if not response:
        return {"ok": False, "error": "response is required"}
    judged = pe.judge_response(response, case=args.get("case") or {},
                               rubric=args.get("rubric") or [],
                               constraints=args.get("constraints") or [])
    return {"tool": "prompt_rubric_judge", **judged}
