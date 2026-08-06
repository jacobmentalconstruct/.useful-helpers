"""bootstrap.py — Phase 1 Bootstrap Nucleus (builder-tunable scaffold scorer).

Ownership: core/nucleus/bootstrap.py

The Bootstrap Nucleus evaluates a pair of HyperHunks and computes:

  RoutingProfile     — per-surface contribution weights {surface: float}, sums to 1.0
  ConnectionStrength — scalar Σ(W_i · S_i) ∈ [0, ∞)
  InteractionType    — dominant mode label + raw similarity vector

This is Phase 1 — deterministic, no learned weights. The scaffold is now
explicitly tunable through BootstrapConfig so probe runs can be reproduced and
builder-side adjustments can be made without hand-editing scorer code.
"""

from __future__ import annotations

import json
import math
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

_SURFACE_ORDER = ["grammatical", "structural", "statistical", "semantic", "verbatim"]
_SURFACE_SET = set(_SURFACE_ORDER)

_STRUCTURED_PROSE_KINDS = {
    "md_code_block",
    "md_table",
}

_INTERACTION_LABELS: Dict[str, str] = {
    "grammatical": "grammatical_dominant",
    "structural": "structural_bridge",
    "statistical": "statistical_echo",
    "semantic": "semantic_resonance",
}


@dataclass
class ExplicitReferenceProfile:
    """Builder-tunable boosts for explicit cross-reference signals."""

    overlap_weight: float = 0.0
    target_hint_bonus: float = 0.0

    @classmethod
    def from_dict(
        cls,
        payload: Dict[str, Any],
        *,
        strict: bool = True,
        base: Optional["ExplicitReferenceProfile"] = None,
    ) -> "ExplicitReferenceProfile":
        allowed = {"overlap_weight", "target_hint_bonus"}
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"Unknown explicit_reference_profile keys: {sorted(unknown)}")
        if strict and set(payload) != allowed:
            missing = sorted(allowed - set(payload))
            raise ValueError(f"Missing explicit_reference_profile keys: {missing}")

        merged = (base.to_dict() if base is not None else cls().to_dict())
        merged.update(payload)
        profile = cls(**merged)
        profile.validate()
        return profile

    def validate(self) -> None:
        for name, value in self.to_dict().items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be numeric")
            if value < 0.0 or value > 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0")

    def to_dict(self) -> Dict[str, float]:
        return {
            "overlap_weight": self.overlap_weight,
            "target_hint_bonus": self.target_hint_bonus,
        }


@dataclass
class GrammaticalMatchProfile:
    """Tiered grammatical match weights used by the bootstrap scaffold."""

    exact_code_kind: float = 1.0
    exact_heading_kind: float = 0.7
    exact_structured_prose_kind: float = 0.532
    exact_generic_prose_kind: float = 0.305
    exact_fragment_kind: float = 0.2
    family_code_kind: float = 0.5
    family_prose_kind: float = 0.1
    family_fragment_kind: float = 0.05

    @classmethod
    def from_dict(
        cls,
        payload: Dict[str, Any],
        *,
        strict: bool = True,
        base: Optional["GrammaticalMatchProfile"] = None,
    ) -> "GrammaticalMatchProfile":
        allowed = {
            "exact_code_kind",
            "exact_heading_kind",
            "exact_structured_prose_kind",
            "exact_generic_prose_kind",
            "exact_fragment_kind",
            "family_code_kind",
            "family_prose_kind",
            "family_fragment_kind",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"Unknown grammatical_match_profile keys: {sorted(unknown)}")
        if strict and set(payload) != allowed:
            missing = sorted(allowed - set(payload))
            raise ValueError(f"Missing grammatical_match_profile keys: {missing}")

        merged = (base.to_dict() if base is not None else cls().to_dict())
        merged.update(payload)
        profile = cls(**merged)
        profile.validate()
        return profile

    def validate(self) -> None:
        for name, value in self.to_dict().items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be numeric")
            if value < 0.0 or value > 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0")

    def to_dict(self) -> Dict[str, float]:
        return {
            "exact_code_kind": self.exact_code_kind,
            "exact_heading_kind": self.exact_heading_kind,
            "exact_structured_prose_kind": self.exact_structured_prose_kind,
            "exact_generic_prose_kind": self.exact_generic_prose_kind,
            "exact_fragment_kind": self.exact_fragment_kind,
            "family_code_kind": self.family_code_kind,
            "family_prose_kind": self.family_prose_kind,
            "family_fragment_kind": self.family_fragment_kind,
        }


@dataclass
class BootstrapConfig:
    """Builder-tunable configuration for the Phase 1 scaffold nucleus."""

    edge_threshold: float = 0.3
    dominance_threshold: float = 0.40
    surface_fractions: Dict[str, float] = field(default_factory=lambda: {
        "grammatical": 0.35,
        "structural": 0.25,
        "statistical": 0.20,
        "semantic": 0.15,
        "verbatim": 0.05,
    })
    grammatical_match_profile: GrammaticalMatchProfile = field(
        default_factory=GrammaticalMatchProfile
    )
    explicit_reference_profile: ExplicitReferenceProfile = field(
        default_factory=ExplicitReferenceProfile
    )
    semantic_absent_threshold_scale: float = 1.0

    @classmethod
    def default(cls) -> "BootstrapConfig":
        config = cls()
        config.validate()
        return config

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "BootstrapConfig":
        allowed = {
            "edge_threshold",
            "dominance_threshold",
            "surface_fractions",
            "grammatical_match_profile",
            "explicit_reference_profile",
            "semantic_absent_threshold_scale",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise ValueError(f"Unknown bootstrap config keys: {sorted(unknown)}")
        if set(payload) != allowed:
            missing = sorted(allowed - set(payload))
            raise ValueError(f"Missing bootstrap config keys: {missing}")

        fractions = payload["surface_fractions"]
        if not isinstance(fractions, dict):
            raise ValueError("surface_fractions must be an object")

        match_profile = payload["grammatical_match_profile"]
        if not isinstance(match_profile, dict):
            raise ValueError("grammatical_match_profile must be an object")
        explicit_reference_profile = payload["explicit_reference_profile"]
        if not isinstance(explicit_reference_profile, dict):
            raise ValueError("explicit_reference_profile must be an object")

        config = cls(
            edge_threshold=float(payload["edge_threshold"]),
            dominance_threshold=float(payload["dominance_threshold"]),
            surface_fractions={str(k): float(v) for k, v in fractions.items()},
            grammatical_match_profile=GrammaticalMatchProfile.from_dict(match_profile, strict=True),
            explicit_reference_profile=ExplicitReferenceProfile.from_dict(
                explicit_reference_profile,
                strict=True,
            ),
            semantic_absent_threshold_scale=float(payload["semantic_absent_threshold_scale"]),
        )
        config.validate()
        return config

    def with_overrides(self, overrides: Dict[str, Any]) -> "BootstrapConfig":
        allowed = {
            "edge_threshold",
            "dominance_threshold",
            "surface_fractions",
            "grammatical_match_profile",
            "explicit_reference_profile",
            "semantic_absent_threshold_scale",
        }
        unknown = set(overrides) - allowed
        if unknown:
            raise ValueError(f"Unknown bootstrap override keys: {sorted(unknown)}")

        payload = self.to_dict()
        if "edge_threshold" in overrides:
            payload["edge_threshold"] = float(overrides["edge_threshold"])
        if "dominance_threshold" in overrides:
            payload["dominance_threshold"] = float(overrides["dominance_threshold"])
        if "semantic_absent_threshold_scale" in overrides:
            payload["semantic_absent_threshold_scale"] = float(
                overrides["semantic_absent_threshold_scale"]
            )
        if "surface_fractions" in overrides:
            fraction_patch = overrides["surface_fractions"]
            if not isinstance(fraction_patch, dict):
                raise ValueError("surface_fractions override must be an object")
            unknown_fractions = set(fraction_patch) - _SURFACE_SET
            if unknown_fractions:
                raise ValueError(
                    f"Unknown surface_fractions keys: {sorted(unknown_fractions)}"
                )
            payload["surface_fractions"].update({
                str(k): float(v) for k, v in fraction_patch.items()
            })
        if "grammatical_match_profile" in overrides:
            match_patch = overrides["grammatical_match_profile"]
            if not isinstance(match_patch, dict):
                raise ValueError("grammatical_match_profile override must be an object")
            payload["grammatical_match_profile"] = GrammaticalMatchProfile.from_dict(
                match_patch,
                strict=False,
                base=self.grammatical_match_profile,
            ).to_dict()
        if "explicit_reference_profile" in overrides:
            ref_patch = overrides["explicit_reference_profile"]
            if not isinstance(ref_patch, dict):
                raise ValueError("explicit_reference_profile override must be an object")
            payload["explicit_reference_profile"] = ExplicitReferenceProfile.from_dict(
                ref_patch,
                strict=False,
                base=self.explicit_reference_profile,
            ).to_dict()

        return BootstrapConfig.from_dict(payload)

    def validate(self) -> None:
        if self.edge_threshold < 0.0:
            raise ValueError("edge_threshold must be >= 0.0")
        if self.dominance_threshold < 0.0 or self.dominance_threshold > 1.0:
            raise ValueError("dominance_threshold must be between 0.0 and 1.0")
        if self.semantic_absent_threshold_scale <= 0.0:
            raise ValueError("semantic_absent_threshold_scale must be > 0.0")

        keys = set(self.surface_fractions)
        if keys != _SURFACE_SET:
            missing = sorted(_SURFACE_SET - keys)
            extra = sorted(keys - _SURFACE_SET)
            detail = []
            if missing:
                detail.append(f"missing={missing}")
            if extra:
                detail.append(f"extra={extra}")
            raise ValueError(
                "surface_fractions must contain exactly "
                f"{sorted(_SURFACE_SET)} ({', '.join(detail)})"
            )
        total = 0.0
        for name, value in self.surface_fractions.items():
            if value < 0.0:
                raise ValueError(f"surface_fractions.{name} must be >= 0.0")
            total += value
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"surface_fractions must sum to 1.0 (got {round(total, 8)})"
            )

        self.grammatical_match_profile.validate()
        self.explicit_reference_profile.validate()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_threshold": self.edge_threshold,
            "dominance_threshold": self.dominance_threshold,
            "surface_fractions": dict(self.surface_fractions),
            "grammatical_match_profile": self.grammatical_match_profile.to_dict(),
            "explicit_reference_profile": self.explicit_reference_profile.to_dict(),
            "semantic_absent_threshold_scale": self.semantic_absent_threshold_scale,
        }

    def save_json(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")


@dataclass
class NucleusResult:
    """Outputs of a single Nucleus evaluation over a hunk pair."""

    connection_strength: float
    routing_profile: Dict[str, float]
    interaction_type: str
    interaction_vector: List[float]
    above_threshold: bool


def _jaccard(set_a: set, set_b: set) -> float:
    """Symmetric Jaccard similarity between two sets."""
    union = len(set_a | set_b)
    if union == 0:
        return 0.0
    return len(set_a & set_b) / union


def _has_embedding(hunk: Any) -> bool:
    embedding = getattr(hunk, "embedding", None)
    return embedding is not None and bool(embedding)


def _is_fragment_kind(node_kind: str) -> bool:
    return node_kind.startswith("fragment_of_")


def _is_heading_kind(node_kind: str) -> bool:
    return node_kind == "md_heading"


def _is_structured_prose_kind(node_kind: str, is_subtype_fn: Any) -> bool:
    return is_subtype_fn(node_kind, "prose_node") and node_kind in _STRUCTURED_PROSE_KINDS


def _is_generic_prose_kind(node_kind: str, is_subtype_fn: Any) -> bool:
    return is_subtype_fn(node_kind, "prose_node") and not _is_heading_kind(node_kind) and not _is_structured_prose_kind(node_kind, is_subtype_fn)


def _grammatical_similarity(
    a: Any,
    b: Any,
    match_profile: GrammaticalMatchProfile,
) -> float:
    """Grammatical affinity: type family, decorators, base classes."""
    from ..contract.ontology import is_subtype

    if a.node_kind == b.node_kind:
        if is_subtype(a.node_kind, "code_node"):
            kind_sim = match_profile.exact_code_kind
        elif _is_heading_kind(a.node_kind):
            kind_sim = match_profile.exact_heading_kind
        elif _is_fragment_kind(a.node_kind) or is_subtype(a.node_kind, "fragment_node"):
            kind_sim = match_profile.exact_fragment_kind
        elif _is_structured_prose_kind(a.node_kind, is_subtype):
            kind_sim = match_profile.exact_structured_prose_kind
        elif _is_generic_prose_kind(a.node_kind, is_subtype):
            kind_sim = match_profile.exact_generic_prose_kind
        else:
            kind_sim = match_profile.exact_generic_prose_kind
    elif is_subtype(a.node_kind, "code_node") and is_subtype(b.node_kind, "code_node"):
        kind_sim = match_profile.family_code_kind
    elif is_subtype(a.node_kind, "prose_node") and is_subtype(b.node_kind, "prose_node"):
        kind_sim = match_profile.family_prose_kind
    elif (
        _is_fragment_kind(a.node_kind)
        or is_subtype(a.node_kind, "fragment_node")
    ) and (
        _is_fragment_kind(b.node_kind)
        or is_subtype(b.node_kind, "fragment_node")
    ):
        kind_sim = match_profile.family_fragment_kind
    else:
        kind_sim = 0.0

    dec_sim = _jaccard(set(a.decorators), set(b.decorators))
    bc_sim = _jaccard(set(a.base_classes), set(b.base_classes))
    return kind_sim * 0.6 + dec_sim * 0.2 + bc_sim * 0.2


def _structural_similarity(a: Any, b: Any) -> float:
    """Structural affinity: path hierarchy, scope stack, heading trail."""
    a_parts = [p for p in a.structural_path.split("/") if p]
    b_parts = [p for p in b.structural_path.split("/") if p]
    if a_parts and b_parts:
        common = sum(1 for x, y in zip(a_parts, b_parts) if x == y)
        path_sim = common / max(len(a_parts), len(b_parts))
    elif not a_parts and not b_parts:
        path_sim = 1.0
    else:
        path_sim = 0.0

    scope_sim = _jaccard(set(a.scope_stack), set(b.scope_stack))
    head_sim = _jaccard(set(a.heading_trail), set(b.heading_trail))

    return path_sim * 0.5 + scope_sim * 0.3 + head_sim * 0.2


def _normalize_reference_tokens(values: List[str]) -> set[str]:
    tokens: set[str] = set()
    for raw in values:
        text = str(raw).strip().lower().replace("\\", "/")
        if not text:
            continue
        candidates = {text}
        if "#" in text:
            left, right = text.split("#", 1)
            if left:
                candidates.add(left)
            if right:
                candidates.add(right)
        tail = text.rsplit("/", 1)[-1]
        if tail:
            candidates.add(tail)
        for candidate in list(candidates):
            if candidate.endswith((".txt", ".md", ".rst")):
                candidates.add(candidate.rsplit(".", 1)[0])
        for candidate in candidates:
            cleaned = candidate.strip(" ./")
            if cleaned:
                tokens.add(cleaned)
    return tokens


def _target_hint_tokens(hunk: Any) -> set[str]:
    tokens: set[str] = set()
    origin_text = str(getattr(hunk, "origin_id", "")).lower().replace("\\", "/")
    if origin_text:
        tail = origin_text.rsplit("/", 1)[-1]
        if tail:
            tokens.add(tail)
        stem = Path(tail).stem if tail else ""
        if stem:
            tokens.add(stem)
    structural_path = str(getattr(hunk, "structural_path", "")).lower()
    if structural_path:
        for part in structural_path.split("/"):
            part = part.strip()
            if part:
                tokens.add(part)
    for heading in getattr(hunk, "heading_trail", []):
        heading_text = str(heading).strip().lower()
        if heading_text:
            tokens.add(heading_text)
            slug = "".join(ch if ch.isalnum() else "_" for ch in heading_text).strip("_")
            if slug:
                tokens.add(slug)
    return tokens


def _explicit_reference_signal(
    a: Any,
    b: Any,
    profile: ExplicitReferenceProfile,
) -> float:
    if profile.overlap_weight <= 0.0 and profile.target_hint_bonus <= 0.0:
        return 0.0

    a_raw_refs = list(getattr(a, "cross_refs", []) or [])
    b_raw_refs = list(getattr(b, "cross_refs", []) or [])
    a_norm_refs = list(getattr(a, "normalized_cross_refs", []) or [])
    b_norm_refs = list(getattr(b, "normalized_cross_refs", []) or [])
    a_refs = _normalize_reference_tokens(a_raw_refs + a_norm_refs)
    b_refs = _normalize_reference_tokens(b_raw_refs + b_norm_refs)
    overlap = _jaccard(a_refs, b_refs)

    hit = 0.0
    if profile.target_hint_bonus > 0.0:
        a_targets = _target_hint_tokens(a)
        b_targets = _target_hint_tokens(b)
        if (a_refs and a_refs & b_targets) or (b_refs and b_refs & a_targets):
            hit = 1.0

    return min(
        1.0,
        profile.overlap_weight * overlap + profile.target_hint_bonus * hit,
    )


def _statistical_similarity(a: Any, b: Any) -> float:
    """Statistical affinity: token count ratio + content token Jaccard."""
    if a.token_count > 0 and b.token_count > 0:
        tc_sim = min(a.token_count, b.token_count) / max(a.token_count, b.token_count)
    else:
        tc_sim = 0.5

    a_words = set(a.content.lower().split())
    b_words = set(b.content.lower().split())
    word_sim = _jaccard(a_words, b_words)

    return tc_sim * 0.3 + word_sim * 0.7


def _semantic_similarity(a: Any, b: Any) -> float:
    """Semantic affinity: cosine similarity over embedding vectors."""
    a_emb: Optional[List[float]] = getattr(a, "embedding", None)
    b_emb: Optional[List[float]] = getattr(b, "embedding", None)
    if a_emb is None or b_emb is None:
        return 0.0
    if not a_emb or not b_emb:
        return 0.0

    dot = sum(x * y for x, y in zip(a_emb, b_emb))
    na = math.sqrt(sum(x * x for x in a_emb))
    nb = math.sqrt(sum(x * x for x in b_emb))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return max(0.0, dot / (na * nb))


def _verbatim_similarity(a: Any, b: Any) -> float:
    """Verbatim affinity: substring containment + word Jaccard (case-sensitive)."""
    if not a.content or not b.content:
        contain_sim = 0.0
    else:
        short, long_c = (
            (a.content, b.content)
            if len(a.content) <= len(b.content)
            else (b.content, a.content)
        )
        if short in long_c:
            contain_sim = len(short) / max(len(long_c), 1)
        else:
            contain_sim = 0.0

    word_sim = _jaccard(set(a.content.split()), set(b.content.split()))
    return contain_sim * 0.5 + word_sim * 0.5


class BootstrapNucleus:
    """Phase 1 deterministic Nucleus using explicit scaffold tuning config."""

    def __init__(
        self,
        config: Optional[BootstrapConfig] = None,
        *,
        edge_threshold: Optional[float] = None,
        dominance_threshold: Optional[float] = None,
    ) -> None:
        resolved = config if config is not None else BootstrapConfig.default()
        if edge_threshold is not None:
            resolved = resolved.with_overrides({"edge_threshold": edge_threshold})
        if dominance_threshold is not None:
            resolved = resolved.with_overrides({"dominance_threshold": dominance_threshold})
        resolved.validate()
        self.config = resolved

    @property
    def edge_threshold(self) -> float:
        return self.config.edge_threshold

    def _effective_edge_threshold(self, a: Any, b: Any) -> float:
        if not _has_embedding(a) and not _has_embedding(b):
            return self.config.edge_threshold * self.config.semantic_absent_threshold_scale
        return self.config.edge_threshold

    def evaluate(self, a: Any, b: Any) -> NucleusResult:
        from ..contract.ontology import get_coupling

        w_base = (get_coupling(a.node_kind) + get_coupling(b.node_kind)) / 2.0
        sims: Dict[str, float] = {
            "grammatical": _grammatical_similarity(
                a, b, self.config.grammatical_match_profile
            ),
            "structural": min(
                1.0,
                _structural_similarity(a, b)
                + _explicit_reference_signal(
                    a,
                    b,
                    self.config.explicit_reference_profile,
                ),
            ),
            "statistical": _statistical_similarity(a, b),
            "semantic": _semantic_similarity(a, b),
            "verbatim": _verbatim_similarity(a, b),
        }

        contributions: Dict[str, float] = {
            surface: w_base * self.config.surface_fractions[surface] * sims[surface]
            for surface in _SURFACE_ORDER
        }
        connection_strength = sum(contributions.values())

        if connection_strength > 0.0:
            routing_profile = {
                surface: round(contributions[surface] / connection_strength, 4)
                for surface in _SURFACE_ORDER
            }
        else:
            routing_profile = {surface: 0.0 for surface in _SURFACE_ORDER}

        max_surface = max(routing_profile, key=routing_profile.__getitem__)
        max_share = routing_profile[max_surface]
        if max_share >= self.config.dominance_threshold:
            interaction_type = _INTERACTION_LABELS.get(max_surface, "multi_surface")
        else:
            interaction_type = "multi_surface"

        interaction_vector = [sims[surface] for surface in _SURFACE_ORDER]
        effective_threshold = self._effective_edge_threshold(a, b)

        return NucleusResult(
            connection_strength=connection_strength,
            routing_profile=routing_profile,
            interaction_type=interaction_type,
            interaction_vector=interaction_vector,
            above_threshold=connection_strength >= effective_threshold,
        )

    def batch_evaluate(
        self,
        hunks: List[Any],
        max_window: int = 50,
    ) -> List[Tuple[str, str, NucleusResult]]:
        results: List[Tuple[str, str, NucleusResult]] = []
        for i, b in enumerate(hunks):
            start = max(0, i - max_window)
            for a in hunks[start:i]:
                results.append((a.occurrence_id, b.occurrence_id, self.evaluate(a, b)))
        return results
