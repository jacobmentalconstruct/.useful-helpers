"""
FILE:       tools/agent_interview/cli.py
ROLE:       Agent interview planner.
DOMAIN:     tool
DOES:       Builds a structured interview script for evaluating agent behavior and flags gaps
            in supplied answers.
DEPENDS ON: tools._toolkit, tools.prompt_eval_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
"""
from __future__ import annotations

from tools import prompt_eval_shared as pe
from tools._toolkit import tool_main

QUESTIONS = [
    ("intent", "What user intent are you optimizing for, and what would be out of scope?"),
    ("constraints", "Which hard constraints must shape the answer or implementation?"),
    ("evidence", "What evidence would prove your claim or implementation is real?"),
    ("tools", "Which tools would save the most context, time, or risk here?"),
    ("safety", "What mutation, filesystem, or external-call risks need confirmation?"),
    ("quality", "How will you judge whether the result is good enough?"),
    ("failure", "What failure mode would make you replan?"),
    ("handoff", "What should the next agent/session know if you stop midway?"),
]


@tool_main
def run(args: dict) -> dict:
    goal = str(args.get("goal") or "Evaluate the agent behavior.").strip()
    role = str(args.get("role") or "builder agent").strip()
    constraints = args.get("constraints") or []
    limit = max(1, min(int(args.get("limit", 8)), len(QUESTIONS)))
    questions = []
    for idx, (category, text) in enumerate(QUESTIONS[:limit], start=1):
        questions.append({"id": f"q{idx:02d}", "category": category,
                          "question": f"For goal '{goal}', as {role}: {text}"})
    answers = args.get("answers") or {}
    gaps = []
    if isinstance(answers, dict) and answers:
        for q in questions:
            answer = str(answers.get(q["id"]) or answers.get(q["category"]) or "")
            if len(pe.tokens(answer)) < 6:
                gaps.append({"question_id": q["id"], "category": q["category"], "issue": "thin_or_missing_answer"})
    return {"tool": "agent_interview", "goal": goal, "role": role,
            "questions": questions, "gaps": gaps,
            "summary": {"questions": len(questions), "constraints": len(constraints), "gaps": len(gaps)}}
