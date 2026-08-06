"""
manifold_kernel.relations.relation_types — Relation type metadata and validation.

Provides utilities for querying relation properties: directionality,
inverse relations, and allowed combinations.
"""

from __future__ import annotations

from typing import Dict, Optional

from ..types import RelationType


# ── Inverse relation map ─────────────────────────────────────────────

INVERSE_MAP: Dict[RelationType, RelationType] = {
    RelationType.PARENT_OF: RelationType.CHILD_OF,
    RelationType.CHILD_OF: RelationType.PARENT_OF,
    RelationType.PREV_OF: RelationType.NEXT_OF,
    RelationType.NEXT_OF: RelationType.PREV_OF,
    RelationType.CONTAINS: RelationType.CONTAINED_BY,
    RelationType.CONTAINED_BY: RelationType.CONTAINS,
}

# Symmetric relations (their own inverse)
SYMMETRIC_TYPES = frozenset({
    RelationType.SAME_ARTIFACT,
    RelationType.SEMANTIC_NEIGHBOR,
})

# Structural (topology-preserving) relations
STRUCTURAL_TYPES = frozenset({
    RelationType.PARENT_OF,
    RelationType.CHILD_OF,
    RelationType.PREV_OF,
    RelationType.NEXT_OF,
    RelationType.CONTAINS,
    RelationType.CONTAINED_BY,
    RelationType.BELONGS_TO_SOURCE,
})

# Anchoring (query/session/agent/user context) relations
ANCHOR_TYPES = frozenset({
    RelationType.ANCHORED_TO_QUERY,
    RelationType.ANCHORED_TO_SESSION,
    RelationType.ANCHORED_TO_AGENT,
    RelationType.ANCHORED_TO_USER,
})


def inverse_of(rt: RelationType) -> Optional[RelationType]:
    """Return the inverse relation type, or None for symmetric/anchor types."""
    if rt in SYMMETRIC_TYPES:
        return rt
    return INVERSE_MAP.get(rt)


def is_structural(rt: RelationType) -> bool:
    return rt in STRUCTURAL_TYPES


def is_symmetric(rt: RelationType) -> bool:
    return rt in SYMMETRIC_TYPES


def is_anchor(rt: RelationType) -> bool:
    return rt in ANCHOR_TYPES
