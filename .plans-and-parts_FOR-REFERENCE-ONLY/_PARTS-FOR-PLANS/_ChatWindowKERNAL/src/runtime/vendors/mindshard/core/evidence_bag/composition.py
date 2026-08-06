"""
Evidence Bag composition and density packing.

Converts a scored candidate pool into a bounded, balanced evidence bag.
Implements category budgets, density-based greedy packing, redundancy
suppression, oversize handling, and spillover redistribution.

Design doc references:
  - evidence_bag_composition_and_tuning.md
  - evidence_bag_runtime_policy.md
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from evidence_bag.config import (
    CompositionConfig,
    OversizePolicy,
    PackingStrategy,
)
from evidence_bag.node import NodeKind, ScoredNode
from evidence_bag.redundancy import compute_redundancy_penalties


# ---------------------------------------------------------------------------
# Evidence Bag output
# ---------------------------------------------------------------------------

@dataclass
class BagItem:
    """A single item packed into the evidence bag."""

    node_id: Optional[int]
    kind: str
    content: str
    source_ref: str
    score: float
    density: float
    is_truncated: bool = False
    is_neighbor: bool = False

    @property
    def weight(self) -> int:
        return len(self.content)


@dataclass
class EvidenceBag:
    """
    The final assembled evidence bag, including metadata about how it
    was constructed (for debugging, replay, and tuning).
    """

    items: List[BagItem] = field(default_factory=list)
    total_chars: int = 0
    char_budget: int = 0
    runtime_metadata: Dict = field(default_factory=dict)

    @property
    def item_count(self) -> int:
        return len(self.items)

    @property
    def utilization(self) -> float:
        """Fraction of budget used."""
        if self.char_budget <= 0:
            return 0.0
        return self.total_chars / self.char_budget

    def to_prompt_block(self, header: str = "## Evidence") -> str:
        """Format the bag as a text block suitable for model prompts."""
        lines = [header]
        for i, item in enumerate(self.items, 1):
            tag = f"[{item.kind}]"
            src = f" ({item.source_ref})" if item.source_ref else ""
            trunc = " [truncated]" if item.is_truncated else ""
            lines.append(f"\n### {i}. {tag}{src}{trunc}")
            lines.append(item.content)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Composer
# ---------------------------------------------------------------------------

def _item_weight(content_len: int, alpha: float, base_cost: float) -> float:
    """Compute the packing weight of a content block."""
    return math.pow(content_len, alpha) + base_cost


def _node_density(score: float, content_len: int, alpha: float, base_cost: float) -> float:
    """Compute packing density = score / item_weight."""
    w = _item_weight(content_len, alpha, base_cost)
    if w <= 0:
        return 0.0
    return score / w


def _assign_category(sn: ScoredNode) -> str:
    """Map a scored node to its budget category."""
    if sn.is_neighbor:
        return "neighbor"
    return sn.node.kind.value if sn.node.kind.value in ("goal", "memory", "knowledge") else "knowledge"


class BagComposer:
    """
    Assembles a bounded Evidence Bag from scored candidate nodes.

    Usage:
        composer = BagComposer(config)
        bag = composer.compose(scored_candidates)
    """

    def __init__(self, config: CompositionConfig) -> None:
        self.config = config

    def compose(self, candidates: List[ScoredNode]) -> EvidenceBag:
        """
        Build an EvidenceBag from scored candidates.

        Steps:
          1. Assign candidates to categories
          2. Allocate category budgets
          3. Pack each category with redundancy-aware density ranking
          4. Redistribute unused budget (spillover)
          5. Apply oversize handling
          6. Emit final bag with metadata

        Args:
            candidates: Pre-scored, sorted candidate nodes.

        Returns:
            An EvidenceBag with items packed under the character budget.
        """
        cfg = self.config
        budget = cfg.char_budget

        # 1. Categorize
        by_category: Dict[str, List[ScoredNode]] = {
            "goal": [],
            "memory": [],
            "knowledge": [],
            "neighbor": [],
        }
        for sn in candidates:
            cat = _assign_category(sn)
            by_category.setdefault(cat, []).append(sn)

        # 2. Allocate budgets
        ratios = cfg.category_ratios
        cat_budgets: Dict[str, int] = {
            cat: int(budget * ratios.get(cat, 0))
            for cat in by_category
        }

        # 3. Pack each category
        selected: List[BagItem] = []
        selected_scored: List[ScoredNode] = []
        spillover_pool: List[ScoredNode] = []

        for cat in ("goal", "knowledge", "memory", "neighbor"):
            cat_nodes = by_category.get(cat, [])
            cat_budget = cat_budgets.get(cat, 0)

            packed, remaining, used = self._pack_category(
                cat_nodes, cat_budget, selected_scored, cfg
            )
            selected.extend(packed)
            selected_scored.extend(
                sn for sn in cat_nodes if any(
                    b.node_id == sn.node.node_id for b in packed
                )
            )

            # Track unused budget and leftover candidates for spillover
            unused = cat_budget - used
            if unused > 0:
                spillover_pool.extend(remaining)

        # 4. Spillover — fill remaining global budget
        total_used = sum(item.weight for item in selected)
        remaining_budget = budget - total_used

        if remaining_budget > 0 and spillover_pool:
            spill_packed, _, _ = self._pack_category(
                spillover_pool, remaining_budget, selected_scored, cfg
            )
            selected.extend(spill_packed)

        # 5. Build final bag
        total_chars = sum(item.weight for item in selected)
        bag = EvidenceBag(
            items=selected,
            total_chars=total_chars,
            char_budget=budget,
            runtime_metadata=self._build_metadata(cfg),
        )
        return bag

    def _pack_category(
        self,
        candidates: List[ScoredNode],
        budget: int,
        already_selected: List[ScoredNode],
        cfg: CompositionConfig,
    ) -> Tuple[List[BagItem], List[ScoredNode], int]:
        """
        Pack candidates into the given budget using density ranking.

        Returns:
            (packed_items, remaining_candidates, chars_used)
        """
        if not candidates or budget <= 0:
            return [], candidates, 0

        alpha = cfg.alpha
        base_cost = cfg.base_cost

        # Compute base densities
        density_list: List[Tuple[ScoredNode, float]] = []
        for sn in candidates:
            d = _node_density(
                sn.final_score, len(sn.node.content), alpha, base_cost
            )
            density_list.append((sn, d))

        # Apply redundancy penalties
        penalties = compute_redundancy_penalties(
            candidates, already_selected, cfg.redundancy_strength
        )
        adjusted: List[Tuple[ScoredNode, float]] = []
        for sn, d in density_list:
            nid = sn.node.node_id
            if nid is not None and nid in penalties:
                d = d * (1.0 - penalties[nid])
            adjusted.append((sn, d))

        # Sort by adjusted density descending
        adjusted.sort(key=lambda x: x[1], reverse=True)

        packed: List[BagItem] = []
        remaining: List[ScoredNode] = []
        used = 0

        for sn, density in adjusted:
            content = sn.node.content
            content_len = len(content)
            item_w = content_len + int(cfg.base_cost)

            if used + content_len <= budget:
                # Fits entirely
                packed.append(BagItem(
                    node_id=sn.node.node_id,
                    kind=sn.node.kind.value,
                    content=content,
                    source_ref=sn.node.source_ref,
                    score=sn.final_score,
                    density=density,
                    is_neighbor=sn.is_neighbor,
                ))
                used += content_len
            elif content_len > (budget - used) > 0:
                # Oversize — apply policy
                remaining_space = budget - used
                item = self._handle_oversize(
                    sn, density, remaining_space, cfg.oversize_policy
                )
                if item is not None:
                    packed.append(item)
                    used += item.weight
                else:
                    remaining.append(sn)
            else:
                remaining.append(sn)

        return packed, remaining, used

    @staticmethod
    def _handle_oversize(
        sn: ScoredNode,
        density: float,
        remaining_space: int,
        policy: OversizePolicy,
    ) -> Optional[BagItem]:
        """Apply oversize policy to a node that doesn't fit."""
        if policy == OversizePolicy.STRICT:
            return None

        if policy == OversizePolicy.TRUNCATE:
            truncated = sn.node.content[:remaining_space]
            return BagItem(
                node_id=sn.node.node_id,
                kind=sn.node.kind.value,
                content=truncated,
                source_ref=sn.node.source_ref,
                score=sn.final_score,
                density=density,
                is_truncated=True,
                is_neighbor=sn.is_neighbor,
            )

        if policy == OversizePolicy.FOCUS_EXTRACT:
            # Focus extract: keep the first chunk that fits.
            # A more sophisticated version could use query-token overlap
            # on sentence boundaries, but this keeps the default path fast.
            truncated = sn.node.content[:remaining_space]
            return BagItem(
                node_id=sn.node.node_id,
                kind=sn.node.kind.value,
                content=truncated,
                source_ref=sn.node.source_ref,
                score=sn.final_score,
                density=density,
                is_truncated=True,
                is_neighbor=sn.is_neighbor,
            )

        return None

    @staticmethod
    def _build_metadata(cfg: CompositionConfig) -> Dict:
        return {
            "budget_ratios": cfg.category_ratios,
            "alpha": cfg.alpha,
            "neighbor_beta": cfg.neighbor_beta,
            "neighbor_threshold": cfg.neighbor_threshold,
            "redundancy_penalty_strength": cfg.redundancy_strength.value,
            "oversize_policy": cfg.oversize_policy.value,
            "packing_strategy": cfg.packing_strategy.value,
            "top_seed_count": cfg.top_seed_count,
            "final_candidate_pool_cap": cfg.final_candidate_pool_cap,
            "char_budget": cfg.char_budget,
        }
