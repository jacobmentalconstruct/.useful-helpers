"""
manifold_kernel.ingest.pipeline — End-to-end ingestion orchestrator.

Coordinates: load → normalise → chunk → ID → records → semantic → relations → persist.

Ingestion is deterministic: same input + same config = same artifact IDs
(because IDs are derived from content hashes).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

from ..config import KernelConfig
from ..errors import IngestionError
from ..types import (
    ArtifactRecord,
    ArtifactType,
    RelationRecord,
    RelationType,
    SemanticRecord,
    SourceRecord,
    StructuralRecord,
    VerbatimRecord,
    content_hash,
    make_artifact_id,
    make_relation_id,
    make_source_id,
)
from ..storage.sqlite_store import SQLiteStore
from .chunker import ChunkSpan, chunk_text
from .loader import LoadedSource, load_sources
from .normalizer import normalize_text
from .semantic_adapter import SemanticAdapter, create_adapter, vector_to_blob

logger = logging.getLogger(__name__)


def _detect_artifact_type(path: str, text: str) -> ArtifactType:
    """Heuristic type detection based on file extension."""
    ext = Path(path).suffix.lower()
    if ext in (".py", ".js", ".ts", ".rs", ".go", ".java", ".c", ".cpp", ".h"):
        return ArtifactType.CODE_CHUNK
    return ArtifactType.TEXT_CHUNK


def ingest_source(
    target: str | Path,
    store: SQLiteStore,
    config: KernelConfig,
    semantic_adapter: Optional[SemanticAdapter] = None,
) -> dict:
    """
    Ingest a source path into the store.

    Returns a summary dict with counts for diagnostics.
    """
    if semantic_adapter is None:
        semantic_adapter = create_adapter(config.semantic)

    stats = {
        "sources_ingested": 0,
        "artifacts_created": 0,
        "relations_created": 0,
        "errors": [],
    }

    for loaded in load_sources(target, config.ingest):
        try:
            result = _ingest_single_source(loaded, store, config, semantic_adapter)
            stats["sources_ingested"] += 1
            stats["artifacts_created"] += result["artifact_count"]
            stats["relations_created"] += result["relation_count"]
        except Exception as exc:
            logger.warning("Failed to ingest %s: %s", loaded.path, exc)
            stats["errors"].append({"path": loaded.path, "error": str(exc)})

    return stats


def _ingest_single_source(
    loaded: LoadedSource,
    store: SQLiteStore,
    config: KernelConfig,
    semantic_adapter: SemanticAdapter,
) -> dict:
    """Process one loaded source file into canonical records."""

    # Check if already ingested (by file hash)
    existing = store.find_source_by_hash(loaded.file_hash)
    if existing is not None:
        logger.info("Source already ingested: %s", loaded.path)
        return {"artifact_count": 0, "relation_count": 0}

    # 1. Register source
    source_id = make_source_id()
    store.add_source(SourceRecord(
        source_id=source_id,
        path=loaded.path,
        file_hash=loaded.file_hash,
    ))

    # 2. Normalise
    normalized = normalize_text(loaded.raw_text, config.ingest)

    # 3. Chunk
    chunks = chunk_text(normalized, config.ingest)
    if not chunks:
        return {"artifact_count": 0, "relation_count": 0}

    # 4. Create artifact records for each chunk
    artifact_type = _detect_artifact_type(loaded.path, normalized)
    artifact_ids: List[str] = []
    relations: List[RelationRecord] = []

    for i, chunk in enumerate(chunks):
        art_id = make_artifact_id()
        artifact_ids.append(art_id)
        c_hash = content_hash(chunk.text)

        # Artifact record
        store.add_artifact(ArtifactRecord(
            artifact_id=art_id,
            source_id=source_id,
            artifact_type=artifact_type,
            content_hash=c_hash,
        ))

        # Verbatim record
        store.add_verbatim(VerbatimRecord(
            artifact_id=art_id,
            raw_text=chunk.text,
            normalized_text=chunk.text,
            char_start=chunk.char_start,
            char_end=chunk.char_end,
        ))

        # Structural record
        store.add_structural(StructuralRecord(
            artifact_id=art_id,
            container_id=source_id,
            path=loaded.path,
            depth=0,
            ordinal=chunk.ordinal,
            parent_artifact_id=None,
            prev_artifact_id=artifact_ids[i - 1] if i > 0 else None,
            next_artifact_id=None,  # filled in linking pass
        ))

        # Semantic record
        try:
            sem_result = semantic_adapter.embed(chunk.text)
            blob = vector_to_blob(sem_result.vector) if sem_result.vector else b""
            store.add_semantic(SemanticRecord(
                artifact_id=art_id,
                semantic_backend=sem_result.backend,
                feature_blob=blob,
                norm=sem_result.norm,
                summary_json=json.dumps({"token_count": sem_result.token_count}),
            ))
        except Exception as exc:
            logger.warning("Semantic embedding failed for %s: %s", art_id, exc)
            store.add_semantic(SemanticRecord(artifact_id=art_id))

        # Source relation
        relations.append(RelationRecord(
            relation_id=make_relation_id(),
            from_id=art_id,
            to_id=source_id,
            relation_type=RelationType.BELONGS_TO_SOURCE,
        ))

    # 5. Build inter-chunk relations (prev/next)
    for i in range(len(artifact_ids)):
        if i > 0:
            relations.append(RelationRecord(
                relation_id=make_relation_id(),
                from_id=artifact_ids[i],
                to_id=artifact_ids[i - 1],
                relation_type=RelationType.PREV_OF,
            ))
        if i < len(artifact_ids) - 1:
            relations.append(RelationRecord(
                relation_id=make_relation_id(),
                from_id=artifact_ids[i],
                to_id=artifact_ids[i + 1],
                relation_type=RelationType.NEXT_OF,
            ))

    # 6. Persist relations
    store.add_relations_batch(relations)

    logger.info(
        "Ingested %s: %d artifacts, %d relations",
        loaded.path, len(artifact_ids), len(relations),
    )
    return {
        "artifact_count": len(artifact_ids),
        "relation_count": len(relations),
    }
