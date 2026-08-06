"""
FILE:       tools/delegate/cli.py
ROLE:       Hand a bounded task to a LOCAL model that uses the sidecar's own hands (the payoff).
DOMAIN:     tool
DOES:       Runs a bounded tool-use loop: a local Ollama model is given the task plus an allowlist
            of the sidecar's Observe verbs, emits one tool call at a time as JSON, and each call is
            executed THROUGH THE GOVERNED SEAM (so every step is audit-logged like any other).
            Returns the distilled answer plus the full trail, optionally grounded as evidence.
DEPENDS ON: tools._toolkit (seam_call), tools.llm_shared (the one governed inference seam); (stdlib) json, os
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Apply authority)
            correlate  -  so the expensive agent spends its budget on judgement, not fetching)
NOTES:      Bounded by construction: max_steps, a per-call timeout, and an ALLOWLIST that is
            Observe-only by default (a small local model must not hold write/exec verbs) and can
            never include `delegate` itself. Degrades honestly when no model is reachable.
"""
from __future__ import annotations

import json
import os

from tools import llm_shared
from tools._toolkit import (
    apply_with,
    attach_evidence,
    confirmed,
    first_json_object,
    project_root,
    seam_call,
    suite_home,
    tool_main,
)

# Measured, not assumed: on the "which file defines X" probe, qwen2.5-coder:7b confidently
# answered "no file defines it" against an observation that plainly showed the match, while
# qwen2.5:7b (the general model) answered correctly in ~6s. A fast wrong answer is worse than
# none, so the default is the one that reads observations correctly. Override per call or via env.
DEFAULT_MODEL = os.environ.get("SUITE_DELEGATE_MODEL", "qwen2.5:7b")
# Read-only verbs a local model can safely drive. Widen deliberately via `allow`.
DEFAULT_ALLOW = ["repo_search", "glob", "read_file", "file_tree", "diff"]
_MAX_STEPS = 12
_OBS_CAP = 1500
_STEP_TIMEOUT = 120

_PROMPT_HEAD = (
    "You are a research assistant working inside a codebase. Answer the TASK by calling tools.\n"
    "Reply with EXACTLY ONE json object and nothing else, either:\n"
    '  {"tool": "<name>", "args": {...}}   to call a tool\n'
    '  {"answer": "<your final answer>"}   when you can answer\n\n'
    "Rules:\n"
    "- Ground every answer in the OBSERVATION text. Read it literally.\n"
    "- If an OBSERVATION already contains the answer, answer immediately.\n"
    "- Never say something is absent when an OBSERVATION shows it present.\n\n"
    "TOOLS:\n")


def _tool_menu(allow: list[str]) -> str:
    menu = {
        "repo_search": '{"tool":"repo_search","args":{"query":"<text>","root":"."}}  search file contents',
        "glob": '{"tool":"glob","args":{"pattern":"**/*.py"}}  list files matching a pattern',
        "read_file": '{"tool":"read_file","args":{"path":"<path>","limit":80}}  read a file',
        "file_tree": '{"tool":"file_tree","args":{"root":"."}}  list the tree',
        "diff": '{"tool":"diff","args":{"a":"<path>","b":"<path>"}}  compare two files',
    }
    return "\n".join(f"- {menu.get(t, t)}" for t in allow)




def _authority_of(tool_id: str) -> str:
    """A tool's declared authority, straight from its manifest. Unknown tools read as elevated so
    an unrecognised name can never slip past the Observe-only default."""
    try:
        manifest = suite_home() / "tools" / tool_id / "tool.json"
        if not manifest.is_file():
            manifest = suite_home() / "apps" / tool_id / "tool.json"
        if not manifest.is_file():
            return "unknown"
        return str(json.loads(manifest.read_text(encoding="utf-8")).get("authority") or "unknown")
    except (OSError, json.JSONDecodeError):
        return "unknown"


def _call_through_seam(tool: str, args: dict) -> dict:
    """Execute one delegated tool call via the governed seam, so it is audit-logged."""
    return seam_call(tool, args, timeout=_STEP_TIMEOUT)


@tool_main
def run(args: dict) -> dict:
    task = str(args.get("task") or "").strip()
    if not task:
        return {"ok": False, "error": "task is required"}
    model = str(args.get("model") or DEFAULT_MODEL)
    max_steps = max(1, min(int(args.get("max_steps", 6)), _MAX_STEPS))
    allow = [t for t in (args.get("allow") or DEFAULT_ALLOW) if t != "delegate"]  # never itself
    if not allow:
        return {"ok": False, "error": "allow list is empty"}
    # A small local model must not silently receive write/exec authority. Anything above Observe
    # requires a deliberate allow_apply:true from the CALLER, who owns that risk.
    if not bool(args.get("allow_apply")):
        elevated = sorted(t for t in allow if _authority_of(t) != "Observe")
        if elevated:
            return {"ok": False, "error": (
                f"refusing to delegate non-Observe tools {elevated} to a local model; "
                f"pass allow_apply:true to accept that risk deliberately"),
                "elevated": elevated}

    plan = {"tool": "delegate", "task": task, "model": model,
            "allow": allow, "max_steps": max_steps, "target": project_root().as_posix()}
    if not confirmed(args):
        return {**plan, "dry_run": True, "ran": False, "apply_with": apply_with()}

    _mod, client_err = llm_shared.client()
    if client_err:
        return {**plan, "ok": False, "ran": False,
                "error": f"{client_err}; cannot delegate",
                "configure": "pip install ollama, and run a local model"}

    transcript = _PROMPT_HEAD + _tool_menu(allow) + f"\n\nTASK: {task}\n"
    steps: list[dict] = []
    answer = None
    for _ in range(max_steps):
        # Every turn is accounted separately: a delegation that burned twelve steps and a
        # delegation that answered in one must not look the same in the usage log.
        turn = llm_shared.chat(model, transcript, purpose="delegate.step",
                               num_ctx=8192, num_predict=300, temperature=0.1)
        if not turn["ok"]:  # service down / model missing  -  degrade, never crash
            return {**plan, "ok": False, "ran": False, "steps": steps,
                    "error": f"model call failed: {str(turn['error'])[:200]}"}
        reply = turn["content"] or ""

        move = first_json_object(reply)
        if move is None:
            steps.append({"note": "unparseable model reply", "reply": reply[:200]})
            transcript += "\nYour reply was not valid JSON. Reply with ONE json object.\n"
            continue
        if "answer" in move:
            answer = str(move["answer"])
            break
        tool = str(move.get("tool") or "")
        if tool not in allow:
            steps.append({"tool": tool, "ok": False, "error": "tool not in allowlist"})
            transcript += f"\nOBSERVATION: '{tool}' is not available. Choose from: {allow}\n"
            continue
        targs = move.get("args") if isinstance(move.get("args"), dict) else {}
        result = _call_through_seam(tool, targs)
        obs = json.dumps(result.get("output") if result["ok"] else result.get("error"),
                         ensure_ascii=False)[:_OBS_CAP]
        steps.append({"tool": tool, "args": targs, "ok": result["ok"],
                      "observation": obs[:400]})
        transcript += f"\n{json.dumps(move)}\nOBSERVATION: {obs}\n"

    out = {**plan, "dry_run": False, "ran": True, "complete": answer is not None,
           "answer": answer, "used_steps": len(steps), "steps": steps,
           "ok": answer is not None}
    if not out["ok"]:
        out["error"] = f"no answer within {max_steps} steps (the trail is in `steps`)"
    if args.get("evidence"):
        out["evidence_id"] = attach_evidence(
            f"delegate: {task[:80]}", json.dumps({"answer": answer, "steps": steps},
                                                 ensure_ascii=False))
    return out
