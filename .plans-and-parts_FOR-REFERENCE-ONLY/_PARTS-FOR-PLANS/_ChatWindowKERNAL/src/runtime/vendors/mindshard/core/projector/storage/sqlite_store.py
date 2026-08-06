"""
manifold_kernel.storage.sqlite_store — SQLite-backed canonical record store.

Explicit CRUD operations for all six record tables.  No hidden magic —
every write validates IDs and relation integrity where practical.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config import StorageConfig
from ..errors import (
    ArtifactNotFoundError,
    DuplicateArtifactError,
    SchemaError,
    StorageError,
)
from ..types import (
    ArtifactRecord,
    ArtifactType,
    RelationRecord,
    RelationType,
    SemanticRecord,
    SourceRecord,
    StructuralRecord,
    VerbatimRecord,
)
from .schema import init_schema


class SQLiteStore:
    """Low-level persistence layer wrapping a single SQLite database."""

    def __init__(self, config: StorageConfig) -> None:
        self._config = config
        self._conn: Optional[sqlite3.Connection] = None

    # ── Lifecycle ─────────────────────────────────────────────────────

    def open(self) -> None:
        """Open (or create) the database and ensure schema exists."""
        try:
            self._conn = sqlite3.connect(
                self._config.db_path,
                check_same_thread=False,
            )
            self._conn.row_factory = sqlite3.Row
            init_schema(self._conn)
        except sqlite3.Error as exc:
            raise SchemaError(f"Failed to initialise database: {exc}") from exc

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise StorageError("Store is not open. Call .open() first.")
        return self._conn

    # ── Source CRUD ───────────────────────────────────────────────────

    def add_source(self, rec: SourceRecord) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO sources (source_id, path, file_hash, ingested_at, metadata_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (rec.source_id, rec.path, rec.file_hash, rec.ingested_at, rec.metadata_json),
        )
        self.conn.commit()

    def get_source(self, source_id: str) -> Optional[SourceRecord]:
        row = self.conn.execute(
            "SELECT * FROM sources WHERE source_id = ?", (source_id,)
        ).fetchone()
        if not row:
            return None
        return SourceRecord(
            source_id=row["source_id"],
            path=row["path"],
            file_hash=row["file_hash"],
            ingested_at=row["ingested_at"],
            metadata_json=row["metadata_json"],
        )

    def find_source_by_hash(self, file_hash: str) -> Optional[SourceRecord]:
        row = self.conn.execute(
            "SELECT * FROM sources WHERE file_hash = ?", (file_hash,)
        ).fetchone()
        if not row:
            return None
        return SourceRecord(
            source_id=row["source_id"],
            path=row["path"],
            file_hash=row["file_hash"],
            ingested_at=row["ingested_at"],
            metadata_json=row["metadata_json"],
        )

    # ── Artifact CRUD ────────────────────────────────────────────────

    def add_artifact(self, rec: ArtifactRecord) -> None:
        try:
            self.conn.execute(
                "INSERT INTO artifacts (artifact_id, source_id, artifact_type, content_hash, created_at, metadata_json) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (rec.artifact_id, rec.source_id, rec.artifact_type.value, rec.content_hash, rec.created_at, rec.metadata_json),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as exc:
            raise DuplicateArtifactError(f"Artifact {rec.artifact_id} already exists") from exc

    def get_artifact(self, artifact_id: str) -> Optional[ArtifactRecord]:
        row = self.conn.execute(
            "SELECT * FROM artifacts WHERE artifact_id = ?", (artifact_id,)
        ).fetchone()
        if not row:
            return None
        return ArtifactRecord(
            artifact_id=row["artifact_id"],
            source_id=row["source_id"],
            artifact_type=ArtifactType(row["artifact_type"]),
            content_hash=row["content_hash"],
            created_at=row["created_at"],
            metadata_json=row["metadata_json"],
        )

    def list_artifacts(self, source_id: Optional[str] = None) -> List[ArtifactRecord]:
        if source_id:
            rows = self.conn.execute(
                "SELECT * FROM artifacts WHERE source_id = ? ORDER BY created_at", (source_id,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM artifacts ORDER BY created_at").fetchall()
        return [
            ArtifactRecord(
                artifact_id=r["artifact_id"],
                source_id=r["source_id"],
                artifact_type=ArtifactType(r["artifact_type"]),
                content_hash=r["content_hash"],
                created_at=r["created_at"],
                metadata_json=r["metadata_json"],
            )
            for r in rows
        ]

    # ── Verbatim CRUD ────────────────────────────────────────────────

    def add_verbatim(self, rec: VerbatimRecord) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO verbatim (artifact_id, raw_text, normalized_text, byte_start, byte_end, char_start, char_end) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (rec.artifact_id, rec.raw_text, rec.normalized_text, rec.byte_start, rec.byte_end, rec.char_start, rec.char_end),
        )
        self.conn.commit()

    def get_verbatim(self, artifact_id: str) -> Optional[VerbatimRecord]:
        row = self.conn.execute(
            "SELECT * FROM verbatim WHERE artifact_id = ?", (artifact_id,)
        ).fetchone()
        if not row:
            return None
        return VerbatimRecord(
            artifact_id=row["artifact_id"],
            raw_text=row["raw_text"],
            normalized_text=row["normalized_text"],
            byte_start=row["byte_start"],
            byte_end=row["byte_end"],
            char_start=row["char_start"],
            char_end=row["char_end"],
        )

    # ── Structural CRUD ──────────────────────────────────────────────

    def add_structural(self, rec: StructuralRecord) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO structural "
            "(artifact_id, container_id, path, depth, ordinal, parent_artifact_id, prev_artifact_id, next_artifact_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (rec.artifact_id, rec.container_id, rec.path, rec.depth, rec.ordinal,
             rec.parent_artifact_id, rec.prev_artifact_id, rec.next_artifact_id),
        )
        self.conn.commit()

    def get_structural(self, artifact_id: str) -> Optional[StructuralRecord]:
        row = self.conn.execute(
            "SELECT * FROM structural WHERE artifact_id = ?", (artifact_id,)
        ).fetchone()
        if not row:
            return None
        return StructuralRecord(
            artifact_id=row["artifact_id"],
            container_id=row["container_id"],
            path=row["path"],
            depth=row["depth"],
            ordinal=row["ordinal"],
            parent_artifact_id=row["parent_artifact_id"],
            prev_artifact_id=row["prev_artifact_id"],
            next_artifact_id=row["next_artifact_id"],
        )

    # ── Semantic CRUD ────────────────────────────────────────────────

    def add_semantic(self, rec: SemanticRecord) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO semantic (artifact_id, semantic_backend, feature_blob, norm, summary_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (rec.artifact_id, rec.semantic_backend, rec.feature_blob, rec.norm, rec.summary_json),
        )
        self.conn.commit()

    def get_semantic(self, artifact_id: str) -> Optional[SemanticRecord]:
        row = self.conn.execute(
            "SELECT * FROM semantic WHERE artifact_id = ?", (artifact_id,)
        ).fetchone()
        if not row:
            return None
        return SemanticRecord(
            artifact_id=row["artifact_id"],
            semantic_backend=row["semantic_backend"],
            feature_blob=bytes(row["feature_blob"]) if row["feature_blob"] else b"",
            norm=row["norm"],
            summary_json=row["summary_json"],
        )

    def list_semantic_by_backend(self, backend: str) -> List[SemanticRecord]:
        rows = self.conn.execute(
            "SELECT * FROM semantic WHERE semantic_backend = ?", (backend,)
        ).fetchall()
        return [
            SemanticRecord(
                artifact_id=r["artifact_id"],
                semantic_backend=r["semantic_backend"],
                feature_blob=bytes(r["feature_blob"]) if r["feature_blob"] else b"",
                norm=r["norm"],
                summary_json=r["summary_json"],
            )
            for r in rows
        ]

    # ── Relation CRUD ────────────────────────────────────────────────

    def add_relation(self, rec: RelationRecord) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO relations (relation_id, from_id, to_id, relation_type, weight, metadata_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (rec.relation_id, rec.from_id, rec.to_id, rec.relation_type.value, rec.weight, rec.metadata_json),
        )
        self.conn.commit()

    def add_relations_batch(self, recs: List[RelationRecord]) -> None:
        """Insert multiple relations in a single transaction."""
        with self.conn:
            self.conn.executemany(
                "INSERT OR REPLACE INTO relations (relation_id, from_id, to_id, relation_type, weight, metadata_json) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (r.relation_id, r.from_id, r.to_id, r.relation_type.value, r.weight, r.metadata_json)
                    for r in recs
                ],
            )

    def get_relations_from(self, artifact_id: str, relation_type: Optional[str] = None) -> List[RelationRecord]:
        if relation_type:
            rows = self.conn.execute(
                "SELECT * FROM relations WHERE from_id = ? AND relation_type = ?",
                (artifact_id, relation_type),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM relations WHERE from_id = ?", (artifact_id,)
            ).fetchall()
        return self._rows_to_relations(rows)

    def get_relations_to(self, artifact_id: str, relation_type: Optional[str] = None) -> List[RelationRecord]:
        if relation_type:
            rows = self.conn.execute(
                "SELECT * FROM relations WHERE to_id = ? AND relation_type = ?",
                (artifact_id, relation_type),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM relations WHERE to_id = ?", (artifact_id,)
            ).fetchall()
        return self._rows_to_relations(rows)

    def get_relations_involving(self, artifact_id: str) -> List[RelationRecord]:
        rows = self.conn.execute(
            "SELECT * FROM relations WHERE from_id = ? OR to_id = ?",
            (artifact_id, artifact_id),
        ).fetchall()
        return self._rows_to_relations(rows)

    def _rows_to_relations(self, rows) -> List[RelationRecord]:
        return [
            RelationRecord(
                relation_id=r["relation_id"],
                from_id=r["from_id"],
                to_id=r["to_id"],
                relation_type=RelationType(r["relation_type"]),
                weight=r["weight"],
                metadata_json=r["metadata_json"],
            )
            for r in rows
        ]

    # ── Aggregate queries ────────────────────────────────────────────

    def count_artifacts(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]

    def count_relations(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]

    def count_sources(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]

    def all_artifact_ids(self) -> List[str]:
        rows = self.conn.execute("SELECT artifact_id FROM artifacts").fetchall()
        return [r["artifact_id"] for r in rows]
