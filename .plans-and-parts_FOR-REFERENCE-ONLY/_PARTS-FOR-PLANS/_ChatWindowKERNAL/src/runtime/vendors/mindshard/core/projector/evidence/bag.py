"""
manifold_kernel.evidence.bag — Evidence bag model and distillation.

Transforms the scored projection graph into a bounded, structured
output package that downstream tools can consume.  The evidence bag
preserves provenance, ranking rationale, and extraction statistics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..config import KernelConfig, OutputConfig
from ..types import ProjectionGraph, ProjectionNode, RelationType

# Type-only import to avoid circular dependency at runtime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..storage.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)


@dataclass
class EvidenceItem:
    """A single piece of evidence with its provenance and score.

    Attribute aliases (content/source_ref/node_id/kind/is_neighbor/density)
    provide compatibility with the interrogation layer's typed record
    extractors, which expect CodeMONKEY BagItem field names.
    """
    artifact_id: str
    score: float
    score_components: Dict[str, float]
    text_snippet: str
    artifact_type: str
    depth: int
    source: str  # "seed", "neighbor", "propagated"
    source_path: str = ""  # file path of the originating source

    # ── Compatibility properties for interrogation layer ──────────
    @property
    def content(self) -> str:
        return self.text_snippet

    @property
    def source_ref(self) -> str:
        return self.source_path

    @property
    def node_id(self) -> str:
        return self.artifact_id

    @property
    def kind(self) -> str:
        return self.artifact_type

    @property
    def is_neighbor(self) -> bool:
        return self.source == "neighbor"

    @property
    def is_truncated(self) -> bool:
        return False

    @property
    def density(self) -> float:
        return self.score / max(len(self.text_snippet), 1) if self.text_snippet else 0.0


@dataclass
class EvidenceRelation:
    """A relation included in the evidence bag."""
    from_id: str
    to_id: str
    relation_type: str
    weight: float


@dataclass
class ExtractionStats:
    """Diagnostic statistics about the evidence extraction."""
    total_nodes_in_projection: int
    total_edges_in_projection: int
    items_included: int
    items_excluded: int
    max_score: float
    min_score: float
    mean_score: float


@dataclass
class EvidenceBag:
    """Bounded structured evidence package for downstream use."""
    query: str
    lens_profile: str
    items: List[EvidenceItem] = field(default_factory=list)
    relations: List[EvidenceRelation] = field(default_factory=list)
    seed_ids: List[str] = field(default_factory=list)
    stats: Optional[ExtractionStats] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


def _build_source_path_map(
    artifact_ids: List[str],
    store: Optional["SQLiteStore"],
) -> Dict[str, str]:
    """Batch-resolve artifact_id → originating file path via SourceRecord."""
    if store is None:
        return {}
    path_map: Dict[str, str] = {}
    # Cache source_id → path to avoid repeated lookups
    source_cache: Dict[str, str] = {}
    for aid in artifact_ids:
        art = store.get_artifact(aid)
        if art is None:
            continue
        sid = art.source_id
        if sid not in source_cache:
            src = store.get_source(sid)
            source_cache[sid] = src.path if src else ""
        path_map[aid] = source_cache[sid]
    return path_map


def distill_evidence(
    graph: ProjectionGraph,
    query: str,
    lens_profile: str,
    config: KernelConfig,
    seed_ids: Optional[List[str]] = None,
    max_items: Optional[int] = None,
    min_score: float = 0.0,
    store: Optional["SQLiteStore"] = None,
) -> EvidenceBag:
    """
    Distill the scored projection graph into a bounded evidence bag.

    Nodes are ranked by score and trimmed to max_items.  Relations
    between included nodes are preserved.

    Args:
        store: Optional SQLiteStore — when provided, each EvidenceItem's
               source_path is populated with the originating file path.
    """
    seed_set = set(seed_ids) if seed_ids else set()
    output_config = config.output

    # Sort nodes by score descending
    ranked: List[ProjectionNode] = sorted(
        graph.nodes.values(),
        key=lambda n: n.score,
        reverse=True,
    )

    # Apply bounds
    if max_items is None:
        max_items = config.projection.default_max_nodes
    included_nodes = [n for n in ranked if n.score >= min_score][:max_items]
    included_ids = {n.artifact_id for n in included_nodes}

    # Batch-resolve source paths
    source_paths = _build_source_path_map(
        [n.artifact_id for n in included_nodes], store,
    )

    # Build evidence items
    items: List[EvidenceItem] = []
    for node in included_nodes:
        source = "seed" if node.artifact_id in seed_set else (
            "neighbor" if node.depth <= 1 else "propagated"
        )
        snippet = node.text_preview
        if output_config.include_text_snippets:
            snippet = snippet[:output_config.max_snippet_chars]
        else:
            snippet = ""

        items.append(EvidenceItem(
            artifact_id=node.artifact_id,
            score=node.score,
            score_components=node.score_components,
            text_snippet=snippet,
            artifact_type=node.artifact_type.value if isinstance(node.artifact_type, RelationType.__class__) else str(node.artifact_type.value),
            depth=node.depth,
            source=source,
            source_path=source_paths.get(node.artifact_id, ""),
        ))

    # Include relations between evidence items
    evidence_relations: List[EvidenceRelation] = []
    if output_config.include_relation_metadata:
        for edge in graph.edges:
            if edge.from_id in included_ids and edge.to_id in included_ids:
                evidence_relations.append(EvidenceRelation(
                    from_id=edge.from_id,
                    to_id=edge.to_id,
                    relation_type=edge.relation_type.value,
                    weight=edge.weight,
                ))

    # Compute stats
    scores = [n.score for n in included_nodes] if included_nodes else [0.0]
    stats = ExtractionStats(
        total_nodes_in_projection=graph.node_count,
        total_edges_in_projection=graph.edge_count,
        items_included=len(items),
        items_excluded=graph.node_count - len(items),
        max_score=max(scores),
        min_score=min(scores),
        mean_score=sum(scores) / len(scores),
    )

    return EvidenceBag(
        query=query,
        lens_profile=lens_profile,
        items=items,
        relations=evidence_relations,
        seed_ids=list(seed_set),
        stats=stats,
    )
