"""
Node data model for the Evidence Bag system.

Nodes are the atomic units of memory. Each node carries content, metadata,
and optional embedding vectors. The scoring and composition layers operate
on nodes without knowing where they came from.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class NodeKind(Enum):
    """Categories of memory nodes."""

    GOAL = "goal"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    TOOL_RESULT = "tool_result"
    ANSWER = "answer"


class TrustState(Enum):
    """Trust levels for answer nodes. Other node kinds ignore this."""

    NORMAL = "normal"
    WEAK = "weak"
    UNVERIFIED = "unverified"
    ERROR = "error"
    UNTAGGED = "untagged"
    SUPERSEDED = "superseded"


@dataclass
class Node:
    """
    A single memory node.

    Attributes:
        node_id:      Unique identifier (assigned by the store).
        kind:         Category of this node.
        content:      The text payload.
        tags:         Freeform tags for lexical matching and noise detection.
        source_ref:   Provenance string (file path, URL, tool name, etc.).
        created_at:   Unix timestamp of creation.
        access_count: How many times this node has been retrieved.
        goal_id:      Optional goal this node is associated with.
        trust_state:  Trust level (only meaningful for ANSWER nodes).
        connections:  Explicit edges to other node IDs (for neighbor expansion).
        vector:       Optional pre-computed embedding (list of floats).
    """

    node_id: Optional[int] = None
    kind: NodeKind = NodeKind.KNOWLEDGE
    content: str = ""
    tags: List[str] = field(default_factory=list)
    source_ref: str = ""
    created_at: float = field(default_factory=time.time)
    access_count: int = 0
    goal_id: Optional[str] = None
    trust_state: TrustState = TrustState.NORMAL
    connections: List[int] = field(default_factory=list)
    vector: Optional[List[float]] = None


@dataclass
class ScoredNode:
    """
    A node with computed scores attached, produced by the scoring layer.

    Attributes:
        node:               The underlying Node.
        vector_score:       Clamped cosine similarity against the query.
        tag_matches:        Count of overlapping tag tokens with the query.
        content_matches:    Count of overlapping content tokens with the query.
        scope_matches:      Count of overlapping source_ref tokens with the query.
        recency_bonus:      Time-decay bonus.
        reinforcement:      Access-frequency bonus.
        noise_penalty:      Accumulated penalty from noise signals.
        raw_score:          Gravity score before kind/boundary shaping.
        kind_multiplier:    Multiplier for this node's kind.
        boundary_dampener:  Goal-boundary dampener (1.0 unless cross-goal answer).
        final_score:        raw_score * kind_multiplier * boundary_dampener.
        is_neighbor:        True if this node was added via neighbor expansion.
        seed_parent_id:     If is_neighbor, the seed node that expanded to this.
    """

    node: Node
    vector_score: float = 0.0
    tag_matches: int = 0
    content_matches: int = 0
    scope_matches: int = 0
    recency_bonus: float = 0.0
    reinforcement: float = 0.0
    noise_penalty: float = 0.0
    raw_score: float = 0.0
    kind_multiplier: float = 1.0
    boundary_dampener: float = 1.0
    final_score: float = 0.0
    is_neighbor: bool = False
    seed_parent_id: Optional[int] = None
