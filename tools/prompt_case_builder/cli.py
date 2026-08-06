"""
FILE:       tools/prompt_case_builder/cli.py
ROLE:       Prompt evaluation case builder.
DOMAIN:     tool
DOES:       Builds deterministic benchmark/training case JSON from a scenario and constraints.
DEPENDS ON: tools._toolkit, tools.prompt_eval_shared, (stdlib) json
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from Prompt Lab TrainingCase/TrainingSuite records.
"""
from __future__ import annotations

import json

from tools import prompt_eval_shared as pe
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    prompt = str(args.get("prompt") or args.get("scenario") or "").strip()
    if not prompt:
        return {"ok": False, "error": "prompt or scenario is required"}
    constraints = args.get("constraints") or []
    case = pe.make_case(str(args.get("id") or "case-001"), str(args.get("label") or "Generated Case"),
                        prompt, constraints=constraints,
                        probe_type=str(args.get("probe_type") or "direct_model_probe"))
    suite = {"id": str(args.get("suite_id") or "generated"), "name": str(args.get("suite_name") or "Generated Suite"),
             "cases": [case]}
    written = False
    if args.get("write"):
        out = pe.workspace_path(str(args.get("out") or "_artifacts/prompt_eval/generated_case.json"))
        if out.exists() and not args.get("overwrite"):
            return {"ok": False, "error": f"out exists; use overwrite:true: {out}"}
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(suite, indent=2), encoding="utf-8")
        written = True
    return {"tool": "prompt_case_builder", "case": case, "suite": suite,
            "written": written, "summary": {"cases": 1, "checks": len(case["deterministic_checks"])}}
