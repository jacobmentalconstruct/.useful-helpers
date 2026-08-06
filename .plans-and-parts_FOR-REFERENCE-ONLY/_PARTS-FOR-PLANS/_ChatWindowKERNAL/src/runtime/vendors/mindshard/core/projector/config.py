"""
manifold_kernel.config — Explicit configuration objects.

All tuneable behaviour is surfaced here so that nothing important is
buried inside UI handlers or prompt strings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class StorageConfig:
    """Where and how to persist canonical records."""
    db_path: str = "manifold_kernel.db"
    wal_mode: bool = True
    foreign_keys: bool = True


@dataclass
class IngestConfig:
    """Controls for the ingestion pipeline."""
    chunk_size: int = 512
    chunk_overlap: int = 64
    file_extensions: tuple = (".md", ".txt", ".py", ".json", ".html", ".rst", ".cfg", ".toml", ".yaml", ".yml")
    normalize_whitespace: bool = True
    normalize_case: bool = False
    strip_comments: bool = False


@dataclass
class SemanticConfig:
    """Semantic backend selection and parameters."""
    backend: str = "bdvec"
    bdvec_tokenizer_path: str = ""
    bdvec_embeddings_path: str = ""
    fallback_to_none: bool = True


@dataclass
class ProjectionConfig:
    """Defaults for query-time projection."""
    default_radius: int = 2
    default_max_seeds: int = 12
    default_max_nodes: int = 100
    relation_filter: tuple = ()


@dataclass
class LensConfig:
    """Weight coefficients for the lens scoring equation."""
    semantic_similarity: float = 0.35
    structural_proximity: float = 0.25
    identity_relevance: float = 0.15
    adjacency_support: float = 0.15
    exact_match: float = 0.10
    propagation_decay: float = 0.5
    neighborhood_density_bonus: float = 0.05


@dataclass
class OutputConfig:
    """Controls for evidence bag serialisation."""
    include_text_snippets: bool = True
    include_relation_metadata: bool = True
    include_diagnostics: bool = False
    max_snippet_chars: int = 300


@dataclass
class KernelConfig:
    """Top-level configuration envelope."""
    storage: StorageConfig = field(default_factory=StorageConfig)
    ingest: IngestConfig = field(default_factory=IngestConfig)
    semantic: SemanticConfig = field(default_factory=SemanticConfig)
    projection: ProjectionConfig = field(default_factory=ProjectionConfig)
    lens: LensConfig = field(default_factory=LensConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def with_defaults(cls, db_path: str = "_project_library/manifold_kernel.db") -> "KernelConfig":
        """Factory that fills in sensible defaults.

        The default db_path places the canonical store inside _project_library/
        to keep the project root clean.
        """
        return cls(storage=StorageConfig(db_path=db_path))
