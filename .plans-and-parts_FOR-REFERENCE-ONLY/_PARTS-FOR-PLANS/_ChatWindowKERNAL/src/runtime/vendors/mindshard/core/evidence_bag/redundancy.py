"""
Redundancy suppression for Evidence Bag composition.

Applies density penalties to nodes that share provenance, tags, or
structural neighborhood with already-selected items. Uses metadata
heuristics only — no pairwise embedding similarity in the default path.

Design doc reference: evidence_bag_composition_and_tuning.md §8
"""

from __future__ import annotations

from typing import Dict, List, Set, Tuple

from evidence_bag.config import RedundancyStrength
from evidence_bag.node import ScoredNode

# Penalty factor per redundancy strength level.
# These are the maximum cumulative penalty factors applied to density.
_STRENGTH_CAPS: Dict[RedundancyStrength, float] = {
    RedundancyStrength.LOW: 0.25,
    RedundancyStrength.MEDIUM: 0.50,
    RedundancyStrength.HIGH: 0.75,
}

# Per-signal contribution to redundancy_penalty_factor
_SOURCE_OVERLAP_WEIGHT = 0.30
_TAG_CLUSTER_WEIGHT = 0.20
_CATEGORY_SOURCE_REPEAT_WEIGHT = 0.25


def compute_redundancy_penalties(
    candidates: List[ScoredNode],
    selected: List[ScoredNode],
    strength: RedundancyStrength,
) -> Dict[int, float]:
    """
    Compute per-candidate redundancy penalty factors.

    For each candidate, checks overlap with already-selected items on:
      - same source_ref
      - shared tag cluster
      - repeated (category, source) combinations

    Args:
        candidates: Nodes being considered for packing.
        selected:   Nodes already packed into the bag.
        strength:   Controls the maximum penalty cap.

    Returns:
        Dict mapping candidate node_id → penalty_factor in [0, cap).
        Missing IDs have zero penalty.
    """
    if not selected or not candidates:
        return {}

    cap = _STRENGTH_CAPS.get(strength, 0.50)

    # Pre-compute selected signatures
    selected_sources: Set[str] = set()
    selected_tags: Set[str] = set()
    selected_cat_source: Set[Tuple[str, str]] = set()

    for sn in selected:
        src = sn.node.source_ref
        if src:
            selected_sources.add(src)
        for tag in sn.node.tags:
            selected_tags.add(tag.lower())
        selected_cat_source.add((sn.node.kind.value, src))

    penalties: Dict[int, float] = {}

    for cand in candidates:
        nid = cand.node.node_id
        if nid is None:
            continue

        penalty = 0.0

        # Source overlap
        if cand.node.source_ref and cand.node.source_ref in selected_sources:
            penalty += _SOURCE_OVERLAP_WEIGHT

        # Tag cluster overlap
        cand_tags = {t.lower() for t in cand.node.tags}
        if cand_tags and selected_tags:
            overlap_ratio = len(cand_tags & selected_tags) / len(cand_tags)
            penalty += _TAG_CLUSTER_WEIGHT * overlap_ratio

        # Category+source repeat
        cat_src = (cand.node.kind.value, cand.node.source_ref)
        if cat_src in selected_cat_source:
            penalty += _CATEGORY_SOURCE_REPEAT_WEIGHT

        # Clamp to cap
        penalty = min(penalty, cap)
        if penalty > 0.0:
            penalties[nid] = penalty

    return penalties
