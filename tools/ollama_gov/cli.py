"""
FILE:       tools/ollama_gov/cli.py
ROLE:       Hardware-aware Ollama governor  -  list models and run token-governed local inference.
DOMAIN:     tool
DOES:       action=tiers: return the ctx/predict safety tiers (pure data, always works).
            action=models: list local Ollama models (optional `search` filter).
            action=run: governed chat (num_ctx/num_predict from a tier). Degrades gracefully
            when the `ollama` package or service is unavailable.
DEPENDS ON: tools._toolkit, tools.llm_shared (the one governed inference seam); (stdlib) json
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Sandbox authority)
NOTES:      The larger tiers are the operator's hardware profiles.
"""
from __future__ import annotations

import json

from tools import llm_shared
from tools._toolkit import tool_main

# Operator hardware profiles (8GB VRAM / 32GB RAM). Agent automation should prefer the first.
# Sourced from llm_shared so the tiers this tool ADVERTISES are literally the ones every other
# caller is BOUND BY - a governor that publishes different numbers than it enforces governs nothing.
TIERS = llm_shared.TIERS


def _usage_report(args: dict) -> dict:
    """Read back the accounting log. Accounting nobody can READ is not governance, so the
    governor is where you ask what local inference has actually cost."""
    path = llm_shared.usage_path()
    if not path.exists():
        return {"tool": "ollama_gov", "action": "usage", "calls": 0, "by_purpose": {},
                "note": "no local inference recorded yet"}
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:  # a torn last line - report the rest rather than failing the read
            continue
    by_purpose: dict[str, dict] = {}
    for row in rows:
        bucket = by_purpose.setdefault(str(row.get("purpose", "unknown")),
                                       {"calls": 0, "duration_ms": 0, "output_tokens": 0})
        bucket["calls"] += int(row.get("calls") or 1)
        bucket["duration_ms"] += int(row.get("duration_ms") or 0)
        bucket["output_tokens"] += int(row.get("output_tokens") or 0)
    limit = int(args.get("limit", 20))
    return {"tool": "ollama_gov", "action": "usage", "log": str(path), "calls": len(rows),
            "by_purpose": by_purpose, "recent": rows[-limit:] if limit > 0 else []}


@tool_main
def run(args: dict) -> dict:
    action = str(args.get("action", "tiers")).lower()

    if action == "tiers":
        return {"tool": "ollama_gov", "action": "tiers", "tiers": TIERS,
                "agent_budget": {"max_params": "~4B", "max_tokens": "~4k", "recommend_tier": "VRAM Only (Fastest)"}}

    if action == "models":
        listed = llm_shared.list_models(args.get("search"))
        if not listed["ok"]:
            return {"ok": False, "error": listed["error"]}
        models = listed["models"]
        return {"tool": "ollama_gov", "action": "models", "count": len(models), "models": models}

    if action == "run":
        model = args.get("model")
        prompt = args.get("prompt")
        if not model or not prompt:
            return {"ok": False, "error": "'model' and 'prompt' are required for run"}
        result = llm_shared.chat(
            model, prompt, purpose="ollama_gov.run", tier=args.get("tier"),
            num_ctx=args.get("num_ctx"), num_predict=args.get("num_predict"),
            temperature=float(args.get("temperature", 0.7)))
        if not result["ok"]:
            return {"ok": False, "error": result["error"]}
        return {"tool": "ollama_gov", "action": "run", "model": model, "tier": result["tier"],
                "num_ctx": result["num_ctx"], "num_predict": result["num_predict"],
                "duration_ms": result["duration_ms"],
                "prompt_tokens": result["prompt_tokens"],
                "output_tokens": result["output_tokens"],
                "response": result["content"]}

    if action == "usage":
        return _usage_report(args)

    return {"ok": False, "error": f"unknown action {action!r}; use tiers|models|run|usage"}
