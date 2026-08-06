"""
manifold_kernel.lens.profiles — Named lens configuration presets.

Each profile biases the scoring equation toward a different retrieval
strategy.  Profiles are applied by overwriting the default LensConfig
coefficients.
"""

from __future__ import annotations

from typing import Dict

from ..config import LensConfig


# ── Named profiles ───────────────────────────────────────────────────

PROFILES: Dict[str, LensConfig] = {
    "balanced": LensConfig(
        semantic_similarity=0.30,
        structural_proximity=0.25,
        identity_relevance=0.15,
        adjacency_support=0.15,
        exact_match=0.15,
        propagation_decay=0.5,
        neighborhood_density_bonus=0.05,
    ),
    "semantic_heavy": LensConfig(
        semantic_similarity=0.55,
        structural_proximity=0.10,
        identity_relevance=0.10,
        adjacency_support=0.10,
        exact_match=0.15,
        propagation_decay=0.6,
        neighborhood_density_bonus=0.03,
    ),
    "structure_heavy": LensConfig(
        semantic_similarity=0.10,
        structural_proximity=0.50,
        identity_relevance=0.15,
        adjacency_support=0.20,
        exact_match=0.05,
        propagation_decay=0.4,
        neighborhood_density_bonus=0.08,
    ),
    "provenance_heavy": LensConfig(
        semantic_similarity=0.10,
        structural_proximity=0.20,
        identity_relevance=0.40,
        adjacency_support=0.20,
        exact_match=0.10,
        propagation_decay=0.3,
        neighborhood_density_bonus=0.04,
    ),
    "exact_match_heavy": LensConfig(
        semantic_similarity=0.10,
        structural_proximity=0.10,
        identity_relevance=0.10,
        adjacency_support=0.10,
        exact_match=0.60,
        propagation_decay=0.7,
        neighborhood_density_bonus=0.02,
    ),
    "neighborhood_support_heavy": LensConfig(
        semantic_similarity=0.15,
        structural_proximity=0.15,
        identity_relevance=0.10,
        adjacency_support=0.45,
        exact_match=0.15,
        propagation_decay=0.4,
        neighborhood_density_bonus=0.10,
    ),
}


def get_profile(name: str) -> LensConfig:
    """Return a named lens profile, or the balanced default."""
    return PROFILES.get(name, PROFILES["balanced"])


def list_profiles() -> list:
    """Return all available profile names."""
    return sorted(PROFILES.keys())
