"""HyperHunk v2 — Splitter-local wire-format contract.

This is the Splitter's owned copy of the Phase 1 HyperHunk contract.
It intentionally does not import from ``final/contract`` at runtime, so the
project can run as a self-contained component from its own folder.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class HyperHunk:
    """A content-addressed, structurally-aware, richly-contextual text hunk."""

    content: str
    origin_id: str
    layer_type: str
    node_kind: str

    structural_path: str = ""
    sibling_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_occurrence_id: Optional[str] = None
    prev_sibling_occurrence_id: Optional[str] = None

    scope_stack: List[str] = field(default_factory=list)
    scope_docstrings: Dict[str, str] = field(default_factory=dict)
    base_classes: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    import_context: List[str] = field(default_factory=list)

    heading_trail: List[str] = field(default_factory=list)
    cross_refs: List[str] = field(default_factory=list)
    normalized_cross_refs: List[str] = field(default_factory=list)
    reference_kinds: List[str] = field(default_factory=list)
    list_role: str = ""
    list_depth: int = 0
    reference_confidence: float = 0.0

    context_window: str = ""
    sibling_count: int = 0
    document_position: float = 0.0

    token_count: int = 0
    split_reason: str = ""

    extraction_engine: str = ""
    extraction_confidence: float = 1.0

    hunk_id: str = field(init=False, repr=True)
    occurrence_id: str = field(init=False, repr=True)

    def __post_init__(self) -> None:
        content_payload = f"{self.node_kind}:{self.content}"
        self.hunk_id = hashlib.sha256(content_payload.encode()).hexdigest()

        occurrence_payload = (
            f"{self.origin_id}:{self.structural_path}:"
            f"{self.sibling_index}:{self.hunk_id}"
        )
        self.occurrence_id = hashlib.sha256(
            occurrence_payload.encode()
        ).hexdigest()

    def __len__(self) -> int:
        return len(self.content)

    @property
    def verbatim_surface(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "origin_id": self.origin_id,
        }

    @property
    def structural_surface(self) -> Dict[str, Any]:
        return {
            "structural_path": self.structural_path,
            "sibling_index": self.sibling_index,
            "parent_occurrence_id": self.parent_occurrence_id,
            "prev_sibling_occurrence_id": self.prev_sibling_occurrence_id,
            "scope_stack": self.scope_stack,
            "heading_trail": self.heading_trail,
            "document_position": self.document_position,
            "sibling_count": self.sibling_count,
        }

    @property
    def grammatical_surface(self) -> Dict[str, Any]:
        return {
            "node_kind": self.node_kind,
            "layer_type": self.layer_type,
            "decorators": self.decorators,
            "base_classes": self.base_classes,
            "import_context": self.import_context,
            "scope_docstrings": self.scope_docstrings,
            "cross_refs": self.cross_refs,
            "normalized_cross_refs": self.normalized_cross_refs,
            "reference_kinds": self.reference_kinds,
            "list_role": self.list_role,
            "list_depth": self.list_depth,
            "reference_confidence": self.reference_confidence,
        }

    @property
    def statistical_surface(self) -> Dict[str, Any]:
        return {
            "token_count": self.token_count,
            "context_window": self.context_window,
            "split_reason": self.split_reason,
            "extraction_engine": self.extraction_engine,
            "extraction_confidence": self.extraction_confidence,
        }

    @property
    def semantic_surface(self) -> Dict[str, Any]:
        return {}

    @property
    def surfaces(self) -> Dict[str, Dict[str, Any]]:
        return {
            "verbatim": self.verbatim_surface,
            "structural": self.structural_surface,
            "grammatical": self.grammatical_surface,
            "statistical": self.statistical_surface,
            "semantic": self.semantic_surface,
        }

    def surface_richness(self) -> Dict[str, float]:
        defaults: Dict[str, Any] = {
            "structural_path": "",
            "sibling_index": 0,
            "parent_occurrence_id": None,
            "prev_sibling_occurrence_id": None,
            "scope_stack": [],
            "heading_trail": [],
            "document_position": 0.0,
            "sibling_count": 0,
            "decorators": [],
            "base_classes": [],
            "import_context": [],
            "scope_docstrings": {},
            "cross_refs": [],
            "normalized_cross_refs": [],
            "reference_kinds": [],
            "list_role": "",
            "list_depth": 0,
            "reference_confidence": 0.0,
            "token_count": 0,
            "context_window": "",
            "split_reason": "",
            "extraction_engine": "",
            "extraction_confidence": 1.0,
        }
        result = {}
        for name, surface in self.surfaces.items():
            if name == "verbatim":
                result[name] = 1.0
                continue
            if name == "semantic":
                result[name] = 0.0
                continue
            total = len(surface)
            if total == 0:
                result[name] = 0.0
                continue
            populated = sum(
                1 for key, value in surface.items()
                if value != defaults.get(key, value)
            )
            result[name] = round(populated / total, 2)
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "origin_id": self.origin_id,
            "layer_type": self.layer_type,
            "node_kind": self.node_kind,
            "structural_path": self.structural_path,
            "sibling_index": self.sibling_index,
            "parent_occurrence_id": self.parent_occurrence_id,
            "prev_sibling_occurrence_id": self.prev_sibling_occurrence_id,
            "metadata": self.metadata,
            "scope_stack": self.scope_stack,
            "scope_docstrings": self.scope_docstrings,
            "base_classes": self.base_classes,
            "decorators": self.decorators,
            "import_context": self.import_context,
            "heading_trail": self.heading_trail,
            "cross_refs": self.cross_refs,
            "normalized_cross_refs": self.normalized_cross_refs,
            "reference_kinds": self.reference_kinds,
            "list_role": self.list_role,
            "list_depth": self.list_depth,
            "reference_confidence": self.reference_confidence,
            "context_window": self.context_window,
            "sibling_count": self.sibling_count,
            "document_position": self.document_position,
            "token_count": self.token_count,
            "split_reason": self.split_reason,
            "extraction_engine": self.extraction_engine,
            "extraction_confidence": self.extraction_confidence,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "HyperHunk":
        return cls(
            content=d["content"],
            origin_id=d["origin_id"],
            layer_type=d["layer_type"],
            node_kind=d["node_kind"],
            structural_path=d.get("structural_path", ""),
            sibling_index=d.get("sibling_index", 0),
            metadata=d.get("metadata", {}),
            parent_occurrence_id=d.get("parent_occurrence_id"),
            prev_sibling_occurrence_id=d.get("prev_sibling_occurrence_id"),
            scope_stack=d.get("scope_stack", []),
            scope_docstrings=d.get("scope_docstrings", {}),
            base_classes=d.get("base_classes", []),
            decorators=d.get("decorators", []),
            import_context=d.get("import_context", []),
            heading_trail=d.get("heading_trail", []),
            cross_refs=d.get("cross_refs", []),
            normalized_cross_refs=d.get("normalized_cross_refs", []),
            reference_kinds=d.get("reference_kinds", []),
            list_role=d.get("list_role", ""),
            list_depth=d.get("list_depth", 0),
            reference_confidence=d.get("reference_confidence", 0.0),
            context_window=d.get("context_window", ""),
            sibling_count=d.get("sibling_count", 0),
            document_position=d.get("document_position", 0.0),
            token_count=d.get("token_count", 0),
            split_reason=d.get("split_reason", ""),
            extraction_engine=d.get("extraction_engine", ""),
            extraction_confidence=d.get("extraction_confidence", 1.0),
        )
