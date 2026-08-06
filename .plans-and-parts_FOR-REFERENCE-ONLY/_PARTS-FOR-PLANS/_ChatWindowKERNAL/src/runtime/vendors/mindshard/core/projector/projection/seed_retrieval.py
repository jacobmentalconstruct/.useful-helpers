"""
manifold_kernel.projection.seed_retrieval — Seed artifact selection.

Given a query, select the initial set of seed artifacts from the store.
Seeds are chosen by:
  1. Token-level text match (individual query words against verbatim text)
  2. Semantic similarity (when a semantic backend is available)
  3. Phrase-level exact match (full query substring — highest precision)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..config import KernelConfig
from ..errors import SeedRetrievalError
from ..storage.sqlite_store import SQLiteStore
from ..ingest.semantic_adapter import SemanticAdapter, blob_to_vector
from ..types import ArtifactRecord

logger = logging.getLogger(__name__)


@dataclass
class SeedCandidate:
    """A candidate seed with its relevance score and origin."""
    artifact_id: str
    score: float
    source: str  # "exact", "token", "semantic"


# Stopwords to skip during token matching
_STOPWORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "and", "or", "but", "if", "then", "else", "when", "where", "how",
    "what", "which", "who", "whom", "this", "that", "these", "those",
    "it", "its", "of", "in", "to", "for", "with", "on", "at", "from",
    "by", "about", "as", "into", "through", "during", "before", "after",
    "above", "below", "between", "out", "off", "over", "under", "again",
    "further", "once", "here", "there", "all", "each", "every", "both",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very",
})


def _tokenize_query(query: str) -> List[str]:
    """Extract meaningful tokens from a query string."""
    tokens = re.findall(r"[a-z0-9_]+", query.lower())
    return [t for t in tokens if len(t) >= 3 and t not in _STOPWORDS]


def retrieve_seeds(
    query: str,
    store: SQLiteStore,
    semantic_adapter: SemanticAdapter,
    config: KernelConfig,
    max_seeds: Optional[int] = None,
) -> List[SeedCandidate]:
    """
    Select seed artifacts for a query.

    Combines token-level text matching, phrase-level exact match,
    and semantic similarity ranking, bounded by max_seeds.
    """
    max_seeds = max_seeds or config.projection.default_max_seeds
    candidates: Dict[str, SeedCandidate] = {}

    # 1. Token-level search (broad recall)
    token_matches = _token_search(query, store, max_seeds * 3)
    for art_id, score in token_matches:
        if art_id not in candidates:
            candidates[art_id] = SeedCandidate(artifact_id=art_id, score=score, source="token")
        else:
            candidates[art_id].score = max(candidates[art_id].score, score)

    # 2. Phrase-level exact search (boost if full query appears)
    phrase_matches = _phrase_search(query, store, max_seeds)
    for art_id, score in phrase_matches:
        if art_id not in candidates:
            candidates[art_id] = SeedCandidate(artifact_id=art_id, score=score, source="exact")
        else:
            # Boost existing score — exact phrase match is strong signal
            candidates[art_id].score = min(1.0, candidates[art_id].score + score * 0.3)
            candidates[art_id].source = "exact"

    # 3. Semantic similarity search
    if len(candidates) < max_seeds:
        remaining = max_seeds - len(candidates)
        sem_matches = _semantic_search(query, store, semantic_adapter, remaining * 2)
        for art_id, score in sem_matches:
            if art_id not in candidates:
                candidates[art_id] = SeedCandidate(artifact_id=art_id, score=score, source="semantic")

    # Sort by score descending and return top seeds
    result = sorted(candidates.values(), key=lambda c: c.score, reverse=True)
    return result[:max_seeds]


def _token_search(
    query: str,
    store: SQLiteStore,
    limit: int,
) -> List[Tuple[str, float]]:
    """Search verbatim records for individual query token matches.

    Scores each artifact by the fraction of query tokens it contains,
    weighted by inverse document frequency approximation.
    """
    tokens = _tokenize_query(query)
    if not tokens:
        return []

    # For each token, find matching artifacts
    token_hits: Dict[str, Dict[str, bool]] = {}  # art_id → {token: True}

    for token in tokens:
        rows = store.conn.execute(
            "SELECT artifact_id FROM verbatim "
            "WHERE LOWER(normalized_text) LIKE ? LIMIT ?",
            (f"%{token}%", limit * 2),
        ).fetchall()
        for row in rows:
            art_id = row["artifact_id"]
            if art_id not in token_hits:
                token_hits[art_id] = {}
            token_hits[art_id][token] = True

    # Score by fraction of query tokens matched
    results = []
    for art_id, matched_tokens in token_hits.items():
        coverage = len(matched_tokens) / len(tokens)
        # Bonus for matching more tokens
        score = coverage * 0.8 + (0.2 if coverage > 0.5 else 0.0)
        results.append((art_id, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]


def _phrase_search(
    query: str,
    store: SQLiteStore,
    limit: int,
) -> List[Tuple[str, float]]:
    """Search verbatim records for full phrase substring matches."""
    query_lower = query.lower().strip()
    if not query_lower or len(query_lower) < 5:
        return []

    rows = store.conn.execute(
        "SELECT artifact_id, normalized_text FROM verbatim "
        "WHERE LOWER(normalized_text) LIKE ? LIMIT ?",
        (f"%{query_lower}%", limit * 3),
    ).fetchall()

    results = []
    for row in rows:
        text = row["normalized_text"].lower()
        if query_lower in text:
            ratio = len(query_lower) / max(len(text), 1)
            score = min(1.0, 0.5 + ratio * 0.5)
            results.append((row["artifact_id"], score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]


def _semantic_search(
    query: str,
    store: SQLiteStore,
    semantic_adapter: SemanticAdapter,
    limit: int,
) -> List[Tuple[str, float]]:
    """Rank artifacts by semantic similarity to the query."""
    if semantic_adapter.backend_name == "none":
        return []

    try:
        query_result = semantic_adapter.embed(query)
        if not query_result.vector:
            return []
    except Exception:
        return []

    query_vec = query_result.vector
    records = store.list_semantic_by_backend(semantic_adapter.backend_name)

    scored = []
    for rec in records:
        vec = blob_to_vector(rec.feature_blob)
        if not vec:
            continue
        sim = semantic_adapter.similarity(query_vec, vec)
        scored.append((rec.artifact_id, sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]
