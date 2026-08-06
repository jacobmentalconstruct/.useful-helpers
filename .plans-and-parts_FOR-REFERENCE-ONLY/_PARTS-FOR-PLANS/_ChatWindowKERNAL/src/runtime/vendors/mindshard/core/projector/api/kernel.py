"""
manifold_kernel.api.kernel — Top-level ManifoldKernel public API.

This is a TOOL FOR AGENTS, not an agent itself.  It provides:

  Canonical pipeline:
    kernel.ingest_source(path)
    kernel.extract_evidence(query, ...)
    kernel.project(query, ...)
    kernel.inspect_artifact(artifact_id)
    kernel.list_neighbors(artifact_id, depth)

  Evidence Bag runtime (CodeMONKEY gravity scoring + composition):
    kernel.evidence_runtime   — direct access to EvidenceBagRuntime
    kernel.assemble_bag(query, query_vector, ...)

  Interrogation (dimension-aware context for agent prompts):
    kernel.interrogate(bag_items, query, mode, scope)

  Mechanical Embedder access:
    kernel.embed_texts(texts)
    kernel.nearest_tokens(vector, k)
    kernel.embedder_info()
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..config import KernelConfig
from ..errors import ArtifactNotFoundError, ManifoldKernelError
from ..storage.sqlite_store import SQLiteStore
from ..ingest.semantic_adapter import SemanticAdapter, create_adapter
from ..ingest.pipeline import ingest_source as _ingest_source
from ..relations.builder import build_semantic_neighbors
from ..projection.projector import project as _project
from ..lens.scoring import score_graph
from ..lens.profiles import get_profile
from ..lens.propagation import propagate_scores
from ..evidence.bag import EvidenceBag, distill_evidence
from ..evidence.serializer import evidence_to_json, evidence_to_summary
from ..types import ProjectionGraph

logger = logging.getLogger(__name__)


class ManifoldKernel:
    """
    Public API for the Graph Manifold Kernel Tool.

    This is a substrate for agents — it does NOT contain agent logic.
    Agents call into it for ingestion, projection, scoring, evidence
    assembly, dimension-aware interrogation, and direct embedder access.

    Usage::

        kernel = ManifoldKernel(config)
        kernel.ingest_source("docs/")
        bag = kernel.extract_evidence("How does X work?", lens_profile="balanced")
        context = kernel.interrogate(bag.items, "How does X work?")
        vec = kernel.embed_texts(["hello world"])
    """

    def __init__(self, config: Optional[KernelConfig] = None) -> None:
        self._config = config or KernelConfig.with_defaults()
        self._store = SQLiteStore(self._config.storage)
        self._store.open()
        self._semantic: Optional[SemanticAdapter] = None
        self._evidence_runtime = None
        self._embedder = None

    @property
    def config(self) -> KernelConfig:
        return self._config

    @property
    def store(self) -> SQLiteStore:
        return self._store

    @property
    def semantic_adapter(self) -> SemanticAdapter:
        """Lazy-load the semantic adapter."""
        if self._semantic is None:
            self._semantic = create_adapter(self._config.semantic)
        return self._semantic

    def close(self) -> None:
        """Close all database connections."""
        self._store.close()
        if self._evidence_runtime is not None:
            self._evidence_runtime.close()

    # ══════════════════════════════════════════════════════════════════
    # Ingestion
    # ══════════════════════════════════════════════════════════════════

    def ingest_source(self, path: str | Path) -> Dict[str, Any]:
        """
        Ingest a source file or directory into canonical records.

        Returns a stats dict with ingestion counts.
        """
        stats = _ingest_source(
            target=path,
            store=self._store,
            config=self._config,
            semantic_adapter=self.semantic_adapter,
        )

        # Post-ingestion: build semantic neighbor relations
        if self.semantic_adapter.backend_name != "none":
            try:
                neighbor_count = build_semantic_neighbors(
                    self._store, self.semantic_adapter, self._config,
                )
                stats["semantic_neighbors_created"] = neighbor_count
            except Exception as exc:
                logger.warning("Semantic neighbor build failed: %s", exc)
                stats["semantic_neighbors_created"] = 0

        return stats

    # ══════════════════════════════════════════════════════════════════
    # Projection
    # ══════════════════════════════════════════════════════════════════

    def project(
        self,
        query: str,
        max_seeds: Optional[int] = None,
        max_nodes: Optional[int] = None,
        radius: Optional[int] = None,
        relation_filter: Optional[Set[str]] = None,
    ) -> ProjectionGraph:
        """
        Build a bounded temporary in-memory manifold for a query.

        Returns the raw ProjectionGraph (before lens scoring).
        """
        return _project(
            query=query,
            store=self._store,
            semantic_adapter=self.semantic_adapter,
            config=self._config,
            max_seeds=max_seeds,
            max_nodes=max_nodes,
            radius=radius,
            relation_filter=relation_filter,
        )

    # ══════════════════════════════════════════════════════════════════
    # Evidence extraction (manifold lens pipeline)
    # ══════════════════════════════════════════════════════════════════

    def extract_evidence(
        self,
        query: str,
        lens_profile: str = "balanced",
        max_seeds: Optional[int] = None,
        max_nodes: Optional[int] = None,
        radius: Optional[int] = None,
        max_items: Optional[int] = None,
        min_score: float = 0.0,
    ) -> EvidenceBag:
        """
        Full pipeline: project → score → propagate → distill evidence bag.
        """
        # 1. Project
        graph = self.project(
            query=query,
            max_seeds=max_seeds,
            max_nodes=max_nodes,
            radius=radius,
        )

        if not graph.nodes:
            return EvidenceBag(query=query, lens_profile=lens_profile)

        # 2. Score with lens
        lens_config = get_profile(lens_profile)
        seed_ids = [
            nid for nid, node in graph.nodes.items()
            if node.score_components.get("seed_score", 0) > 0
        ]

        score_graph(
            graph=graph,
            query=query,
            store=self._store,
            semantic_adapter=self.semantic_adapter,
            lens=lens_config,
            seed_ids=seed_ids,
        )

        # 3. Propagate scores
        propagate_scores(graph, lens_config)

        # 4. Distill evidence bag (pass store for source_path resolution)
        return distill_evidence(
            graph=graph,
            query=query,
            lens_profile=lens_profile,
            config=self._config,
            seed_ids=seed_ids,
            max_items=max_items,
            min_score=min_score,
            store=self._store,
        )

    # ══════════════════════════════════════════════════════════════════
    # Evidence Bag Runtime (CodeMONKEY gravity scoring + composition)
    # ══════════════════════════════════════════════════════════════════

    @property
    def evidence_runtime(self):
        """
        Lazy-load the CodeMONKEY EvidenceBagRuntime.

        This gives agents direct access to the gravity scorer, bag
        composer, node store, and all runtime modes (PRECISION_LOCAL,
        CONVERSATIONAL, EXPLORATION, TASK_LOCK, DEEP_PACKING).

        The runtime operates on its own evidence_bag.db alongside
        the manifold kernel's canonical store.
        """
        if self._evidence_runtime is None:
            try:
                from evidence_bag.runtime import EvidenceBagRuntime
                from evidence_bag.config import RuntimeMode

                db_path = self._config.storage.db_path
                if db_path == ":memory:":
                    eb_db = ":memory:"
                else:
                    # Store in _project_library/ alongside the canonical DB
                    project_root = Path(db_path).resolve().parent
                    lib_dir = project_root / "_project_library"
                    lib_dir.mkdir(parents=True, exist_ok=True)
                    eb_db = str(lib_dir / "evidence_bag.db")

                self._evidence_runtime = EvidenceBagRuntime(
                    db_path=eb_db,
                    mode=RuntimeMode.PRECISION_LOCAL,
                )
                logger.info("Evidence bag runtime initialised: %s", eb_db)
            except Exception as exc:
                logger.warning("Evidence bag runtime init failed: %s", exc)
                return None
        return self._evidence_runtime

    def assemble_bag(
        self,
        query_text: str,
        query_vector: Optional[List[float]] = None,
        active_goal_id: Optional[str] = None,
        char_budget: Optional[int] = None,
        runtime_mode: Optional[str] = None,
    ):
        """
        Assemble an evidence bag using the CodeMONKEY gravity pipeline.

        This is the direct gravity-scored assembly path. For agents that
        want the full CodeMONKEY scoring (vector similarity + lexical
        overlap + recency + reinforcement + noise penalties + kind
        multipliers + boundary dampening + redundancy suppression +
        density packing).

        Args:
            query_text:    The query or task description.
            query_vector:  Optional embedding vector for the query.
                           If None and the mechanical embedder is available,
                           it will be computed automatically.
            active_goal_id: Current goal ID for boundary dampening.
            char_budget:   Override the default character budget.
            runtime_mode:  One of: precision_local, conversational,
                           exploration, task_lock, deep_packing.

        Returns:
            An EvidenceBag from the CodeMONKEY composition layer.
        """
        rt = self.evidence_runtime
        if rt is None:
            raise ManifoldKernelError("Evidence bag runtime not available")

        # Switch mode if requested
        if runtime_mode is not None:
            from evidence_bag.config import RuntimeMode
            mode_map = {
                "precision_local": RuntimeMode.PRECISION_LOCAL,
                "conversational": RuntimeMode.CONVERSATIONAL,
                "exploration": RuntimeMode.EXPLORATION,
                "task_lock": RuntimeMode.TASK_LOCK,
                "deep_packing": RuntimeMode.DEEP_PACKING,
            }
            mode = mode_map.get(runtime_mode.lower())
            if mode:
                rt.set_mode(mode)

        # Auto-embed if no vector provided and embedder is available
        if query_vector is None:
            try:
                result = self.embed_texts([query_text])
                if result and result["vectors"]:
                    query_vector = result["vectors"][0]
            except Exception:
                pass  # Fall through — gravity scorer works without vectors

        return rt.assemble(
            query_text=query_text,
            query_vector=query_vector,
            active_goal_id=active_goal_id,
            char_budget=char_budget,
        )

    # ══════════════════════════════════════════════════════════════════
    # Interrogation (dimension-aware context for agent prompts)
    # ══════════════════════════════════════════════════════════════════

    def interrogate(
        self,
        bag_items: list,
        query: str,
        mode: str = "chat",
        scope: str = "local",
    ) -> str:
        """
        Transform flat evidence bag items into dimension-aware structured
        context suitable for agent prompt injection.

        Classifies intent → builds typed records per dimension → constrains
        answer shape with grounding rules → returns formatted markdown.

        Args:
            bag_items: List of BagItem/EvidenceItem objects.
            query:     The user's raw query text.
            mode:      Agent task mode (chat, classify, label, patch, etc.).
            scope:     Agent task scope (local, project, global).

        Returns:
            Formatted dimension-aware context string.
        """
        from ..evidence.interrogation import (
            TaskMode, TaskScope, interrogate_evidence,
        )

        task_mode = TaskMode(mode) if mode in [m.value for m in TaskMode] else TaskMode.CHAT
        task_scope = TaskScope(scope) if scope in [s.value for s in TaskScope] else TaskScope.LOCAL

        return interrogate_evidence(bag_items, query, task_mode, task_scope)

    # ══════════════════════════════════════════════════════════════════
    # Mechanical Embedder (BDVec BPE-SVD)
    # ══════════════════════════════════════════════════════════════════

    @property
    def embedder(self):
        """
        Lazy-load the BDVec DeterministicEmbedProvider.

        Returns None if artifacts are not available.
        """
        if self._embedder is None:
            try:
                from mechanical_tokenizer_bundle.bdvec.bpe_svd.inference.provider import (
                    DeterministicEmbedProvider,
                )
                cfg = self._config.semantic
                tok = cfg.bdvec_tokenizer_path
                emb = cfg.bdvec_embeddings_path

                if not tok or not emb:
                    # Auto-discover from bundle location
                    src_root = Path(__file__).resolve().parent.parent.parent
                    bundle = src_root / "mechanical_tokenizer_bundle" / "bdvec"
                    tok = str(bundle / "artifacts" / "tokenizer.json")
                    emb = str(bundle / "artifacts" / "embeddings.npy")

                if Path(tok).is_file() and Path(emb).is_file():
                    self._embedder = DeterministicEmbedProvider(tok, emb)
                    logger.info("Mechanical embedder loaded: %s", tok)
                else:
                    logger.info("Mechanical embedder artifacts not found")
            except ImportError:
                logger.warning("mechanical_tokenizer_bundle not importable")
        return self._embedder

    def embed_texts(self, texts: List[str]) -> Optional[Dict[str, Any]]:
        """
        Embed texts using the mechanical BPE-SVD embedder.

        Returns dict with: vectors, dimensions, token_counts, token_ids.
        Returns None if the embedder is not available.
        """
        emb = self.embedder
        if emb is None:
            return None
        result = emb.embed_texts(texts)
        return {
            "vectors": result.vectors,
            "dimensions": result.dimensions,
            "token_counts": result.token_counts,
            "token_ids": result.token_ids,
        }

    def nearest_tokens(
        self,
        vector: List[float],
        k: int = 10,
    ) -> Optional[List[Tuple[str, float]]]:
        """
        Find the k nearest BPE tokens to a vector in embedding space.

        Returns list of (token_symbol, cosine_similarity) tuples.
        Returns None if the embedder is not available.
        """
        emb = self.embedder
        if emb is None:
            return None
        results = emb.nearest_tokens(vector, k=k)
        return [(symbol, sim) for symbol, sim, _ in results]

    def decode_token_ids(self, token_ids: List[int]) -> Optional[List[str]]:
        """Map token IDs back to symbol strings."""
        emb = self.embedder
        if emb is None:
            return None
        return emb.decode_token_ids(token_ids)

    def embedder_info(self) -> Dict[str, Any]:
        """
        Return metadata about the mechanical embedder's configuration.

        Useful for agents to inspect what embedder is active, its
        vocabulary size, dimensionality, and artifact paths.
        """
        emb = self.embedder
        if emb is None:
            return {"available": False, "backend": "none"}

        vocab = emb.vocab
        import numpy as np
        emb_shape = emb._embeddings.shape

        return {
            "available": True,
            "backend": "bdvec_bpe_svd",
            "vocab_size": len(vocab),
            "dimensions": emb_shape[1],
            "embedding_matrix_shape": list(emb_shape),
            "end_of_word_symbol": emb._end_of_word,
            "merge_count": len(emb._merges),
        }

    # ══════════════════════════════════════════════════════════════════
    # Inspection
    # ══════════════════════════════════════════════════════════════════

    def inspect_artifact(self, artifact_id: str) -> Dict[str, Any]:
        """Return full canonical information for an artifact."""
        artifact = self._store.get_artifact(artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(f"Artifact not found: {artifact_id}")

        verbatim = self._store.get_verbatim(artifact_id)
        structural = self._store.get_structural(artifact_id)
        semantic = self._store.get_semantic(artifact_id)
        relations = self._store.get_relations_involving(artifact_id)

        return {
            "artifact": {
                "artifact_id": artifact.artifact_id,
                "source_id": artifact.source_id,
                "artifact_type": artifact.artifact_type.value,
                "content_hash": artifact.content_hash,
                "created_at": artifact.created_at,
            },
            "verbatim": {
                "raw_text": verbatim.raw_text if verbatim else None,
                "char_start": verbatim.char_start if verbatim else None,
                "char_end": verbatim.char_end if verbatim else None,
            } if verbatim else None,
            "structural": {
                "path": structural.path if structural else None,
                "depth": structural.depth if structural else None,
                "ordinal": structural.ordinal if structural else None,
                "parent": structural.parent_artifact_id if structural else None,
                "prev": structural.prev_artifact_id if structural else None,
                "next": structural.next_artifact_id if structural else None,
            } if structural else None,
            "semantic": {
                "backend": semantic.semantic_backend if semantic else None,
                "norm": semantic.norm if semantic else None,
                "has_vector": bool(semantic.feature_blob) if semantic else False,
            } if semantic else None,
            "relations": [
                {
                    "relation_id": r.relation_id,
                    "from_id": r.from_id,
                    "to_id": r.to_id,
                    "type": r.relation_type.value,
                    "weight": r.weight,
                }
                for r in relations
            ],
        }

    def list_neighbors(
        self,
        artifact_id: str,
        depth: int = 1,
    ) -> List[Dict[str, Any]]:
        """Return typed neighbors for an artifact up to *depth* hops."""
        from ..projection.neighborhood import expand_neighborhood

        node_ids, relations = expand_neighborhood(
            seed_ids=[artifact_id],
            store=self._store,
            config=self._config,
            radius=depth,
            max_nodes=200,
        )

        # Remove the query artifact itself
        node_ids.discard(artifact_id)

        results = []
        for nid in node_ids:
            art = self._store.get_artifact(nid)
            if art is None:
                continue
            rels = [r for r in relations if r.from_id == nid or r.to_id == nid]
            results.append({
                "artifact_id": nid,
                "type": art.artifact_type.value,
                "relations": [
                    {"type": r.relation_type.value, "weight": r.weight}
                    for r in rels
                ],
            })

        return results

    # ══════════════════════════════════════════════════════════════════
    # Diagnostics
    # ══════════════════════════════════════════════════════════════════

    def stats(self) -> Dict[str, Any]:
        """Return aggregate counts and capabilities for diagnostics."""
        base = {
            "artifacts": self._store.count_artifacts(),
            "relations": self._store.count_relations(),
            "sources": self._store.count_sources(),
        }

        # Embedder info
        base["embedder"] = self.embedder_info()

        # Evidence runtime info
        rt = self.evidence_runtime
        if rt is not None:
            base["evidence_bag"] = {
                "available": True,
                "node_count": rt.node_count(),
                "mode": rt.config.packing_strategy.value,
            }
        else:
            base["evidence_bag"] = {"available": False}

        return base
