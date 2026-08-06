"""
manifold_kernel.errors — Typed exception hierarchy.

Every error the kernel can raise descends from ManifoldKernelError so that
callers can catch the entire family in one clause when desired.
"""

from __future__ import annotations


class ManifoldKernelError(Exception):
    """Root exception for all manifold-kernel errors."""


# ── Ingestion errors ─────────────────────────────────────────────────

class IngestionError(ManifoldKernelError):
    """Raised when the ingest pipeline fails."""


class SourceNotFoundError(IngestionError):
    """Raised when a requested source path does not exist."""


class ChunkingError(IngestionError):
    """Raised when the chunker cannot segment a source."""


class NormalizationError(IngestionError):
    """Raised when text normalization fails."""


# ── Storage errors ───────────────────────────────────────────────────

class StorageError(ManifoldKernelError):
    """Raised when the persistence layer fails."""


class SchemaError(StorageError):
    """Raised when the database schema is invalid or cannot be initialised."""


class DuplicateArtifactError(StorageError):
    """Raised when an artifact ID collision is detected."""


class ArtifactNotFoundError(StorageError):
    """Raised when a requested artifact does not exist."""


# ── Projection errors ────────────────────────────────────────────────

class ProjectionError(ManifoldKernelError):
    """Raised when projection construction fails."""


class SeedRetrievalError(ProjectionError):
    """Raised when seed selection returns zero candidates."""


class BoundExceededError(ProjectionError):
    """Raised when a projection exceeds configured bounds."""


# ── Semantic errors ──────────────────────────────────────────────────

class SemanticError(ManifoldKernelError):
    """Raised when the semantic adapter encounters a problem."""


class SemanticBackendUnavailable(SemanticError):
    """Raised when the configured semantic backend cannot be reached."""


# ── Configuration errors ─────────────────────────────────────────────

class ConfigError(ManifoldKernelError):
    """Raised when configuration is invalid or incomplete."""
