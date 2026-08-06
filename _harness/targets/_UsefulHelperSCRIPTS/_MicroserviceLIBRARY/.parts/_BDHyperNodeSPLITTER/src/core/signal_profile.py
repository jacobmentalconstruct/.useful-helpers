"""Builder-tunable Splitter signal profile.

This profile is owned by the Splitter and controls only extraction and
enrichment behavior. It does not contain graph-scoring or Emitter logic.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict


def _require_numeric(name: str, value: Any, *, minimum: float | None = None) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    numeric = float(value)
    if minimum is not None and numeric < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return numeric


def _require_bool(name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


@dataclass
class StructuredTextProfile:
    txt_promotion_sensitivity: float = 1.0
    list_heavy_threshold: int = 3
    indented_block_threshold: int = 5
    heading_pair_threshold: int = 2

    @classmethod
    def from_dict(
        cls,
        payload: Dict[str, Any],
        *,
        strict: bool = True,
        base: "StructuredTextProfile | None" = None,
    ) -> "StructuredTextProfile":
        allowed = {
            "txt_promotion_sensitivity",
            "list_heavy_threshold",
            "indented_block_threshold",
            "heading_pair_threshold",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"Unknown structured_text_profile keys: {sorted(unknown)}")
        if strict and set(payload) != allowed:
            missing = sorted(allowed - set(payload))
            raise ValueError(f"Missing structured_text_profile keys: {missing}")

        merged = (base.to_dict() if base is not None else cls().to_dict())
        merged.update(payload)
        profile = cls(
            txt_promotion_sensitivity=float(merged["txt_promotion_sensitivity"]),
            list_heavy_threshold=int(merged["list_heavy_threshold"]),
            indented_block_threshold=int(merged["indented_block_threshold"]),
            heading_pair_threshold=int(merged["heading_pair_threshold"]),
        )
        profile.validate()
        return profile

    def validate(self) -> None:
        _require_numeric("txt_promotion_sensitivity", self.txt_promotion_sensitivity, minimum=0.1)
        if self.list_heavy_threshold < 1:
            raise ValueError("list_heavy_threshold must be >= 1")
        if self.indented_block_threshold < 1:
            raise ValueError("indented_block_threshold must be >= 1")
        if self.heading_pair_threshold < 1:
            raise ValueError("heading_pair_threshold must be >= 1")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "txt_promotion_sensitivity": self.txt_promotion_sensitivity,
            "list_heavy_threshold": self.list_heavy_threshold,
            "indented_block_threshold": self.indented_block_threshold,
            "heading_pair_threshold": self.heading_pair_threshold,
        }


@dataclass
class ReferenceExtractionProfile:
    enabled: bool = True
    normalization_mode: str = "python_reference_v1"
    minimum_reference_quality: float = 0.35
    keep_raw_refs: bool = True

    @classmethod
    def from_dict(
        cls,
        payload: Dict[str, Any],
        *,
        strict: bool = True,
        base: "ReferenceExtractionProfile | None" = None,
    ) -> "ReferenceExtractionProfile":
        allowed = {
            "enabled",
            "normalization_mode",
            "minimum_reference_quality",
            "keep_raw_refs",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"Unknown reference_extraction_profile keys: {sorted(unknown)}")
        if strict and set(payload) != allowed:
            missing = sorted(allowed - set(payload))
            raise ValueError(f"Missing reference_extraction_profile keys: {missing}")

        merged = (base.to_dict() if base is not None else cls().to_dict())
        merged.update(payload)
        profile = cls(
            enabled=bool(merged["enabled"]),
            normalization_mode=str(merged["normalization_mode"]),
            minimum_reference_quality=float(merged["minimum_reference_quality"]),
            keep_raw_refs=bool(merged["keep_raw_refs"]),
        )
        profile.validate()
        return profile

    def validate(self) -> None:
        _require_bool("enabled", self.enabled)
        if self.normalization_mode not in {"python_reference_v1", "none"}:
            raise ValueError("normalization_mode must be 'python_reference_v1' or 'none'")
        _require_numeric("minimum_reference_quality", self.minimum_reference_quality, minimum=0.0)
        if self.minimum_reference_quality > 1.0:
            raise ValueError("minimum_reference_quality must be <= 1.0")
        _require_bool("keep_raw_refs", self.keep_raw_refs)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "normalization_mode": self.normalization_mode,
            "minimum_reference_quality": self.minimum_reference_quality,
            "keep_raw_refs": self.keep_raw_refs,
        }


@dataclass
class ListRepresentationProfile:
    emit_list_items: bool = False
    max_list_item_length: int = 320
    preserve_markers: bool = True
    inherit_heading_ancestry: bool = True

    @classmethod
    def from_dict(
        cls,
        payload: Dict[str, Any],
        *,
        strict: bool = True,
        base: "ListRepresentationProfile | None" = None,
    ) -> "ListRepresentationProfile":
        allowed = {
            "emit_list_items",
            "max_list_item_length",
            "preserve_markers",
            "inherit_heading_ancestry",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"Unknown list_representation_profile keys: {sorted(unknown)}")
        if strict and set(payload) != allowed:
            missing = sorted(allowed - set(payload))
            raise ValueError(f"Missing list_representation_profile keys: {missing}")

        merged = (base.to_dict() if base is not None else cls().to_dict())
        merged.update(payload)
        profile = cls(
            emit_list_items=bool(merged["emit_list_items"]),
            max_list_item_length=int(merged["max_list_item_length"]),
            preserve_markers=bool(merged["preserve_markers"]),
            inherit_heading_ancestry=bool(merged["inherit_heading_ancestry"]),
        )
        profile.validate()
        return profile

    def validate(self) -> None:
        _require_bool("emit_list_items", self.emit_list_items)
        if self.max_list_item_length < 32:
            raise ValueError("max_list_item_length must be >= 32")
        _require_bool("preserve_markers", self.preserve_markers)
        _require_bool("inherit_heading_ancestry", self.inherit_heading_ancestry)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "emit_list_items": self.emit_list_items,
            "max_list_item_length": self.max_list_item_length,
            "preserve_markers": self.preserve_markers,
            "inherit_heading_ancestry": self.inherit_heading_ancestry,
        }


@dataclass
class FragmentInheritanceProfile:
    inherit_full_reference_context: bool = True
    keep_parent_node_kind_family: bool = True
    context_window_retain_ratio: float = 1.0

    @classmethod
    def from_dict(
        cls,
        payload: Dict[str, Any],
        *,
        strict: bool = True,
        base: "FragmentInheritanceProfile | None" = None,
    ) -> "FragmentInheritanceProfile":
        allowed = {
            "inherit_full_reference_context",
            "keep_parent_node_kind_family",
            "context_window_retain_ratio",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"Unknown fragment_inheritance_profile keys: {sorted(unknown)}")
        if strict and set(payload) != allowed:
            missing = sorted(allowed - set(payload))
            raise ValueError(f"Missing fragment_inheritance_profile keys: {missing}")

        merged = (base.to_dict() if base is not None else cls().to_dict())
        merged.update(payload)
        profile = cls(
            inherit_full_reference_context=bool(merged["inherit_full_reference_context"]),
            keep_parent_node_kind_family=bool(merged["keep_parent_node_kind_family"]),
            context_window_retain_ratio=float(merged["context_window_retain_ratio"]),
        )
        profile.validate()
        return profile

    def validate(self) -> None:
        _require_bool("inherit_full_reference_context", self.inherit_full_reference_context)
        _require_bool("keep_parent_node_kind_family", self.keep_parent_node_kind_family)
        ratio = _require_numeric(
            "context_window_retain_ratio",
            self.context_window_retain_ratio,
            minimum=0.0,
        )
        if ratio > 1.0:
            raise ValueError("context_window_retain_ratio must be <= 1.0")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inherit_full_reference_context": self.inherit_full_reference_context,
            "keep_parent_node_kind_family": self.keep_parent_node_kind_family,
            "context_window_retain_ratio": self.context_window_retain_ratio,
        }


@dataclass
class SplitterSignalProfile:
    structured_text_profile: StructuredTextProfile = field(default_factory=StructuredTextProfile)
    reference_extraction_profile: ReferenceExtractionProfile = field(
        default_factory=ReferenceExtractionProfile
    )
    list_representation_profile: ListRepresentationProfile = field(
        default_factory=ListRepresentationProfile
    )
    fragment_inheritance_profile: FragmentInheritanceProfile = field(
        default_factory=FragmentInheritanceProfile
    )

    @classmethod
    def default(cls) -> "SplitterSignalProfile":
        profile = cls()
        profile.validate()
        return profile

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "SplitterSignalProfile":
        allowed = {
            "structured_text_profile",
            "reference_extraction_profile",
            "list_representation_profile",
            "fragment_inheritance_profile",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"Unknown splitter signal profile keys: {sorted(unknown)}")
        if set(payload) != allowed:
            missing = sorted(allowed - set(payload))
            raise ValueError(f"Missing splitter signal profile keys: {missing}")

        profile = cls(
            structured_text_profile=StructuredTextProfile.from_dict(
                payload["structured_text_profile"],
                strict=True,
            ),
            reference_extraction_profile=ReferenceExtractionProfile.from_dict(
                payload["reference_extraction_profile"],
                strict=True,
            ),
            list_representation_profile=ListRepresentationProfile.from_dict(
                payload["list_representation_profile"],
                strict=True,
            ),
            fragment_inheritance_profile=FragmentInheritanceProfile.from_dict(
                payload["fragment_inheritance_profile"],
                strict=True,
            ),
        )
        profile.validate()
        return profile

    @classmethod
    def load_json(cls, path: str | Path) -> "SplitterSignalProfile":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Splitter signal profile JSON must be an object")
        return cls.from_dict(payload)

    def validate(self) -> None:
        self.structured_text_profile.validate()
        self.reference_extraction_profile.validate()
        self.list_representation_profile.validate()
        self.fragment_inheritance_profile.validate()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "structured_text_profile": self.structured_text_profile.to_dict(),
            "reference_extraction_profile": self.reference_extraction_profile.to_dict(),
            "list_representation_profile": self.list_representation_profile.to_dict(),
            "fragment_inheritance_profile": self.fragment_inheritance_profile.to_dict(),
        }

    def save_json(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
