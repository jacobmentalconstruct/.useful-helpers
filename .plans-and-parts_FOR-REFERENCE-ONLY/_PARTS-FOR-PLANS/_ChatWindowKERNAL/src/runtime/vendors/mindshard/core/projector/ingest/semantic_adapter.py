"""
manifold_kernel.ingest.semantic_adapter — Pluggable semantic backend interface.

The semantic layer is intentionally backend-agnostic.  This module defines the
adapter contract and provides a BDVec adapter that wraps the mechanical
tokenizer bundle already present in the project.
"""

from __future__ import annotations

import json
import struct
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config import SemanticConfig
from ..errors import SemanticBackendUnavailable, SemanticError


@dataclass
class SemanticResult:
    """Result of embedding a single text."""
    vector: List[float]
    norm: float
    token_count: int
    backend: str


class SemanticAdapter(ABC):
    """Interface contract for semantic backends."""

    @abstractmethod
    def embed(self, text: str) -> SemanticResult:
        """Embed a single text string."""

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[SemanticResult]:
        """Embed a batch of texts."""

    @abstractmethod
    def similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Cosine similarity between two vectors."""

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Human-readable backend identifier."""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Dimensionality of output vectors."""


class NullAdapter(SemanticAdapter):
    """No-op adapter for when no semantic backend is available."""

    def embed(self, text: str) -> SemanticResult:
        return SemanticResult(vector=[], norm=0.0, token_count=0, backend="none")

    def embed_batch(self, texts: List[str]) -> List[SemanticResult]:
        return [self.embed(t) for t in texts]

    def similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        return 0.0

    @property
    def backend_name(self) -> str:
        return "none"

    @property
    def dimensions(self) -> int:
        return 0


class BDVecAdapter(SemanticAdapter):
    """
    Wraps the mechanical tokenizer bundle's DeterministicEmbedProvider.

    Locates the BDVec artifacts relative to the project src/ tree and
    loads the provider lazily on first use.
    """

    def __init__(self, config: SemanticConfig) -> None:
        self._config = config
        self._provider = None
        self._dims: int = 0

    def _ensure_loaded(self) -> None:
        if self._provider is not None:
            return

        # Resolve paths to the mechanical tokenizer bundle
        tokenizer_path = Path(self._config.bdvec_tokenizer_path)
        embeddings_path = Path(self._config.bdvec_embeddings_path)

        if not tokenizer_path.is_file() or not embeddings_path.is_file():
            # Try to auto-discover from the project layout
            src_root = Path(__file__).resolve().parent.parent.parent
            bundle = src_root / "mechanical_tokenizer_bundle" / "bdvec"
            tokenizer_path = bundle / "artifacts" / "tokenizer.json"
            embeddings_path = bundle / "artifacts" / "embeddings.npy"

        if not tokenizer_path.is_file():
            raise SemanticBackendUnavailable(
                f"BDVec tokenizer not found at {tokenizer_path}"
            )
        if not embeddings_path.is_file():
            raise SemanticBackendUnavailable(
                f"BDVec embeddings not found at {embeddings_path}"
            )

        # Import the provider from the bundle
        bdvec_src = tokenizer_path.parent.parent
        if str(bdvec_src) not in sys.path:
            sys.path.insert(0, str(bdvec_src))

        try:
            from bpe_svd.inference.provider import DeterministicEmbedProvider
            self._provider = DeterministicEmbedProvider(tokenizer_path, embeddings_path)
            # Probe dimensions
            probe = self._provider.embed_texts(["probe"])
            self._dims = probe.dimensions
        except Exception as exc:
            raise SemanticBackendUnavailable(f"Failed to load BDVec: {exc}") from exc

    def embed(self, text: str) -> SemanticResult:
        self._ensure_loaded()
        result = self._provider.embed_texts([text])
        vec = result.vectors[0] if result.vectors else []
        norm = 0.0
        if vec:
            import numpy as np
            norm = float(np.linalg.norm(vec))
        return SemanticResult(
            vector=vec,
            norm=norm,
            token_count=result.token_counts[0] if result.token_counts else 0,
            backend="bdvec",
        )

    def embed_batch(self, texts: List[str]) -> List[SemanticResult]:
        self._ensure_loaded()
        result = self._provider.embed_texts(texts)
        import numpy as np
        results = []
        for i, vec in enumerate(result.vectors):
            norm = float(np.linalg.norm(vec)) if vec else 0.0
            results.append(SemanticResult(
                vector=vec,
                norm=norm,
                token_count=result.token_counts[i] if i < len(result.token_counts) else 0,
                backend="bdvec",
            ))
        return results

    def similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b:
            return 0.0
        import numpy as np
        a = np.array(vec_a)
        b = np.array(vec_b)
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    @property
    def backend_name(self) -> str:
        return "bdvec"

    @property
    def dimensions(self) -> int:
        self._ensure_loaded()
        return self._dims


def create_adapter(config: SemanticConfig) -> SemanticAdapter:
    """Factory: create the configured semantic adapter."""
    if config.backend == "bdvec":
        try:
            adapter = BDVecAdapter(config)
            # Try loading eagerly to detect failures
            adapter._ensure_loaded()
            return adapter
        except SemanticBackendUnavailable:
            if config.fallback_to_none:
                return NullAdapter()
            raise
    return NullAdapter()


def vector_to_blob(vec: List[float]) -> bytes:
    """Pack a float list into a compact binary blob."""
    return struct.pack(f"<{len(vec)}f", *vec)


def blob_to_vector(blob: bytes) -> List[float]:
    """Unpack a binary blob back into a float list."""
    if not blob:
        return []
    count = len(blob) // 4
    return list(struct.unpack(f"<{count}f", blob))
