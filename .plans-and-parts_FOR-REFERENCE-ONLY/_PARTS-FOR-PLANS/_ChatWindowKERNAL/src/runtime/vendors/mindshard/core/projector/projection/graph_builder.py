"""
manifold_kernel.projection.graph_builder — Assemble the temporary in-memory projection graph.

Reads canonical records for the selected node set and assembles them
into a ProjectionGraph with annotated nodes and typed edges.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Set

from ..storage.sqlite_store import SQLiteStore
from ..types import (
    ArtifactType,
    ProjectionEdge,
    ProjectionGraph,
    ProjectionNode,
    RelationRecord,
)

logger = logging.getLogger(__name__)


def build_projection_graph(
    node_ids: Set[str],
    relations: List[RelationRecord],
    store: SQLiteStore,
    seed_ids: Set[str],
) -> ProjectionGraph:
    """
    Build an in-memory ProjectionGraph from the selected node set.

    Each node is annotated with its artifact type, a text preview from
    the verbatim record, and its depth from the nearest seed.
    """
    graph = ProjectionGraph()

    # Compute depth from seeds via BFS over the relation set
    depths = _compute_depths(node_ids, relations, seed_ids)

    for art_id in node_ids:
        artifact = store.get_artifact(art_id)
        if artifact is None:
            # Could be a source ID referenced in relations — skip
            continue

        verbatim = store.get_verbatim(art_id)
        text_preview = ""
        if verbatim:
            text_preview = verbatim.raw_text[:300]

        graph.add_node(ProjectionNode(
            artifact_id=art_id,
            artifact_type=artifact.artifact_type,
            score=0.0,  # will be filled by the lens engine
            text_preview=text_preview,
            depth=depths.get(art_id, 999),
        ))

    # Add edges (only between nodes that exist in the graph)
    seen_edges: set = set()
    for rel in relations:
        if rel.from_id in graph.nodes and rel.to_id in graph.nodes:
            edge_key = (rel.from_id, rel.to_id, rel.relation_type.value)
            if edge_key not in seen_edges:
                graph.add_edge(ProjectionEdge(
                    from_id=rel.from_id,
                    to_id=rel.to_id,
                    relation_type=rel.relation_type,
                    weight=rel.weight,
                ))
                seen_edges.add(edge_key)

    logger.debug(
        "Built projection graph: %d nodes, %d edges",
        graph.node_count, graph.edge_count,
    )
    return graph


def _compute_depths(
    node_ids: Set[str],
    relations: List[RelationRecord],
    seed_ids: Set[str],
) -> Dict[str, int]:
    """BFS from seeds to compute minimum depth for each node."""
    from collections import deque

    # Build adjacency from relations
    adj: Dict[str, List[str]] = {}
    for rel in relations:
        adj.setdefault(rel.from_id, []).append(rel.to_id)
        adj.setdefault(rel.to_id, []).append(rel.from_id)

    depths: Dict[str, int] = {}
    queue: deque = deque()

    for sid in seed_ids:
        if sid in node_ids:
            depths[sid] = 0
            queue.append(sid)

    while queue:
        current = queue.popleft()
        current_depth = depths[current]
        for neighbor in adj.get(current, []):
            if neighbor in node_ids and neighbor not in depths:
                depths[neighbor] = current_depth + 1
                queue.append(neighbor)

    return depths
