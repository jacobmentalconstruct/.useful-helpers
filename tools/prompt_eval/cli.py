"""
FILE:       tools/prompt_eval/cli.py
ROLE:       Prompt evaluation aggregator.
DOMAIN:     tool
DOES:       Scores supplied responses across benchmark/training cases and aggregates results.
DEPENDS ON: tools._toolkit, tools.prompt_eval_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from Prompt Lab EvalRun records.
"""
from __future__ import annotations

from tools import prompt_eval_shared as pe
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    if args.get("cases"):
        cases = list(args["cases"])
    else:
        try:
            suite = pe.load_suite(args)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        cases = pe.suite_cases(suite, str(args.get("suite_name") or "default"), int(args.get("limit", 50)))
    responses = args.get("responses") or {}
    if args.get("response") and cases:
        responses = {cases[0].get("id", "case-001"): str(args["response"])}
    if not isinstance(responses, dict):
        return {"ok": False, "error": "responses must be an object keyed by case id"}
    result = pe.aggregate_eval(cases, responses, constraints=args.get("constraints") or [])
    return {"tool": "prompt_eval", "cases": cases, **result}
