"""
FILE:       tools/prompt_diff_report/cli.py
ROLE:       Prompt variant differ.
DOMAIN:     tool
DOES:       Compares baseline and candidate prompts/responses and reports changed terms and risks.
DEPENDS ON: tools._toolkit, tools.prompt_eval_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from Prompt Lab package/promotion delta summaries.
"""
from __future__ import annotations

from tools import prompt_eval_shared as pe
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        baseline, _ = pe.read_text_arg({"text": args.get("baseline"), "path": args.get("baseline_path")})
        candidate, _ = pe.read_text_arg({"text": args.get("candidate"), "path": args.get("candidate_path")})
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    if not baseline and not candidate:
        return {"ok": False, "error": "baseline/candidate text or paths are required"}
    report = pe.diff_report(baseline, candidate,
                            required_terms=args.get("required_terms") or [],
                            forbidden_terms=args.get("forbidden_terms") or [])
    return {"tool": "prompt_diff_report", **report}
