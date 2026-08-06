"""
FILE:       tools/llm_shared.py
ROLE:       THE one place a local model is called - client, probe, tier-bounded call, accounting.
DOMAIN:     tool (shared substrate)
DOES:       client/probe: acquire and health-check a local Ollama backend once, with a cached
            result and an honest error string. chat(): tier-bounded chat completion. embed():
            one embedding vector. record_*(): usage accounting into the state root, so local
            inference is visible and attributable instead of invisible spend.
DEPENDS ON: tools._toolkit (state_root); (optional external) ollama package + running service;
            (stdlib) atexit, json, os, threading, time
WIRES TO:   tools/embed_shared, tools/summarize_shared, tools/delegate/cli, tools/ollama_gov/cli.
NOTES:      D1-O1. Before this, FOUR modules each opened their own client with their own probe and
            degradation convention, and nothing recorded what local inference cost. Local models
            are the one capability that burns real resources AND can silently degrade, so they were
            the one capability with no chokepoint - the same class of hole as an index claiming a
            free lunch while re-embedding everything. There is now exactly ONE `import ollama` in
            the tree, and every call carries a `purpose` into the usage log.

            ACCOUNTING SHAPE: chat calls are logged one JSONL line each (they are few and
            individually expensive). Embeds are NOT - an index run makes thousands, and a
            per-embed line would be a flood nobody reads. They are counted in-process and flushed
            as a single rollup line at exit. The log is a governance record, so it has to stay
            readable to be worth writing.
"""
from __future__ import annotations

import atexit
import json
import os
import threading
import time

from tools._toolkit import state_root

# Operator hardware profiles (8GB VRAM / 32GB RAM). Agent automation should prefer the first.
TIERS = {
    "VRAM Only (Fastest)": {"ctx": 8192, "predict": 512},
    "Balanced (MoE)":      {"ctx": 16384, "predict": 1024},
    "Deep Logic (Slow)":   {"ctx": 32768, "predict": 2048},
    "Extreme (Risk)":      {"ctx": 65536, "predict": 4096},
}
DEFAULT_TIER = "VRAM Only (Fastest)"

USAGE_FILENAME = "llm_usage.jsonl"

# Probe cache keyed by (kind, model) - a chat model being up says nothing about an embed model.
_probes: dict[tuple[str, str], dict] = {}
_lock = threading.Lock()

# In-process embed rollup; flushed once at exit. See ACCOUNTING SHAPE above.
_embed_rollup: dict[str, dict] = {}


def disabled() -> bool:
    """Global kill-switch for ALL local inference. Per-family switches still apply on top."""
    return os.environ.get("SUITE_LLM_DISABLE") == "1"


def client():
    """The only `import ollama` in the toolkit. Returns (module, error-string-or-None)."""
    if disabled():
        return None, "local inference disabled via SUITE_LLM_DISABLE=1"
    try:
        import ollama
        return ollama, None
    except ImportError:
        return None, "ollama package not installed (pip install ollama)"


def usage_path():
    return state_root() / USAGE_FILENAME


def _write_usage(record: dict) -> None:
    """Best-effort append. Accounting must never be the reason a tool fails."""
    try:
        path = usage_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        record.setdefault("at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=True) + "\n")
    except Exception:
        pass


def record_embeds(model: str, count: int = 1, chars: int = 0) -> None:
    """Count an embed against the rollup. Cheap and lock-guarded; flushed at exit."""
    with _lock:
        row = _embed_rollup.setdefault(model, {"calls": 0, "chars": 0})
        row["calls"] += count
        row["chars"] += chars


def _flush_embed_rollup() -> None:
    with _lock:
        rows = {m: dict(v) for m, v in _embed_rollup.items()}
        _embed_rollup.clear()
    for model, row in rows.items():
        if row["calls"]:
            _write_usage({"kind": "embed", "purpose": "index", "model": model,
                          "calls": row["calls"], "chars": row["chars"]})


atexit.register(_flush_embed_rollup)


def probe(model: str, kind: str = "chat") -> dict:
    """Is this model usable right now? Cached per (kind, model).

    Returns {available, backend, error}. `backend` is a stable tag callers can store alongside
    data they derived from it - an embedding index MUST know which space it was built in.
    """
    if disabled():
        return {"available": False, "backend": None,
                "error": "local inference disabled via SUITE_LLM_DISABLE=1"}
    key = (kind, model)
    if key in _probes:
        return dict(_probes[key])
    mod, err = client()
    if mod is None:
        result = {"available": False, "backend": None, "error": err}
        _probes[key] = result
        return dict(result)
    try:
        if kind == "embed":
            resp = mod.embeddings(model=model, prompt="probe")
            vec = resp["embedding"] if isinstance(resp, dict) else resp.embedding
            result = {"available": True, "backend": f"ollama:{model}:{len(vec)}", "error": None}
        else:
            mod.chat(model=model, messages=[{"role": "user", "content": "ok"}],
                     options={"num_ctx": 2048, "num_predict": 1})
            result = {"available": True, "backend": f"ollama:{model}", "error": None}
    except Exception as e:  # service down, model missing - degrade, never crash
        result = {"available": False, "backend": None, "error": str(e)}
    _probes[key] = result
    return dict(result)


def reset_probe_cache() -> None:
    """Forget cached availability - used by tests that toggle the kill-switches mid-process."""
    _probes.clear()


def _tier_bounds(tier: str | None, num_ctx=None, num_predict=None) -> tuple[int, int, str]:
    name = tier if tier in TIERS else DEFAULT_TIER
    bounds = TIERS[name]
    return (int(num_ctx if num_ctx is not None else bounds["ctx"]),
            int(num_predict if num_predict is not None else bounds["predict"]),
            name)


def chat(model: str, prompt: str, *, purpose: str, tier: str | None = None,
         num_ctx=None, num_predict=None, temperature: float = 0.1) -> dict:
    """One tier-bounded chat call, accounted. Returns {ok, content, error, ...}.

    `purpose` is REQUIRED and lands in the usage log: an entry that cannot say which capability
    spent the tokens is not a governance record, it is noise.
    """
    ctx, predict, tier_name = _tier_bounds(tier, num_ctx, num_predict)
    mod, err = client()
    if mod is None:
        return {"ok": False, "content": "", "error": err, "model": model, "tier": tier_name,
                "num_ctx": ctx, "num_predict": predict}

    started = time.time()
    try:
        resp = mod.chat(model=model, messages=[{"role": "user", "content": prompt}],
                        options={"num_ctx": ctx, "num_predict": predict,
                                 "temperature": float(temperature)})
    except Exception as e:
        duration_ms = int((time.time() - started) * 1000)
        _write_usage({"kind": "chat", "purpose": purpose, "model": model, "tier": tier_name,
                      "num_ctx": ctx, "num_predict": predict, "duration_ms": duration_ms,
                      "ok": False, "error": str(e)})
        return {"ok": False, "content": "", "error": f"inference failed: {e}", "model": model,
                "tier": tier_name, "num_ctx": ctx, "num_predict": predict}

    duration_ms = int((time.time() - started) * 1000)
    if isinstance(resp, dict):
        content = resp.get("message", {}).get("content", "")
        prompt_tokens = resp.get("prompt_eval_count")
        out_tokens = resp.get("eval_count")
    else:
        content = getattr(getattr(resp, "message", None), "content", "")
        prompt_tokens = getattr(resp, "prompt_eval_count", None)
        out_tokens = getattr(resp, "eval_count", None)

    _write_usage({"kind": "chat", "purpose": purpose, "model": model, "tier": tier_name,
                  "num_ctx": ctx, "num_predict": predict, "duration_ms": duration_ms, "ok": True,
                  "prompt_tokens": prompt_tokens, "output_tokens": out_tokens})
    return {"ok": True, "content": str(content), "error": None, "model": model,
            "tier": tier_name, "num_ctx": ctx, "num_predict": predict,
            "duration_ms": duration_ms, "prompt_tokens": prompt_tokens,
            "output_tokens": out_tokens}


def embed(model: str, text: str) -> list | None:
    """One embedding vector, or None if unavailable. Counted into the embed rollup."""
    mod, err = client()
    if mod is None:
        return None
    try:
        resp = mod.embeddings(model=model, prompt=text or " ")
        vec = resp["embedding"] if isinstance(resp, dict) else resp.embedding
    except Exception:
        return None
    record_embeds(model, 1, len(text or ""))
    return vec


def list_models(search: str | None = None) -> dict:
    """Local model inventory. Returns {ok, models} or {ok:False, error}."""
    mod, err = client()
    if mod is None:
        return {"ok": False, "error": err}
    try:
        resp = mod.list()
    except Exception as e:
        return {"ok": False, "error": f"ollama not reachable: {e}"}
    raw = resp.get("models", []) if isinstance(resp, dict) else getattr(resp, "models", [])
    names = []
    for m in raw:
        if isinstance(m, dict):
            names.append(m.get("name") or m.get("model") or str(m))
        else:
            names.append(getattr(m, "model", None) or getattr(m, "name", None) or str(m))
    if search:
        names = [n for n in names if str(search).lower() in n.lower()]
    return {"ok": True, "models": names}
