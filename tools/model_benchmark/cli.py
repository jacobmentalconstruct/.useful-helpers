"""
FILE:       tools/model_benchmark/cli.py
ROLE:       Benchmark suite planner/evaluator.
DOMAIN:     tool
DOES:       Loads benchmark cases and either emits a run plan or evaluates supplied responses.
DEPENDS ON: tools._toolkit, tools.prompt_eval_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
"""
from __future__ import annotations

from tools import prompt_eval_shared as pe
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        suite = pe.load_suite(args)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    suite_name = str(args.get("suite_name") or "default")
    cases = pe.suite_cases(suite, suite_name, int(args.get("limit", 50)))
    responses = args.get("responses") or {}
    if responses:
        result = pe.aggregate_eval(cases, responses, constraints=args.get("constraints") or [])
        return {"tool": "model_benchmark", "suite_name": suite_name, "mode": "evaluate",
                "cases": cases, **result}
    plan = [{"case_id": c.get("id"), "label": c.get("label"), "probe_type": c.get("probe_type"),
             "prompt": c.get("prompt")} for c in cases]
    return {"tool": "model_benchmark", "suite_name": suite_name, "mode": "plan",
            "run_plan": plan, "summary": {"cases": len(cases), "needs_responses": True}}
