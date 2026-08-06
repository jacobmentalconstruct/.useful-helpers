"""
manifold_kernel.projection.projector — Top-level projection orchestrator.

Coordinates: query → seeds → neighborhood → graph assembly → return.
This is where the "manifold view" emerges from the persistent bones.
"""

from __future__ import annotations

import logging
from typing import Optional, Set

from ..config import KernelConfig
from ..storage.sqlite_store import SQLiteStore
from ..ingest.semantic_adapter import SemanticAdapter
from ..types import ProjectionGraph
from .seed_retrieval import SeedCandidate, retrieve_seeds
from .neighborhood import expand_neighborhood
from .graph_builder import build_projection_graph

logger = logging.getLogger(__name__)


def project(
    query: str,
    store: SQLiteStore,
    semantic_adapter: SemanticAdapter,
    config: KernelConfig,
    max_seeds: Optional[int] = None,
    max_nodes: Optional[int] = None,
    radius: Optional[int] = None,
    relation_filter: Optional[Set[str]] = None,
) -> ProjectionGraph:
    """
    Build a bounded temporary in-memory manifold for the given query.

    Stages:
    1. Retrieve seed artifacts
    2. Expand neighborhood via typed relations
    3. Assemble projection graph with annotated nodes and edges
    """
    # 1. Seed retrieval
    seeds = retrieve_seeds(query, store, semantic_adapter, config, max_seeds)
    if not seeds:
        logger.warning("No seeds found for query: %s", query[:80])
        return ProjectionGraph()

    seed_ids = [s.artifact_id for s in seeds]
    seed_scores = {s.artifact_id: s.score for s in seeds}

    logger.info(
        "Projection: %d seeds for query '%s'",
        len(seeds), query[:60],
    )

    # 2. Neighborhood expansion
    node_ids, relations = expand_neighborhood(
        seed_ids, store, config,
        radius=radius,
        max_nodes=max_nodes,
        relation_filter=relation_filter,
    )

    # 3. Graph assembly
    graph = build_projection_graph(
        node_ids, relations, store,
        seed_ids=set(seed_ids),
    )

    # Annotate seed nodes with their retrieval scores
    for sid, score in seed_scores.items():
        if sid in graph.nodes:
            graph.nodes[sid].score_components["seed_score"] = score

    return graph
