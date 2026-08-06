"""
evidence_bag — A reusable, modular Evidence Bag system for LTM-backed RAG.

Assembles bounded, density-packed bags of scored memory nodes for use as
short-term context in constrained local models (0.5B–7B and up).

Usage:
    from evidence_bag import EvidenceBagRuntime, RuntimeMode

    runtime = EvidenceBagRuntime("memory.db")
    runtime.ingest_node(kind="knowledge", content="...", tags=["python", "ast"])
    bag = runtime.assemble("How does the parser work?")
    for item in bag.items:
        print(item.content, item.score)
"""

from evidence_bag.node import Node, NodeKind, TrustState
from evidence_bag.config import (
    CompositionConfig,
    RuntimeMode,
    PRECISION_LOCAL,
    CONVERSATIONAL,
    EXPLORATION,
    TASK_LOCK,
    DEEP_PACKING,
)
from evidence_bag.runtime import EvidenceBagRuntime
from evidence_bag.scoring import GravityScorer
from evidence_bag.composition import BagComposer, EvidenceBag
from evidence_bag.store import NodeStore
from evidence_bag.tokenizer import tokenize, token_overlap

__all__ = [
    "EvidenceBagRuntime",
    "Node",
    "NodeKind",
    "TrustState",
    "CompositionConfig",
    "RuntimeMode",
    "PRECISION_LOCAL",
    "CONVERSATIONAL",
    "EXPLORATION",
    "TASK_LOCK",
    "DEEP_PACKING",
    "GravityScorer",
    "BagComposer",
    "EvidenceBag",
    "NodeStore",
    "tokenize",
    "token_overlap",
]
