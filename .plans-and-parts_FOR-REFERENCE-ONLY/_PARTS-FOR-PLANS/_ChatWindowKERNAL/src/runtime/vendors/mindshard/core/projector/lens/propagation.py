"""
manifold_kernel.lens.propagation — Score propagation across the projection graph.

After initial per-node scoring, this module spreads influence through
the graph edges.  Nodes connected to high-scoring neighbors receive a
boost, creating a "gravity well" effect around evidence clusters.

This is an optional post-processing pass that can be applied after
the base scoring in scoring.py.
"""

from __future__ import annotations

import logging
from typing import Dict, List

from ..config import LensConfig
from ..types import ProjectionGraph

logger = logging.getLogger(__name__)


def propagate_scores(
    graph: ProjectionGraph,
    lens: LensConfig,
    iterations: int = 2,
) -> ProjectionGraph:
    """
    Diffuse scores along edges with decay.

    Each iteration, a node accumulates a fraction of its neighbors'
    scores weighted by edge weight and the propagation_decay factor.

    Mutates the graph in-place and returns it for chaining.
    """
    if not graph.nodes or not graph.edges:
        return graph

    decay = lens.propagation_decay

    # Build adjacency with weights
    adj: Dict[str, List[tuple]] = {}
    for edge in graph.edges:
        adj.setdefault(edge.from_id, []).append((edge.to_id, edge.weight))
        adj.setdefault(edge.to_id, []).append((edge.from_id, edge.weight))

    for iteration in range(iterations):
        # Compute deltas first (don't update in-place during iteration)
        deltas: Dict[str, float] = {}

        for art_id, node in graph.nodes.items():
            neighbors = adj.get(art_id, [])
            if not neighbors:
                continue

            neighbor_influence = 0.0
            for neighbor_id, edge_weight in neighbors:
                if neighbor_id in graph.nodes:
                    neighbor_influence += graph.nodes[neighbor_id].score * edge_weight

            # Average neighbor influence scaled by decay
            avg_influence = neighbor_influence / len(neighbors)
            deltas[art_id] = avg_influence * decay * (0.5 ** iteration)

        # Apply deltas
        for art_id, delta in deltas.items():
            graph.nodes[art_id].score += delta
            graph.nodes[art_id].score_components["propagation_boost"] = (
                graph.nodes[art_id].score_components.get("propagation_boost", 0.0) + delta
            )

    # Round final scores
    for node in graph.nodes.values():
        node.score = round(node.score, 6)
        node.score_components = {k: round(v, 6) for k, v in node.score_components.items()}

    return graph
