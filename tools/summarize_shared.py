"""
FILE:       tools/summarize_shared.py
ROLE:       Turn gathered project signals into a short PURPOSE statement via a local model.
DOMAIN:     tool (shared substrate)
DOES:       summarize_project(signals) -> a 2-3 sentence purpose, using a small local Ollama chat
            model. Degrades to None when no model is reachable (or disabled), so `attach` simply
            omits the synopsis and stays structural  -  never blocks, never crashes.
DEPENDS ON: tools.llm_shared (the one governed inference seam); (stdlib) os
WIRES TO:   tools/attach (Gf: PROJECT_MAP synopsis).
NOTES:      Phase 6 Gf. One bounded chat call over cheap signals (README, docstrings, structure)
             -  NOT per-file summaries  -  so the front door stays responsive; `attach` caches the
            result in the workbench so re-engage never re-summarizes. Kill-switch
            SUITE_SUMMARY_DISABLE=1; model via SUITE_SUMMARY_MODEL.
"""
from __future__ import annotations

import os

from tools import llm_shared

DEFAULT_MODEL = os.environ.get("SUITE_SUMMARY_MODEL", "qwen2.5:3b")
_probe: dict[str, object] = {"available": None, "model": None, "error": None}

# Head/tail are concatenated around the raw signals  -  NEVER str.format/%, because signal text
# (READMEs, docstrings) routinely contains literal { } and % that would break templating and
# silently lose the synopsis.
# THE MODEL IS ALLOWED TO SAY IT CANNOT TELL.
#
# The first version of this prompt made an answer compulsory and then removed every way of
# declining to give one: "write 2-3 plain sentences stating what this project IS... No
# preamble, no bullet points, just the sentences." Handed a target with no subsystems, no
# entry points, no file types and no confident kind, the model returned "a database
# management system designed to store and manage customer information efficiently, with
# main parts including user authentication for secure access, data validation to ensure
# accuracy, and reporting tools for analytics."
#
# Read that output against the instruction and it is obedience, not malfunction: identity,
# purpose, main parts, in order, filled from the model's prior because the signals held
# nothing to fill them from. "Do not invent features not evidenced" was the only clause
# pointing the other way, and it is a request with no mechanism behind it - directly
# contradicted, in the same breath, by an instruction that requires prose.
#
# So there is now a legal way to refuse, stated before the demand rather than after it.
# The caller does not rely on this: `attach` refuses to make the call at all when the
# signals are thin, because a three-billion-parameter model obeying a negative instruction
# is exactly the thing that cannot be counted on. This is the second line of defence.
REFUSAL = "INSUFFICIENT EVIDENCE"
_PROMPT_HEAD = (
    "You are describing a software/data/records project to a new engineer who has not seen it. "
    f"If the signals below do not actually describe a project, reply with exactly {REFUSAL} "
    "and nothing else - that is a correct and expected answer, not a failure. Otherwise, "
    "using ONLY the signals below, write 2-3 plain sentences stating: what this project IS and "
    "its purpose, and its main parts. Be concrete and specific to these signals. Do not invent "
    "features not evidenced. No preamble, no bullet points, just the sentences or the refusal."
    "\n\nSIGNALS:\n")
_PROMPT_TAIL = "\n\nPURPOSE:"


def probe(model: str = DEFAULT_MODEL) -> dict:
    """Is a summary model usable now? Cached; SUITE_SUMMARY_DISABLE=1 forces unavailable (live)."""
    if os.environ.get("SUITE_SUMMARY_DISABLE") == "1":
        return {"available": False, "model": None, "error": "disabled via env"}
    if _probe["available"] is not None:
        return dict(_probe)
    p = llm_shared.probe(model, kind="chat")
    if p["available"]:
        _probe.update(available=True, model=model, error=None)
    else:  # service down / model missing / package absent  -  degrade
        _probe.update(available=False, model=None, error=p["error"])
    return dict(_probe)


def available(model: str = DEFAULT_MODEL) -> bool:
    return bool(probe(model)["available"])


def summarize_project(signals: str, model: str = DEFAULT_MODEL) -> str | None:
    """One bounded chat call -> a purpose statement, "" if the model declined on the
    evidence, or None if there was no usable answer at all."""
    if not available(model):
        return None
    result = llm_shared.chat(
        model, _PROMPT_HEAD + signals[:6000] + _PROMPT_TAIL,
        purpose="attach.synopsis", num_ctx=8192, num_predict=220, temperature=0.1)
    if not result["ok"]:
        return None
    text = " ".join(str(result["content"]).split()).strip()
    # A REFUSAL IS AN ANSWER, and it is a different answer from "could not ask". Returning
    # the refusal as prose would put the words INSUFFICIENT EVIDENCE into a field the
    # caller renders as a purpose; collapsing it to None would make a working backend that
    # correctly declined indistinguishable from one that was never reachable - and a gate
    # that cannot tell those apart records an untested feature as a passing one.
    #   None -> no usable answer (unreachable, error, empty)
    #   ""   -> asked, and the model declined on the evidence
    if not text:
        return None
    return "" if text.upper().startswith(REFUSAL) else text
