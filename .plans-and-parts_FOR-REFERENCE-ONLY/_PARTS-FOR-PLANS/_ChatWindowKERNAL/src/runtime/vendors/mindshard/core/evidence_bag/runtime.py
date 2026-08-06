"""
Evidence Bag runtime — the top-level pipeline orchestrator.

Owns the full query → bag pipeline:
  1. Seed resolution
  2. Initial candidate retrieval
  3. Node scoring
  4. Top seed selection
  5. Neighbor expansion + scoring
  6. Final candidate pool assembly
  7. Evidence bag composition

This is the only class most consumers need to interact with.
The store, scorer, and composer are internal implementation details.

Design doc reference: evidence_bag_runtime_policy.md §3
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional

from evidence_bag.composition import BagComposer, EvidenceBag
from evidence_bag.config import (
    CompositionConfig,
    RuntimeMode,
    config_for_mode,
)
from evidence_bag.node import Node, NodeKind, ScoredNode, TrustState
from evidence_bag.scoring import GravityScorer
from evidence_bag.store import NodeStore


class EvidenceBagRuntime:
    """
    Top-level runtime for the Evidence Bag system.

    Manages the node store, runs the scoring → composition pipeline,
    and exposes a simple API for ingesting nodes and assembling bags.

    Usage:
        runtime = EvidenceBagRuntime("memory.db")
        runtime.ingest_node(kind="knowledge", content="...", tags=["python"])
        bag = runtime.assemble("How does the parser work?", query_vector=[...])

    The runtime is decoupled from any embedding model. Vectors are passed
    in by the caller (or adapter layer). This makes the package reusable
    across different embedding backends.
    """

    def __init__(
        self,
        db_path: str | Path,
        config: Optional[CompositionConfig] = None,
        mode: RuntimeMode = RuntimeMode.PRECISION_LOCAL,
    ) -> None:
        """
        Initialize the runtime.

        Args:
            db_path: Path to the SQLite database file.
            config:  Optional explicit config. If None, uses the mode preset.
            mode:    Runtime mode preset (ignored if config is provided).
        """
        if config is not None:
            self.config = config
        else:
            self.config = config_for_mode(mode)

        self.store = NodeStore(db_path)
        self.scorer = GravityScorer(self.config)
        self.composer = BagComposer(self.config)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def set_mode(self, mode: RuntimeMode) -> None:
        """Switch to a named runtime mode, rebuilding scorer and composer."""
        self.config = config_for_mode(mode)
        self.scorer = GravityScorer(self.config)
        self.composer = BagComposer(self.config)

    def set_config(self, config: CompositionConfig) -> None:
        """Apply a custom configuration."""
        self.config = config
        self.scorer = GravityScorer(self.config)
        self.composer = BagComposer(self.config)

    # ------------------------------------------------------------------
    # Node ingestion
    # ------------------------------------------------------------------

    def ingest_node(
        self,
        kind: str = "knowledge",
        content: str = "",
        tags: Optional[List[str]] = None,
        source_ref: str = "",
        goal_id: Optional[str] = None,
        trust_state: str = "normal",
        connections: Optional[List[int]] = None,
        vector: Optional[List[float]] = None,
    ) -> int:
        """
        Create and store a new node.

        Args:
            kind:        One of: goal, memory, knowledge, tool_result, answer.
            content:     The text payload.
            tags:        Optional freeform tags.
            source_ref:  Provenance string.
            goal_id:     Optional goal association.
            trust_state: Trust level (for answer nodes).
            connections: Optional list of connected node IDs.
            vector:      Optional pre-computed embedding.

        Returns:
            The new node's ID.
        """
        node = Node(
            kind=NodeKind(kind),
            content=content,
            tags=tags or [],
            source_ref=source_ref,
            goal_id=goal_id,
            trust_state=TrustState(trust_state),
            connections=connections or [],
            vector=vector,
        )
        return self.store.insert(node)

    def ingest_nodes(self, nodes: List[Node]) -> List[int]:
        """Batch-insert pre-built Node objects. Returns list of IDs."""
        return self.store.insert_batch(nodes)

    def connect(self, from_id: int, to_id: int) -> None:
        """Add a directed edge between two nodes."""
        self.store.add_connection(from_id, to_id)

    def update_embedding(self, node_id: int, vector: List[float]) -> None:
        """Set or replace the embedding vector for a node."""
        self.store.update_vector(node_id, vector)

    # ------------------------------------------------------------------
    # Assembly pipeline
    # ------------------------------------------------------------------

    def assemble(
        self,
        query_text: str,
        query_vector: Optional[List[float]] = None,
        active_goal_id: Optional[str] = None,
        char_budget: Optional[int] = None,
    ) -> EvidenceBag:
        """
        Run the full pipeline: retrieve → score → expand → compose → bag.

        Args:
            query_text:     The user's query or task description.
            query_vector:   Optional embedding vector for the query.
            active_goal_id: Current goal ID for boundary dampening.
            char_budget:    Override the config's char_budget for this call.

        Returns:
            An assembled EvidenceBag.
        """
        cfg = self.config
        if char_budget is not None:
            # Temporarily override budget for this assembly
            original_budget = cfg.char_budget
            cfg.char_budget = char_budget
            self.composer.config = cfg

        try:
            bag = self._run_pipeline(query_text, query_vector, active_goal_id)
        finally:
            if char_budget is not None:
                cfg.char_budget = original_budget
                self.composer.config = cfg

        # Bump access counts for packed nodes
        packed_ids = [
            item.node_id for item in bag.items if item.node_id is not None
        ]
        if packed_ids:
            self.store.increment_access_batch(packed_ids)

        # Record runtime mode in metadata
        bag.runtime_metadata["runtime_mode"] = (
            cfg.packing_strategy.value
        )

        return bag

    def _run_pipeline(
        self,
        query_text: str,
        query_vector: Optional[List[float]],
        active_goal_id: Optional[str],
    ) -> EvidenceBag:
        """
        Internal pipeline implementation.

        Pipeline order (from runtime policy doc §3):
          1. Initial candidate retrieval (all nodes)
          2. Initial node scoring
          3. Top seed selection
          4. Neighbor expansion
          5. Neighbor scoring
          6. Final candidate pool assembly (capped)
          7. Evidence bag composition
        """
        cfg = self.config

        # 1. Retrieve all nodes
        all_nodes = self.store.get_all()
        if not all_nodes:
            return EvidenceBag(char_budget=cfg.char_budget)

        # 2. Score all nodes
        scored = self.scorer.score_nodes(
            query_text, query_vector, all_nodes, active_goal_id
        )

        # 3. Top seed selection
        seeds = scored[: cfg.top_seed_count]

        # 4. Neighbor expansion
        neighbor_scored: List[ScoredNode] = []
        seen_ids = {sn.node.node_id for sn in scored if sn.node.node_id is not None}

        for seed in seeds:
            if seed.node.node_id is None:
                continue
            connected = self.store.get_connected(seed.node.node_id)
            for neighbor_node in connected:
                if neighbor_node.node_id in seen_ids:
                    continue
                seen_ids.add(neighbor_node.node_id)

                # 5. Score neighbor
                neighbor_results = self.scorer.score_nodes(
                    query_text,
                    query_vector,
                    [neighbor_node],
                    active_goal_id,
                )
                if not neighbor_results:
                    continue

                nsn = neighbor_results[0]
                # Apply neighbor propagation: score = beta * seed_score
                propagated = cfg.neighbor_beta * seed.final_score
                nsn.final_score = propagated
                nsn.is_neighbor = True
                nsn.seed_parent_id = seed.node.node_id

                # Threshold gate
                if nsn.final_score >= cfg.neighbor_threshold:
                    neighbor_scored.append(nsn)

        # 6. Final candidate pool (seeds + rest + neighbors, capped)
        # Include all initially scored nodes, plus admitted neighbors
        full_pool = scored + neighbor_scored
        full_pool.sort(key=lambda s: s.final_score, reverse=True)
        full_pool = full_pool[: cfg.final_candidate_pool_cap]

        # 7. Compose the bag
        bag = self.composer.compose(full_pool)
        return bag

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def node_count(self) -> int:
        """Return total number of stored nodes."""
        return self.store.count()

    def get_node(self, node_id: int) -> Optional[Node]:
        """Retrieve a single node by ID."""
        return self.store.get(node_id)

    def close(self) -> None:
        """Close the underlying database connection."""
        self.store.close()
