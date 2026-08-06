"""retrieval.py — Cold Artifact anchor queries.

Ownership: core/engine/inference/retrieval.py
    Identifies the epicenter of a query inside the Cold Artifact using two
    complementary strategies:
        1. FTS5 lexical search  — exact/prefix keyword match on content_nodes
        2. ANN vector search    — cosine nearest-neighbours via numpy (no extra deps)

    Both strategies return a set of occurrence_ids that seed the Hot Envelope.

    load_subgraph() additionally derives occurrence-level inhibit candidates from
    pairwise vector anti-correlation inside the active neighbourhood.  These are
    returned under the key ``"inhibit_occ_pairs"`` for direct consumption by the
    Hot Engine's H-matrix builder.

Boundary rule: this module READS from cold_anatomy.db but NEVER writes.
It does not touch tree-sitter, BPE training, or GraphBLAS matrices.

V1 reference: _BDHyperNeuronEMITTER/src/engine/inference/retrieval.py
V1 changes (none — algorithms preserved identically):
    - Module docstring updated to v2 context
    - No algorithmic changes
"""

from __future__ import annotations

import sqlite3
import struct
from pathlib import Path
from typing import List, NamedTuple, Optional

# ── Types ─────────────────────────────────────────────────────────────

class AnchorResult(NamedTuple):
    occurrence_id: str
    hunk_id: str
    score: float          # FTS5 rank (negative = better) or cosine similarity
    origin_id: str
    node_kind: str
    content_snippet: str  # first 120 chars


# ── Helpers ───────────────────────────────────────────────────────────

def _blob_to_vec(blob: bytes) -> List[float]:
    n = len(blob) // 4
    return list(struct.unpack(f"<{n}f", blob))


def _cosine(a: List[float], b: List[float]) -> float:
    import math
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


# ── Public API ────────────────────────────────────────────────────────

def fts_search(
    conn: sqlite3.Connection,
    query: str,
    top_k: int = 10,
) -> List[AnchorResult]:
    """Full-text search over content_nodes via FTS5.

    Returns up to ``top_k`` occurrence anchors ranked by BM25 relevance.
    Each unique hunk_id may appear multiple times (once per occurrence).
    """
    rows = conn.execute(
        """SELECT o.occurrence_id, o.hunk_id, fts.rank,
                  o.origin_id, c.node_kind, c.content
           FROM content_fts fts
           JOIN content_nodes c ON c.rowid = fts.rowid
           JOIN occurrence_nodes o ON o.hunk_id = c.hunk_id
           WHERE content_fts MATCH ?
           ORDER BY fts.rank
           LIMIT ?""",
        (query, top_k),
    ).fetchall()

    return [
        AnchorResult(
            occurrence_id=r[0],
            hunk_id=r[1],
            score=float(r[2]),
            origin_id=r[3],
            node_kind=r[4],
            content_snippet=r[5][:120],
        )
        for r in rows
    ]


def ann_search(
    conn: sqlite3.Connection,
    query_vector: List[float],
    top_k: int = 10,
) -> List[AnchorResult]:
    """Approximate nearest-neighbour search over occurrence vectors.

    Uses brute-force cosine similarity (no sqlite-vec extension required).
    Efficient for the typical neighbourhood size loaded per query.
    """
    rows = conn.execute(
        """SELECT o.occurrence_id, o.hunk_id, o.vector_blob,
                  o.origin_id, c.node_kind, c.content
           FROM occurrence_nodes o
           JOIN content_nodes c ON c.hunk_id = o.hunk_id
           WHERE o.vector_blob IS NOT NULL"""
    ).fetchall()

    scored: List[tuple] = []
    for occ_id, hunk_id, blob, origin_id, node_kind, content in rows:
        vec = _blob_to_vec(blob)
        sim = _cosine(query_vector, vec)
        scored.append((sim, occ_id, hunk_id, origin_id, node_kind, content))

    scored.sort(key=lambda x: -x[0])

    return [
        AnchorResult(
            occurrence_id=r[1],
            hunk_id=r[2],
            score=r[0],
            origin_id=r[3],
            node_kind=r[4],
            content_snippet=r[5][:120],
        )
        for r in scored[:top_k]
    ]


def load_subgraph(
    conn: sqlite3.Connection,
    anchor_occurrence_ids: List[str],
    hop_limit: int = 2,
) -> dict:
    """Load the local subgraph around anchor occurrence_ids.

    Walks up to ``hop_limit`` hops through the relations table and returns
    a dict ready for the Hot Engine:

    Returns
    -------
    dict with keys:
        "nodes" : {occurrence_id: {"hunk_id", "node_kind", "attention_weight",
                                   "static_mass", "vector"}}
        "edges" : [(source_occ_id, op, target_occ_id, weight)]
        "inhibit_occ_pairs" : [(occ_id_a, occ_id_b, magnitude)]
            Occurrence-level inhibit candidates derived from pairwise vector
            anti-correlation (cosine < -0.2) within the active neighbourhood.
            Used by the Hot Engine to populate the H-matrix directly.
    """
    visited: set = set(anchor_occurrence_ids)
    frontier: set = set(anchor_occurrence_ids)

    for _ in range(hop_limit):
        if not frontier:
            break
        placeholders = ",".join("?" * len(frontier))
        neighbours = conn.execute(
            f"""SELECT DISTINCT target_occ_id FROM relations
                WHERE source_occ_id IN ({placeholders})
                UNION
                SELECT DISTINCT source_occ_id FROM relations
                WHERE target_occ_id IN ({placeholders})""",
            list(frontier) + list(frontier),
        ).fetchall()
        new_nodes = {r[0] for r in neighbours} - visited
        visited |= new_nodes
        frontier = new_nodes

    # Load node details
    placeholders = ",".join("?" * len(visited))
    node_rows = conn.execute(
        f"""SELECT o.occurrence_id, o.hunk_id, c.node_kind,
                   c.attention_weight, c.static_mass, o.vector_blob
            FROM occurrence_nodes o
            JOIN content_nodes c ON c.hunk_id = o.hunk_id
            WHERE o.occurrence_id IN ({placeholders})""",
        list(visited),
    ).fetchall()

    nodes = {}
    for occ_id, hunk_id, node_kind, aw, mass, blob in node_rows:
        nodes[occ_id] = {
            "hunk_id": hunk_id,
            "node_kind": node_kind,
            "attention_weight": aw,
            "static_mass": mass,
            "vector": _blob_to_vec(blob) if blob else None,
        }

    # Load edges within subgraph
    edge_rows = conn.execute(
        f"""SELECT source_occ_id, op, target_occ_id, weight
            FROM relations
            WHERE source_occ_id IN ({placeholders})
              AND target_occ_id IN ({placeholders})""",
        list(visited) + list(visited),
    ).fetchall()

    # Derive occurrence-level inhibit candidates from pairwise vector anti-correlation.
    # Two occurrence nodes whose SVD vectors are anti-correlated (cosine < -0.2) are
    # treated as occurrence-level contradiction pairs that the Hot Engine places
    # directly into the H-matrix — no token→occurrence mapping required.
    inhibit_occ_pairs: List[tuple] = _compute_occ_inhibits(nodes)

    return {
        "nodes": nodes,
        "edges": [(r[0], r[1], r[2], r[3]) for r in edge_rows],
        "inhibit_occ_pairs": inhibit_occ_pairs,
    }


def _compute_occ_inhibits(
    nodes: dict,
    anti_cosine_threshold: float = -0.2,
) -> List[tuple]:
    """Return occurrence-level inhibit pairs from vector anti-correlation.

    For each pair of occurrence nodes that both have SVD vectors, computes
    cosine similarity.  Pairs below ``anti_cosine_threshold`` are returned as
    ``(occ_id_a, occ_id_b, magnitude)`` where magnitude = |cosine|.

    Uses numpy for vectorised computation; returns empty list if numpy is
    unavailable or if fewer than two nodes have vectors.
    """
    vec_nodes = [
        (occ_id, data["vector"])
        for occ_id, data in nodes.items()
        if data.get("vector")
    ]
    if len(vec_nodes) < 2:
        return []

    try:
        import numpy as np

        ids = [v[0] for v in vec_nodes]
        mat = np.array([v[1] for v in vec_nodes], dtype=float)

        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms = np.where(norms == 0.0, 1.0, norms)
        unit_mat = mat / norms
        cos_mat = unit_mat @ unit_mat.T  # (n, n) cosine similarity matrix

        n = len(ids)
        pairs: List[tuple] = []
        for i in range(n):
            for j in range(i + 1, n):
                c = float(cos_mat[i, j])
                if c < anti_cosine_threshold:
                    pairs.append((ids[i], ids[j], abs(c)))
        return pairs

    except Exception:
        return []
