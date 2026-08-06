"""
manifold_kernel.projection.neighborhood — Typed relation neighborhood expansion.

Starting from seed nodes, expand outward through typed relations up to a
configurable radius, respecting node count bounds.
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from ..config import KernelConfig
from ..storage.sqlite_store import SQLiteStore
from ..types import RelationRecord, RelationType

logger = logging.getLogger(__name__)


def expand_neighborhood(
    seed_ids: List[str],
    store: SQLiteStore,
    config: KernelConfig,
    radius: Optional[int] = None,
    max_nodes: Optional[int] = None,
    relation_filter: Optional[Set[str]] = None,
) -> Tuple[Set[str], List[RelationRecord]]:
    """
    BFS expansion from seeds through typed relations.

    Returns:
        (set of all reached artifact IDs, list of traversed relations)
    """
    radius = radius or config.projection.default_radius
    max_nodes = max_nodes or config.projection.default_max_nodes

    visited: Set[str] = set(seed_ids)
    all_relations: List[RelationRecord] = []
    frontier: deque = deque()

    # Initialise frontier with seeds at depth 0
    for sid in seed_ids:
        frontier.append((sid, 0))

    while frontier and len(visited) < max_nodes:
        current_id, depth = frontier.popleft()

        if depth >= radius:
            continue

        # Get all relations involving this artifact
        relations = store.get_relations_involving(current_id)

        for rel in relations:
            # Apply relation type filter if specified
            if relation_filter and rel.relation_type.value not in relation_filter:
                continue

            # Determine the neighbor
            neighbor_id = rel.to_id if rel.from_id == current_id else rel.from_id

            all_relations.append(rel)

            if neighbor_id not in visited and len(visited) < max_nodes:
                visited.add(neighbor_id)
                frontier.append((neighbor_id, depth + 1))

    logger.debug(
        "Neighborhood expansion: %d seeds → %d nodes, %d edges (radius=%d)",
        len(seed_ids), len(visited), len(all_relations), radius,
    )
    return visited, all_relations
