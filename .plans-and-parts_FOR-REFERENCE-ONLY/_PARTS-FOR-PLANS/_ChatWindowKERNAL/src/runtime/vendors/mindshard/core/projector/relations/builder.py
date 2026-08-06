"""
manifold_kernel.relations.builder — Post-ingestion relation generation.

Builds semantic neighbor relations by comparing embeddings across
artifacts.  This runs after ingestion to create cross-artifact semantic
edges that the projection engine can walk.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from ..config import KernelConfig
from ..errors import StorageError
from ..storage.sqlite_store import SQLiteStore
from ..types import RelationRecord, RelationType, make_relation_id
from ..ingest.semantic_adapter import SemanticAdapter, blob_to_vector

logger = logging.getLogger(__name__)


def build_semantic_neighbors(
    store: SQLiteStore,
    semantic_adapter: SemanticAdapter,
    config: KernelConfig,
    threshold: float = 0.3,
    max_neighbors: int = 5,
) -> int:
    """
    Scan all semantic records and create SEMANTIC_NEIGHBOR relations
    for artifact pairs whose cosine similarity exceeds *threshold*.

    Returns the number of new relations created.
    """
    # Load all semantic records that have vectors
    records = store.list_semantic_by_backend(semantic_adapter.backend_name)
    if len(records) < 2:
        return 0

    # Build ID -> vector map
    vectors = {}
    for rec in records:
        vec = blob_to_vector(rec.feature_blob)
        if vec:
            vectors[rec.artifact_id] = vec

    if len(vectors) < 2:
        return 0

    ids = list(vectors.keys())
    new_relations: List[RelationRecord] = []

    for i in range(len(ids)):
        similarities = []
        for j in range(len(ids)):
            if i == j:
                continue
            sim = semantic_adapter.similarity(vectors[ids[i]], vectors[ids[j]])
            if sim >= threshold:
                similarities.append((ids[j], sim))

        # Keep only top-K neighbors
        similarities.sort(key=lambda x: x[1], reverse=True)
        for neighbor_id, sim in similarities[:max_neighbors]:
            new_relations.append(RelationRecord(
                relation_id=make_relation_id(),
                from_id=ids[i],
                to_id=neighbor_id,
                relation_type=RelationType.SEMANTIC_NEIGHBOR,
                weight=sim,
            ))

    if new_relations:
        store.add_relations_batch(new_relations)
        logger.info("Created %d semantic neighbor relations", len(new_relations))

    return len(new_relations)
