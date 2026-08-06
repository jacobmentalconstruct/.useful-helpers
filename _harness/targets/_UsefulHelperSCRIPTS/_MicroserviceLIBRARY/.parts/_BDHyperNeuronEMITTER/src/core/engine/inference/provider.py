"""provider.py — BPE-SVD embedding + Hot Query coordinator.

Ownership: core/engine/inference/provider.py
    Two responsibilities in one module, per domain boundary:

    1. DeterministicEmbedProvider — pure-math BPE-SVD embedding.
       Loads tokenizer.json (vocab + merge rules) and embeddings.npy (dense
       vocab_size × k matrix) produced by the training pipeline.  At query
       time: tokenises text via BPE, looks up token vectors, mean-pools them
       into a single k-dimensional embedding per input string.  Also supports
       reverse lookup (nearest tokens by cosine similarity).
       Dependencies: stdlib + numpy only.

    2. query() — full Reactor pipeline coordinator.
       Fuses FTS5 lexical anchors with optional ANN vector anchors, loads the
       active subgraph from cold_anatomy.db, and runs HotEngine propagation
       to produce a Bag of Evidence.
       Dependencies: stdlib + numpy + core.engine.inference.{retrieval, hot_engine}.

Boundary rule: this module never imports from assembler or surveyor.

V1 reference: _BDHyperNeuronEMITTER/src/engine/inference/provider.py
V1 changes:
    - Module docstring updated to v2 context
    - Internal imports updated: engine.inference.* → core.engine.inference.*
    - Logging added for load operations
    - No algorithmic changes
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)
EMBEDDING_PROVIDER_FILENAME = "embedding_provider_effective.json"
DEFAULT_SENTENCE_TRANSFORMER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# ── Result type ──────────────────────────────────────────────────────

@dataclass
class EmbedResult:
    """Structured result from a call to DeterministicEmbedProvider."""

    vectors: List[List[float]]
    """One pooled embedding vector per input text."""

    dimensions: int
    """Dimensionality of each vector (k)."""

    token_counts: List[int]
    """Number of BPE tokens produced for each input text."""

    token_ids: List[List[int]]
    """Raw BPE token ID sequences, one per input text."""


@dataclass
class EmbeddingProviderSpec:
    """Serializable description of the active embedding provider for a graph DB."""

    provider: str
    model_name: str = ""
    artifacts_dir: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "artifacts_dir": self.artifacts_dir,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "EmbeddingProviderSpec":
        provider = str(payload.get("provider", "none")).strip().lower() or "none"
        return cls(
            provider=provider,
            model_name=str(payload.get("model_name", "") or ""),
            artifacts_dir=str(payload.get("artifacts_dir", "") or ""),
        )


def save_embedding_provider_spec(output_dir: str | Path, spec: EmbeddingProviderSpec) -> Path:
    path = Path(output_dir) / EMBEDDING_PROVIDER_FILENAME
    path.write_text(json.dumps(spec.to_dict(), indent=2), encoding="utf-8")
    return path


def load_embedding_provider_spec(db_path: str | Path) -> EmbeddingProviderSpec:
    path = Path(db_path).resolve().parent / EMBEDDING_PROVIDER_FILENAME
    if not path.is_file():
        return EmbeddingProviderSpec(provider="none")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid embedding provider metadata at {path}")
    return EmbeddingProviderSpec.from_dict(payload)


# ── Provider ─────────────────────────────────────────────────────────

class DeterministicEmbedProvider:
    """BPE-SVD deterministic embedding provider.

    Load once, embed many times.  Fully deterministic: identical input
    always produces identical output on any machine.

    Parameters
    ----------
    tokenizer_path : str | Path
        Path to tokenizer.json produced by BPETrainer.save().
    embeddings_path : str | Path
        Path to embeddings.npy produced by compute_embeddings() + np.save().
    """

    def __init__(
        self,
        tokenizer_path: str | Path,
        embeddings_path: str | Path,
    ) -> None:
        self._vocab: Dict[str, int]
        self._merges: List[Tuple[str, str]]
        self._end_of_word: str
        self._inverse_vocab_cache: Optional[Dict[int, str]] = None
        self._load_tokenizer(Path(tokenizer_path))
        self._embeddings = self._load_embeddings(Path(embeddings_path))

    # ── Artifact loading ─────────────────────────────────────────────

    def _load_tokenizer(self, path: Path) -> None:
        if not path.is_file():
            raise FileNotFoundError(f"Tokenizer not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            spec = json.load(f)
        self._vocab = {str(k): int(v) for k, v in spec["vocab"].items()}
        raw = spec.get("merges", [])
        self._merges = [
            (m[0], m[1]) if isinstance(m, (list, tuple)) else (m[: len(m) // 2], m[len(m) // 2 :])
            for m in raw
        ]
        self._end_of_word = spec.get("end_of_word", "</w>")
        log.debug("DeterministicEmbedProvider: loaded tokenizer vocab_size=%d", len(self._vocab))

    def _load_embeddings(self, path: Path):  # noqa: ANN201
        try:
            import numpy as np  # lazy import
        except ImportError as exc:
            raise ImportError("numpy is required: pip install numpy") from exc
        if not path.is_file():
            raise FileNotFoundError(f"Embeddings not found: {path}")
        arr = np.load(str(path))
        if arr.ndim != 2:
            raise ValueError(f"embeddings.npy must be 2-D, got shape {arr.shape}")
        log.debug("DeterministicEmbedProvider: loaded embeddings shape=%s", arr.shape)
        return arr

    # ── BPE encoding ─────────────────────────────────────────────────

    def _encode_word(self, word: str) -> List[str]:
        symbols: List[str] = list(word) + [self._end_of_word]
        for a, b in self._merges:
            merged = a + b
            i = 0
            new: List[str] = []
            while i < len(symbols):
                if i < len(symbols) - 1 and symbols[i] == a and symbols[i + 1] == b:
                    new.append(merged)
                    i += 2
                else:
                    new.append(symbols[i])
                    i += 1
            symbols = new
        return symbols

    def _encode(self, text: str) -> List[int]:
        ids: List[int] = []
        for word in text.strip().split():
            for sym in self._encode_word(word):
                ids.append(self._vocab.get(sym, -1))
        return ids

    # ── Embedding ────────────────────────────────────────────────────

    def _embed_single(self, text: str):  # noqa: ANN201
        import numpy as np

        token_ids = self._encode(text)
        k = self._embeddings.shape[1]
        if not token_ids:
            return np.zeros(k, dtype=float), token_ids

        rows = []
        for tid in token_ids:
            if 0 <= tid < len(self._embeddings):
                rows.append(self._embeddings[tid])
            else:
                rows.append(np.zeros(k, dtype=float))

        return np.mean(rows, axis=0), token_ids

    def embed_texts(self, texts: List[str]) -> EmbedResult:
        """Embed a list of texts, returning one pooled vector per text.

        Parameters
        ----------
        texts : List[str]
            Input strings to embed.

        Returns
        -------
        EmbedResult
            Pooled vectors, dimensions, token counts, and token ID sequences.
        """
        if not texts:
            return EmbedResult(vectors=[], dimensions=0, token_counts=[], token_ids=[])

        vectors: List[List[float]] = []
        token_counts: List[int] = []
        all_token_ids: List[List[int]] = []

        for text in texts:
            vec, ids = self._embed_single(text)
            vectors.append(vec.tolist())
            token_counts.append(len(ids))
            all_token_ids.append(ids)

        dims = self._embeddings.shape[1]
        return EmbedResult(
            vectors=vectors,
            dimensions=dims,
            token_counts=token_counts,
            token_ids=all_token_ids,
        )

    def embed(self, texts: List[str]) -> EmbedResult:
        """Compatibility alias used by the CLI, assembler, and GUI."""
        return self.embed_texts(texts)

    # ── Reverse lookup ────────────────────────────────────────────────

    @property
    def vocab(self) -> Dict[str, int]:
        """Read-only copy of token vocabulary (symbol → ID)."""
        return dict(self._vocab)

    @property
    def inverse_vocab(self) -> Dict[int, str]:
        """Lazily-built ID → symbol mapping."""
        if self._inverse_vocab_cache is None:
            self._inverse_vocab_cache = {v: k for k, v in self._vocab.items()}
        return dict(self._inverse_vocab_cache)

    def decode_token_ids(self, token_ids: List[int]) -> List[str]:
        """Map integer token IDs back to their symbol strings.

        Unknown IDs are represented as ``<unk:{id}>``.
        """
        inv = self.inverse_vocab
        return [inv.get(tid, f"<unk:{tid}>") for tid in token_ids]

    def nearest_tokens(
        self,
        vector: List[float],
        k: int = 10,
    ) -> List[Tuple[str, float, List[float]]]:
        """Find the k tokens whose embeddings are nearest to vector.

        Returns a list of (symbol, cosine_similarity, token_vector)
        sorted by descending similarity.  All values are plain Python types.
        """
        import numpy as np

        q = np.array(vector, dtype=float)
        q_norm = np.linalg.norm(q)
        if q_norm == 0.0:
            return []

        q_unit = q / q_norm
        norms = np.linalg.norm(self._embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        unit_emb = self._embeddings / norms
        sims = unit_emb @ q_unit

        effective_k = min(k, len(sims))
        top_idx = np.argpartition(sims, -effective_k)[-effective_k:]
        top_idx = top_idx[np.argsort(sims[top_idx])[::-1]]

        inv = self.inverse_vocab
        return [
            (
                inv.get(int(i), f"<unk:{i}>"),
                float(sims[i]),
                self._embeddings[i].tolist(),
            )
            for i in top_idx
        ]


class SentenceTransformerEmbedProvider:
    """Traditional sentence-embedding provider backed by sentence-transformers."""

    def __init__(self, model_name: str = DEFAULT_SENTENCE_TRANSFORMER_MODEL) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for the traditional embedder path"
            ) from exc

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    def embed_texts(self, texts: List[str]) -> EmbedResult:
        if not texts:
            return EmbedResult(vectors=[], dimensions=0, token_counts=[], token_ids=[])

        vectors = self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return EmbedResult(
            vectors=[row.tolist() for row in vectors],
            dimensions=int(vectors.shape[1]) if len(vectors.shape) > 1 else 0,
            token_counts=[len(text.split()) for text in texts],
            token_ids=[[] for _ in texts],
        )

    def embed(self, texts: List[str]) -> EmbedResult:
        return self.embed_texts(texts)


def create_embed_provider(spec: EmbeddingProviderSpec) -> Optional[Any]:
    provider = spec.provider.lower().strip()
    if provider in {"", "none"}:
        return None
    if provider == "deterministic":
        artifacts_dir = Path(spec.artifacts_dir)
        tokenizer_path = artifacts_dir / "tokenizer.json"
        embeddings_path = artifacts_dir / "embeddings.npy"
        return DeterministicEmbedProvider(tokenizer_path, embeddings_path)
    if provider == "sentence-transformers":
        model_name = spec.model_name or DEFAULT_SENTENCE_TRANSFORMER_MODEL
        return SentenceTransformerEmbedProvider(model_name=model_name)
    raise ValueError(f"Unsupported embedding provider: {spec.provider}")


# ── Hot Query API — coordinates Retrieval + HotEngine ────────────────

def query(
    text: str,
    db_path: "str | Path | None" = None,
    top_k: int = 20,
    hop_limit: int = 2,
    decay: float = 0.9,
    embedder_override: str | None = None,
    sentence_model: str | None = None,
) -> "List[BagOfEvidence]":  # noqa: F821
    """Run a full Hot Query: fused FTS5+ANN anchor → subgraph load → propagation.

    This is the primary entry point for inference queries.  It coordinates
    the full Reactor pipeline without requiring the caller to manage
    individual subsystem imports.

    Anchor strategy:
        1. FTS5 lexical search — always attempted.
        2. ANN vector search   — attempted when embedding artifacts
           (tokenizer.json + embeddings.npy) exist alongside the database.
           Results are merged and deduplicated before subgraph expansion.
           FTS anchors are preferred in deduplication order; ANN anchors
           fill in any remaining budget.

    Parameters
    ----------
    text : str
        Natural language or code query string.
    db_path : str | Path, optional
        Path to cold_anatomy.db.  Defaults to artifacts/cold_anatomy.db.
    top_k : int
        Maximum Bag of Evidence results.
    hop_limit : int
        Propagation depth (1–2 recommended).
    decay : float
        Activation decay factor α.

    Returns
    -------
    list[BagOfEvidence]
        Ranked list of activated occurrence nodes.
    """
    import sqlite3
    from pathlib import Path as _Path
    from .retrieval import fts_search, ann_search, load_subgraph
    from .hot_engine import HotEngine, BagOfEvidence

    if db_path is None:
        db_path = _Path(__file__).resolve().parent.parent.parent.parent / "artifacts" / "cold_anatomy.db"

    db_path = _Path(str(db_path))
    if not db_path.is_file():
        log.warning("query(): database not found at %s", db_path)
        return []

    log.debug("query(): text=%r db=%s top_k=%d", text[:60], db_path.name, top_k)
    conn = sqlite3.connect(str(db_path))
    try:
        # ── FTS anchors — always attempted ───────────────────────────────
        fts_anchors = fts_search(conn, text, top_k=top_k)
        log.debug("query(): fts_anchors=%d", len(fts_anchors))

        # ── ANN anchors — opportunistic, requires embedding artifacts ────
        ann_anchors = []
        try:
            provider_spec = load_embedding_provider_spec(db_path)
            if embedder_override is not None:
                provider_spec = EmbeddingProviderSpec(
                    provider=embedder_override,
                    model_name=sentence_model or provider_spec.model_name,
                    artifacts_dir=provider_spec.artifacts_dir,
                )
            elif provider_spec.provider == "none":
                artifacts_dir = db_path.parent
                tokenizer_path = artifacts_dir / "tokenizer.json"
                embeddings_path = artifacts_dir / "embeddings.npy"
                if tokenizer_path.is_file() and embeddings_path.is_file():
                    provider_spec = EmbeddingProviderSpec(
                        provider="deterministic",
                        artifacts_dir=str(artifacts_dir),
                    )

            embed_provider = create_embed_provider(provider_spec)
            if embed_provider is not None:
                result = embed_provider.embed_texts([text])
                if result.vectors and result.vectors[0]:
                    ann_anchors = ann_search(conn, result.vectors[0], top_k=top_k)
                log.debug(
                    "query(): ann_anchors=%d provider=%s",
                    len(ann_anchors),
                    provider_spec.provider,
                )
        except Exception as exc:
            log.debug("query(): ANN skipped (%s)", exc)

        # ── Merge and deduplicate — FTS first, ANN fills remaining slots ─
        seen: set = set()
        merged: list = []
        for anchor in fts_anchors + ann_anchors:
            if anchor.occurrence_id not in seen:
                seen.add(anchor.occurrence_id)
                merged.append(anchor)

        if not merged:
            return []

        anchor_ids = [a.occurrence_id for a in merged]
        subgraph = load_subgraph(conn, anchor_ids, hop_limit=hop_limit)
        engine = HotEngine(decay=decay, hop_limit=hop_limit)
        results = engine.run(subgraph, anchor_ids, top_k=top_k)
        log.debug("query(): boe_results=%d", len(results))
        return results
    finally:
        conn.close()
