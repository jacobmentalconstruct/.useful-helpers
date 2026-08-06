"""
manifold_kernel.lens.scoring — Core lens scoring function.

Applies the configurable scoring equation to each node in a projection
graph, producing per-node composite scores with full component breakdown.

    score(node) =
        a * semantic_similarity
      + b * structural_proximity
      + c * identity_relevance
      + d * adjacency_support
      + e * exact_match

Each factor is computed from node metadata, graph topology, and the
query context.  The lens engine is strictly separated from storage.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from ..config import LensConfig
from ..types import ProjectionGraph, ProjectionNode, RelationType
from ..ingest.semantic_adapter import SemanticAdapter, blob_to_vector
from ..storage.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)


def score_graph(
    graph: ProjectionGraph,
    query: str,
    store: SQLiteStore,
    semantic_adapter: SemanticAdapter,
    lens: LensConfig,
    seed_ids: Optional[List[str]] = None,
) -> ProjectionGraph:
    """
    Apply lens scoring to every node in the projection graph.

    Mutates the graph in-place by setting node.score and
    node.score_components for each node.

    Returns the same graph for chaining.
    """
    if not graph.nodes:
        return graph

    seed_set = set(seed_ids) if seed_ids else set()

    # Pre-compute query embedding for semantic scoring
    query_vec = None
    if semantic_adapter.backend_name != "none":
        try:
            result = semantic_adapter.embed(query)
            query_vec = result.vector if result.vector else None
        except Exception:
            pass

    # Build adjacency index for neighborhood density
    adjacency: Dict[str, List[str]] = {}
    for edge in graph.edges:
        adjacency.setdefault(edge.from_id, []).append(edge.to_id)
        adjacency.setdefault(edge.to_id, []).append(edge.from_id)

    for art_id, node in graph.nodes.items():
        components = _compute_components(
            node=node,
            art_id=art_id,
            query=query,
            query_vec=query_vec,
            store=store,
            semantic_adapter=semantic_adapter,
            adjacency=adjacency,
            seed_set=seed_set,
            lens=lens,
        )

        # Weighted sum
        score = (
            lens.semantic_similarity * components.get("semantic_similarity", 0.0)
            + lens.structural_proximity * components.get("structural_proximity", 0.0)
            + lens.identity_relevance * components.get("identity_relevance", 0.0)
            + lens.adjacency_support * components.get("adjacency_support", 0.0)
            + lens.exact_match * components.get("exact_match", 0.0)
        )

        # Neighborhood density bonus
        neighbor_count = len(adjacency.get(art_id, []))
        density_bonus = min(neighbor_count * lens.neighborhood_density_bonus, 0.2)
        score += density_bonus
        components["neighborhood_density"] = density_bonus

        # Propagation decay by depth
        if node.depth > 0:
            decay = lens.propagation_decay ** node.depth
            score *= decay
            components["decay_factor"] = decay

        node.score = round(score, 6)
        node.score_components = {k: round(v, 6) for k, v in components.items()}

    return graph


def _compute_components(
    node: ProjectionNode,
    art_id: str,
    query: str,
    query_vec: Optional[List[float]],
    store: SQLiteStore,
    semantic_adapter: SemanticAdapter,
    adjacency: Dict[str, List[str]],
    seed_set: set,
    lens: LensConfig,
) -> Dict[str, float]:
    """Compute individual scoring factors for a single node."""
    components: Dict[str, float] = {}

    # ── Semantic similarity ──────────────────────────────────────
    if query_vec:
        sem_rec = store.get_semantic(art_id)
        if sem_rec and sem_rec.feature_blob:
            node_vec = blob_to_vector(sem_rec.feature_blob)
            if node_vec:
                sim = semantic_adapter.similarity(query_vec, node_vec)
                components["semantic_similarity"] = max(0.0, sim)
            else:
                components["semantic_similarity"] = 0.0
        else:
            components["semantic_similarity"] = 0.0
    else:
        components["semantic_similarity"] = 0.0

    # ── Structural proximity ─────────────────────────────────────
    # Closer to seeds = higher structural score
    max_depth = 10
    if node.depth <= max_depth:
        components["structural_proximity"] = 1.0 - (node.depth / max_depth)
    else:
        components["structural_proximity"] = 0.0

    # ── Identity relevance ───────────────────────────────────────
    # Seeds get full identity score
    components["identity_relevance"] = 1.0 if art_id in seed_set else 0.0

    # ── Adjacency support ────────────────────────────────────────
    # How many of this node's neighbors are also seeds?
    neighbors = adjacency.get(art_id, [])
    if neighbors:
        seed_neighbor_count = sum(1 for n in neighbors if n in seed_set)
        components["adjacency_support"] = seed_neighbor_count / len(neighbors)
    else:
        components["adjacency_support"] = 0.0

    # ── Exact match ──────────────────────────────────────────────
    query_lower = query.lower().strip()
    text_lower = node.text_preview.lower()
    if query_lower and query_lower in text_lower:
        # Score by coverage ratio
        components["exact_match"] = min(1.0, len(query_lower) / max(len(text_lower), 1) + 0.5)
    else:
        components["exact_match"] = 0.0

    return components
