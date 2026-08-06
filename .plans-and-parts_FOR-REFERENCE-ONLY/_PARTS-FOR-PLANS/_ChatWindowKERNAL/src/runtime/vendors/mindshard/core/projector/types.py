"""
manifold_kernel.types — Canonical record types and identity primitives.

Every artifact is stably addressable through its artifact_id regardless of
which representational dimension is being accessed.  The types here form the
persistent bones of the system; richer behaviour arises in the transient
projection layer.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ── Identity helpers ─────────────────────────────────────────────────

def make_artifact_id() -> str:
    """Generate a new globally-unique artifact ID."""
    return f"art_{uuid.uuid4().hex[:16]}"


def make_relation_id() -> str:
    """Generate a new globally-unique relation ID."""
    return f"rel_{uuid.uuid4().hex[:16]}"


def make_source_id() -> str:
    """Generate a new globally-unique source ID."""
    return f"src_{uuid.uuid4().hex[:16]}"


def content_hash(text: str) -> str:
    """Deterministic SHA-256 hash of normalised content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Enums ────────────────────────────────────────────────────────────

class ArtifactType(str, Enum):
    TEXT_CHUNK = "text_chunk"
    CODE_CHUNK = "code_chunk"
    SECTION = "section"
    DOCUMENT = "document"
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    OTHER = "other"


class RelationType(str, Enum):
    """Typed edges between artifacts or across dimensions."""
    SAME_ARTIFACT = "same_artifact"
    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"
    PREV_OF = "prev_of"
    NEXT_OF = "next_of"
    CONTAINS = "contains"
    CONTAINED_BY = "contained_by"
    DERIVED_FROM = "derived_from"
    SEMANTIC_NEIGHBOR = "semantic_neighbor"
    BELONGS_TO_SOURCE = "belongs_to_source"
    ANCHORED_TO_QUERY = "anchored_to_query"
    ANCHORED_TO_SESSION = "anchored_to_session"
    ANCHORED_TO_AGENT = "anchored_to_agent"
    ANCHORED_TO_USER = "anchored_to_user"


class SemanticBackend(str, Enum):
    BDVEC = "bdvec"
    NONE = "none"


# ── Canonical record types ───────────────────────────────────────────

@dataclass
class ArtifactRecord:
    """Owns stable identity and basic metadata for one artifact unit."""
    artifact_id: str
    source_id: str
    artifact_type: ArtifactType
    content_hash: str
    created_at: str = field(default_factory=_utcnow)
    metadata_json: str = field(default_factory=lambda: "{}")


@dataclass
class VerbatimRecord:
    """Exact or recoverable content representation."""
    artifact_id: str
    raw_text: str
    normalized_text: str
    byte_start: int = 0
    byte_end: int = 0
    char_start: int = 0
    char_end: int = 0


@dataclass
class StructuralRecord:
    """Source placement and local topology anchors."""
    artifact_id: str
    container_id: str = ""
    path: str = ""
    depth: int = 0
    ordinal: int = 0
    parent_artifact_id: Optional[str] = None
    prev_artifact_id: Optional[str] = None
    next_artifact_id: Optional[str] = None


@dataclass
class SemanticRecord:
    """Backend-specific meaning descriptors."""
    artifact_id: str
    semantic_backend: str = SemanticBackend.NONE.value
    feature_blob: bytes = b""
    norm: float = 0.0
    summary_json: str = field(default_factory=lambda: "{}")


@dataclass
class RelationRecord:
    """Typed inter-artifact or cross-dimensional relation."""
    relation_id: str
    from_id: str
    to_id: str
    relation_type: RelationType
    weight: float = 1.0
    metadata_json: str = field(default_factory=lambda: "{}")


# ── Source record (tracks ingested sources) ──────────────────────────

@dataclass
class SourceRecord:
    """Tracks an ingested source."""
    source_id: str
    path: str
    file_hash: str
    ingested_at: str = field(default_factory=_utcnow)
    metadata_json: str = field(default_factory=lambda: "{}")


# ── Projection / query-time types ────────────────────────────────────

@dataclass
class ProjectionNode:
    """A node in the temporary in-memory projection graph."""
    artifact_id: str
    artifact_type: ArtifactType
    score: float = 0.0
    score_components: Dict[str, float] = field(default_factory=dict)
    text_preview: str = ""
    depth: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectionEdge:
    """An edge in the temporary in-memory projection graph."""
    from_id: str
    to_id: str
    relation_type: RelationType
    weight: float = 1.0


@dataclass
class ProjectionGraph:
    """Bounded temporary in-memory manifold assembled at query time."""
    nodes: Dict[str, ProjectionNode] = field(default_factory=dict)
    edges: List[ProjectionEdge] = field(default_factory=list)

    def add_node(self, node: ProjectionNode) -> None:
        self.nodes[node.artifact_id] = node

    def add_edge(self, edge: ProjectionEdge) -> None:
        self.edges.append(edge)

    def neighbors(self, artifact_id: str) -> List[str]:
        """Return IDs of direct neighbors."""
        result: List[str] = []
        for e in self.edges:
            if e.from_id == artifact_id:
                result.append(e.to_id)
            elif e.to_id == artifact_id:
                result.append(e.from_id)
        return result

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)
