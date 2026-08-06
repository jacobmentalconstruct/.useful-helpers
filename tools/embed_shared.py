"""
FILE:       tools/embed_shared.py
ROLE:       The one place text becomes a vector  -  real local embeddings, with a lexical fallback.
DOMAIN:     tool (shared substrate)
DES:        embed(text) -> (vector, backend). Uses a local Ollama embedding model when the service
            is reachable; falls back to a deterministic lexical hash-vector when it is not, so the
            toolkit still works fully offline. Caches in-process by text so re-embeds are free.
DEPENDS ON: tools.llm_shared (the one governed inference seam); (stdlib) hashlib, math, os, re
WIRES TO:   tools/bd_graph_shared (emit + query); the bd_* graph/RAG family.
NOTES:      Phase 6 Ga. Replaces the sha256 "vector"  -  the field report called that the single
            biggest lie in the system: retrieval was lexical wearing a vector costume. The BACKEND
            tag travels with every index so a query embeds in the SAME space (you cannot cosine an
            Ollama query vector against lexical-stub stored vectors). CAS upstream keys off content
            hash, so a re-index only embeds new/changed hunks.
"""
from __future__ import annotations

import hashlib
import math
import os
import re

from tools import llm_shared

WORD_RE = re.compile(r"[A-Za-z0-9_]+")

DEFAULT_MODEL = os.environ.get("SUITE_EMBED_MODEL", "nomic-embed-text")
LEXICAL_DIMS = 64
LEXICAL_BACKEND = f"lexical:{LEXICAL_DIMS}"

# In-process caches. Keyed by (backend, text); the vector is deterministic per key. Bounded so a
# very large index cannot grow it without limit  -  when full, drop the oldest half (FIFO).
_cache: dict[str, list[float]] = {}
_CACHE_MAX = 50_000
_probe: dict[str, object] = {"available": None, "backend": None, "error": None}


def _cache_put(key: str, vec: list[float]) -> None:
    if len(_cache) >= _CACHE_MAX:
        for old in list(_cache)[: _CACHE_MAX // 2]:
            del _cache[old]
    _cache[key] = vec


def _tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in WORD_RE.finditer(text)]


def lexical_vector(text: str, dims: int = LEXICAL_DIMS) -> list[float]:
    """Deterministic hash-bucket vector. NOT semantic  -  a paraphrase with no shared tokens scores
    near zero. It exists only so retrieval degrades to keyword search when Ollama is absent."""
    dims = max(4, min(int(dims), 256))
    vec = [0.0] * dims
    for token in _tokenize(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:2], "little") % dims
        vec[idx] += -1.0 if digest[2] % 2 else 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    return [round(v / norm, 6) for v in vec] if norm else vec


def probe(model: str = DEFAULT_MODEL) -> dict:
    """Is a real embedding backend usable right now? Cached after the first check.

    `SUITE_EMBED_DISABLE=1` forces the lexical backend (checked live, uncached)  -  used by the
    smoke suite so it stays fast and deterministic instead of depending on a running Ollama.
    Availability itself is answered by llm_shared (the one governed inference seam); this
    function only adds the lexical-fallback vocabulary that the rest of the bd_* family speaks.
    """
    if os.environ.get("SUITE_EMBED_DISABLE") == "1":
        return {"available": False, "backend": LEXICAL_BACKEND, "error": "disabled via env"}
    if _probe["available"] is not None:
        return dict(_probe)
    p = llm_shared.probe(model, kind="embed")
    if p["available"]:
        _probe.update(available=True, backend=p["backend"], error=None)
    else:  # service down, model missing, package absent  -  degrade, never crash
        _probe.update(available=False, backend=LEXICAL_BACKEND, error=p["error"])
    return dict(_probe)


def current_backend(model: str = DEFAULT_MODEL) -> str:
    return str(probe(model)["backend"])


def _embed_ollama(text: str, model: str) -> list[float] | None:
    return llm_shared.embed(model, text)


def embed(text: str, model: str = DEFAULT_MODEL) -> tuple[list[float], str]:
    """Return (vector, backend). Real embeddings when available, lexical otherwise. Cached."""
    text = text or " "
    p = probe(model)
    if p["available"]:
        key = f"{p['backend']}\x00{text}"
        if key in _cache:
            return _cache[key], str(p["backend"])
        vec = _embed_ollama(text, model)
        if vec is not None:
            _cache_put(key, vec)
            return vec, str(p["backend"])
        # a mid-run failure: fall through to lexical for this call
    key = f"{LEXICAL_BACKEND}\x00{text}"
    if key not in _cache:
        _cache_put(key, lexical_vector(text))
    return _cache[key], LEXICAL_BACKEND


def embed_in_backend(text: str, backend: str, model: str = DEFAULT_MODEL) -> tuple[list[float], str]:
    """Embed a query into a SPECIFIC backend's space  -  so a query matches how the index was built  -
    and report the backend actually used. If the index is `ollama:` but Ollama is now unreachable,
    we return a lexical vector AND say so (LEXICAL_BACKEND), so the caller can tell it degraded
    rather than silently comparing 64-dim lexical against 768-dim stored vectors as if semantic."""
    if os.environ.get("SUITE_EMBED_DISABLE") == "1":
        return lexical_vector(text or " "), LEXICAL_BACKEND
    if backend.startswith("ollama:"):
        parts = backend.split(":")  # "ollama:<model>:<dims>"
        idx_model = parts[1] if len(parts) > 1 else model
        vec = _embed_ollama(text or " ", idx_model)
        if vec is not None:
            return vec, backend
        return lexical_vector(text or " "), LEXICAL_BACKEND  # Ollama gone since indexing
    return lexical_vector(text or " "), LEXICAL_BACKEND
