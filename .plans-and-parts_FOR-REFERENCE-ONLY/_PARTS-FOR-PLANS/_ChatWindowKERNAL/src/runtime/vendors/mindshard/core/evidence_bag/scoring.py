"""
Gravity scorer for Evidence Bag nodes.

Implements the full scoring math from Evidence_Bag_and_Memory_Scoring.md:
  - Vector similarity (cosine, clamped)
  - Lexical overlap (tags, content, scope)
  - Recency bonus
  - Reinforcement (access frequency)
  - Noise penalties
  - Kind multipliers
  - Goal boundary dampening

Scoring is a pure function over nodes + query — it does not touch the
database or modify any state.
"""

from __future__ import annotations

import math
import time
from typing import List, Optional

from evidence_bag.config import (
    ANSWER_NOISE_PENALTIES,
    ANSWER_TRUST_MULTIPLIERS,
    CONTENT_NOISE_PENALTIES,
    KIND_MULTIPLIERS,
    TAG_NOISE_PENALTIES,
    CompositionConfig,
)
from evidence_bag.node import Node, NodeKind, ScoredNode, TrustState
from evidence_bag.tokenizer import tokenize, token_overlap


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class GravityScorer:
    """
    Scores a set of nodes against a query using the gravity formula.

    Usage:
        scorer = GravityScorer(config)
        scored = scorer.score_nodes(query_text, query_vector, nodes, active_goal_id)
    """

    def __init__(self, config: CompositionConfig) -> None:
        self.config = config

    def score_nodes(
        self,
        query_text: str,
        query_vector: Optional[List[float]],
        nodes: List[Node],
        active_goal_id: Optional[str] = None,
    ) -> List[ScoredNode]:
        """
        Score all nodes against the query and return ScoredNode list.

        Args:
            query_text:     The raw query string.
            query_vector:   Optional embedding vector for the query.
            nodes:          List of Node objects to score.
            active_goal_id: Current active goal ID for boundary dampening.

        Returns:
            List of ScoredNode with all score fields populated,
            sorted by final_score descending.
        """
        query_tokens = tokenize(query_text)
        now = time.time()
        cfg = self.config

        scored: List[ScoredNode] = []
        for node in nodes:
            sn = self._score_single(
                node, query_tokens, query_vector, active_goal_id, now, cfg
            )
            scored.append(sn)

        scored.sort(key=lambda s: s.final_score, reverse=True)
        return scored

    def _score_single(
        self,
        node: Node,
        query_tokens,
        query_vector: Optional[List[float]],
        active_goal_id: Optional[str],
        now: float,
        cfg: CompositionConfig,
    ) -> ScoredNode:
        sn = ScoredNode(node=node)

        # --- Vector similarity ---
        if query_vector is not None and node.vector is not None:
            raw_cos = _cosine_similarity(query_vector, node.vector)
            sn.vector_score = max(0.0, raw_cos)
        else:
            sn.vector_score = 0.0

        # --- Lexical overlap ---
        node_tag_tokens = tokenize(" ".join(node.tags))
        node_content_tokens = tokenize(node.content)
        node_scope_tokens = tokenize(node.source_ref)

        sn.tag_matches = token_overlap(query_tokens, node_tag_tokens)
        sn.content_matches = token_overlap(query_tokens, node_content_tokens)
        sn.scope_matches = token_overlap(query_tokens, node_scope_tokens)

        # --- Recency ---
        days_old = (now - node.created_at) / 86400.0
        sn.recency_bonus = cfg.recency_scale / (days_old + 1.0)

        # --- Reinforcement ---
        sn.reinforcement = cfg.reinforcement_scale * math.log(
            1.0 + node.access_count
        )

        # --- Noise penalty ---
        sn.noise_penalty = self._compute_noise(node)

        # --- Raw gravity score ---
        sn.raw_score = (
            cfg.w_vector * sn.vector_score
            + cfg.w_tag * sn.tag_matches
            + cfg.w_content * sn.content_matches
            + cfg.w_scope * sn.scope_matches
            + sn.recency_bonus
            + sn.reinforcement
            - sn.noise_penalty
        )
        # Floor at zero — don't let noise drive scores negative
        sn.raw_score = max(0.0, sn.raw_score)

        # --- Kind multiplier ---
        if node.kind == NodeKind.ANSWER:
            sn.kind_multiplier = ANSWER_TRUST_MULTIPLIERS.get(
                node.trust_state.value, 0.12
            )
        else:
            sn.kind_multiplier = KIND_MULTIPLIERS.get(
                node.kind.value, KIND_MULTIPLIERS["default"]
            )

        # --- Goal boundary dampener ---
        if (
            node.kind == NodeKind.ANSWER
            and node.goal_id is not None
            and active_goal_id is not None
            and node.goal_id != active_goal_id
        ):
            sn.boundary_dampener = 0.1
        else:
            sn.boundary_dampener = 1.0

        # --- Final score ---
        sn.final_score = (
            sn.raw_score * sn.kind_multiplier * sn.boundary_dampener
        )

        return sn

    @staticmethod
    def _compute_noise(node: Node) -> float:
        """Accumulate noise penalties from tags and content signals."""
        penalty = 0.0

        # Tag-based penalties
        for tag in node.tags:
            tag_lower = tag.lower()
            if tag_lower in TAG_NOISE_PENALTIES:
                penalty += TAG_NOISE_PENALTIES[tag_lower]

        # Answer-specific penalties
        if node.kind == NodeKind.ANSWER:
            trust_key = node.trust_state.value
            if trust_key in ANSWER_NOISE_PENALTIES:
                penalty += ANSWER_NOISE_PENALTIES[trust_key]

        # Content-based penalties
        content_lower = node.content.lower()
        if "traceback" in content_lower:
            penalty += CONTENT_NOISE_PENALTIES["traceback"]
        if len(node.content) > CONTENT_NOISE_PENALTIES["long_content_threshold"]:
            penalty += CONTENT_NOISE_PENALTIES["long_content_penalty"]

        return penalty
