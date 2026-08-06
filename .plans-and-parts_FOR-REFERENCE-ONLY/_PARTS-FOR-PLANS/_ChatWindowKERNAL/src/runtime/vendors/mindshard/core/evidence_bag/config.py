"""
Configuration and preset modes for the Evidence Bag system.

All tunable dials from the design docs live here. RuntimeMode presets
configure the full pipeline in one shot. Individual values can be
overridden after selecting a preset.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict


class PackingStrategy(Enum):
    GREEDY_DENSITY = "greedy_density"
    KNAPSACK_OPT = "knapsack_opt"


class OversizePolicy(Enum):
    STRICT = "strict"
    TRUNCATE = "truncate"
    FOCUS_EXTRACT = "focus_extract"


class RedundancyStrength(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ---------------------------------------------------------------------------
# Kind multipliers (from scoring doc §4)
# ---------------------------------------------------------------------------

KIND_MULTIPLIERS: Dict[str, float] = {
    "goal": 1.20,
    "memory": 1.00,
    "knowledge": 1.00,
    "tool_result": 0.45,
    "default": 0.90,
}

# Answer-kind multipliers gated by trust state (scoring doc §4)
ANSWER_TRUST_MULTIPLIERS: Dict[str, float] = {
    "normal": 0.35,
    "weak": 0.18,
    "unverified": 0.16,
    "error": 0.10,
    "untagged": 0.12,
    "superseded": 0.06,
}

# ---------------------------------------------------------------------------
# Noise penalties (from scoring doc §5)
# ---------------------------------------------------------------------------

TAG_NOISE_PENALTIES: Dict[str, float] = {
    "error": 14.0,
    "weak-evidence": 18.0,
    "degraded": 8.0,
    "semantic-zero": 8.0,
    "superseded": 28.0,
}

ANSWER_NOISE_PENALTIES: Dict[str, float] = {
    "legacy": 12.0,
    "weak": 10.0,
    "unverified": 8.0,
    "error": 16.0,
}

CONTENT_NOISE_PENALTIES = {
    "traceback": 12.0,
    "long_content_threshold": 1200,
    "long_content_penalty": 6.0,
}


# ---------------------------------------------------------------------------
# Composition config (from composition + runtime policy docs)
# ---------------------------------------------------------------------------

@dataclass
class CompositionConfig:
    """
    All tunable dials for evidence bag assembly.

    This is the single configuration object passed through the pipeline.
    Presets set all values; callers can override individual fields after.
    """

    # --- Category budget ratios (must sum to 1.0) ---
    goal_ratio: float = 0.25
    memory_ratio: float = 0.30
    knowledge_ratio: float = 0.35
    neighbor_ratio: float = 0.10

    # --- Length pressure ---
    alpha: float = 1.10           # exponent on content length in item_weight
    base_cost: float = 100.0      # additive constant in item_weight

    # --- Neighbor expansion ---
    neighbor_beta: float = 0.30   # propagation factor: neighbor_score = beta * seed_score
    neighbor_threshold: float = 5.0  # minimum neighbor score to admit

    # --- Redundancy ---
    redundancy_strength: RedundancyStrength = RedundancyStrength.MEDIUM

    # --- Oversize handling ---
    oversize_policy: OversizePolicy = OversizePolicy.TRUNCATE

    # --- Packing strategy ---
    packing_strategy: PackingStrategy = PackingStrategy.GREEDY_DENSITY
    knapsack_shortlist_top_n: int = 24  # only used when packing_strategy == KNAPSACK_OPT

    # --- Seed and pool limits ---
    top_seed_count: int = 5
    final_candidate_pool_cap: int = 64

    # --- Character budget ---
    char_budget: int = 4000       # total character budget for the bag

    # --- Scoring weights (from scoring doc §2) ---
    w_vector: float = 40.0
    w_tag: float = 8.0
    w_content: float = 3.0
    w_scope: float = 20.0
    recency_scale: float = 5.0    # recency_bonus = recency_scale / (days_old + 1)  — tiebreaker, not dominant
    reinforcement_scale: float = 2.0  # reinforcement = scale * log(1 + access_count)

    @property
    def category_ratios(self) -> Dict[str, float]:
        return {
            "goal": self.goal_ratio,
            "memory": self.memory_ratio,
            "knowledge": self.knowledge_ratio,
            "neighbor": self.neighbor_ratio,
        }

    def validate(self) -> None:
        """Raise ValueError if ratios don't sum to ~1.0 or values are out of range."""
        total = self.goal_ratio + self.memory_ratio + self.knowledge_ratio + self.neighbor_ratio
        if abs(total - 1.0) > 0.01:
            raise ValueError(
                f"Category ratios must sum to 1.0, got {total:.3f}"
            )
        if not (1.0 <= self.alpha <= 1.15):
            raise ValueError(
                f"alpha must be in [1.0, 1.15], got {self.alpha}"
            )
        if not (0.20 <= self.neighbor_beta <= 0.50):
            raise ValueError(
                f"neighbor_beta must be in [0.20, 0.50], got {self.neighbor_beta}"
            )
        if self.char_budget <= 0:
            raise ValueError("char_budget must be positive")


# ---------------------------------------------------------------------------
# Runtime mode presets (from runtime policy doc §13)
# ---------------------------------------------------------------------------

class RuntimeMode(Enum):
    PRECISION_LOCAL = "precision_local"
    CONVERSATIONAL = "conversational"
    EXPLORATION = "exploration"
    TASK_LOCK = "task_lock"
    DEEP_PACKING = "deep_packing"


def _make_precision_local() -> CompositionConfig:
    return CompositionConfig(
        goal_ratio=0.25,
        memory_ratio=0.30,
        knowledge_ratio=0.35,
        neighbor_ratio=0.10,
        alpha=1.10,
        neighbor_beta=0.30,
        neighbor_threshold=5.0,
        redundancy_strength=RedundancyStrength.MEDIUM,
        oversize_policy=OversizePolicy.TRUNCATE,
        packing_strategy=PackingStrategy.GREEDY_DENSITY,
    )


def _make_conversational() -> CompositionConfig:
    return CompositionConfig(
        goal_ratio=0.20,
        memory_ratio=0.40,
        knowledge_ratio=0.25,
        neighbor_ratio=0.15,
        alpha=1.08,
        neighbor_beta=0.35,
        neighbor_threshold=5.0,
        redundancy_strength=RedundancyStrength.MEDIUM,
        oversize_policy=OversizePolicy.TRUNCATE,
        packing_strategy=PackingStrategy.GREEDY_DENSITY,
    )


def _make_exploration() -> CompositionConfig:
    return CompositionConfig(
        goal_ratio=0.15,
        memory_ratio=0.20,
        knowledge_ratio=0.25,
        neighbor_ratio=0.40,
        alpha=1.02,
        neighbor_beta=0.45,
        neighbor_threshold=4.0,
        redundancy_strength=RedundancyStrength.LOW,
        oversize_policy=OversizePolicy.TRUNCATE,
        packing_strategy=PackingStrategy.GREEDY_DENSITY,
    )


def _make_task_lock() -> CompositionConfig:
    return CompositionConfig(
        goal_ratio=0.40,
        memory_ratio=0.20,
        knowledge_ratio=0.30,
        neighbor_ratio=0.10,
        alpha=1.08,
        neighbor_beta=0.20,
        neighbor_threshold=5.0,
        redundancy_strength=RedundancyStrength.MEDIUM,
        oversize_policy=OversizePolicy.STRICT,
        packing_strategy=PackingStrategy.GREEDY_DENSITY,
    )


def _make_deep_packing() -> CompositionConfig:
    return CompositionConfig(
        goal_ratio=0.25,
        memory_ratio=0.25,
        knowledge_ratio=0.35,
        neighbor_ratio=0.15,
        alpha=1.08,
        neighbor_beta=0.30,
        neighbor_threshold=5.0,
        redundancy_strength=RedundancyStrength.MEDIUM,
        oversize_policy=OversizePolicy.FOCUS_EXTRACT,
        packing_strategy=PackingStrategy.KNAPSACK_OPT,
        knapsack_shortlist_top_n=24,
    )


# Named preset instances for direct import
PRECISION_LOCAL = _make_precision_local()
CONVERSATIONAL = _make_conversational()
EXPLORATION = _make_exploration()
TASK_LOCK = _make_task_lock()
DEEP_PACKING = _make_deep_packing()

_MODE_FACTORIES = {
    RuntimeMode.PRECISION_LOCAL: _make_precision_local,
    RuntimeMode.CONVERSATIONAL: _make_conversational,
    RuntimeMode.EXPLORATION: _make_exploration,
    RuntimeMode.TASK_LOCK: _make_task_lock,
    RuntimeMode.DEEP_PACKING: _make_deep_packing,
}


def config_for_mode(mode: RuntimeMode) -> CompositionConfig:
    """Create a fresh CompositionConfig for the given runtime mode."""
    return _MODE_FACTORIES[mode]()
