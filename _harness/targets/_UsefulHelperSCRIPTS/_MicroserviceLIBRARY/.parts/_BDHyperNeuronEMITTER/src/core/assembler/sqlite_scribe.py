"""sqlite_scribe.py — Cold Artifact writer (cold_anatomy.db schema + write ops).

Ownership: core/assembler/sqlite_scribe.py

Creates and populates the Cold Artifact SQLite database consumed by
``core/engine/inference/retrieval.py``.

Cold Artifact Schema
--------------------
content_nodes
    hunk_id       TEXT PRIMARY KEY
    node_kind     TEXT NOT NULL
    content       TEXT NOT NULL
    attention_weight REAL NOT NULL DEFAULT 1.0
    static_mass   INTEGER NOT NULL DEFAULT 0   -- len(content) in chars

occurrence_nodes
    occurrence_id TEXT PRIMARY KEY
    hunk_id       TEXT NOT NULL   -- FK → content_nodes.hunk_id
    origin_id     TEXT NOT NULL   -- source file / document
    structural_path TEXT NOT NULL DEFAULT ''
    vector_blob   BLOB            -- packed float32 SVD vector (struct '<Nf')

relations
    source_occ_id TEXT NOT NULL
    op            TEXT NOT NULL   -- edge predicate (registered in relations.py)
    target_occ_id TEXT NOT NULL
    weight        REAL NOT NULL
    routing_profile TEXT NOT NULL  -- JSON {surface: float}
    interaction_mode TEXT NOT NULL -- InteractionType label
    interaction_vector TEXT NOT NULL  -- JSON [float, ...]
    PRIMARY KEY (source_occ_id, op, target_occ_id)

inhibit_edges
    token_a  TEXT NOT NULL
    token_b  TEXT NOT NULL
    weight   REAL NOT NULL
    PRIMARY KEY (token_a, token_b)

content_fts
    FTS5 virtual table over content_nodes.content (content= option).

Boundary rule: this module ONLY WRITES. It does not read from the database
beyond the initial schema creation check. Reads belong to retrieval.py.

No v1 counterpart — original for the v2 Cold Artifact design.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import struct
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

# ── Schema DDL ─────────────────────────────────────────────────────────────

_DDL = """
CREATE TABLE IF NOT EXISTS content_nodes (
    hunk_id          TEXT    PRIMARY KEY,
    node_kind        TEXT    NOT NULL,
    content          TEXT    NOT NULL,
    attention_weight REAL    NOT NULL DEFAULT 1.0,
    static_mass      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS occurrence_nodes (
    occurrence_id   TEXT PRIMARY KEY,
    hunk_id         TEXT NOT NULL,
    origin_id       TEXT NOT NULL,
    structural_path TEXT NOT NULL DEFAULT '',
    vector_blob     BLOB
);

CREATE TABLE IF NOT EXISTS relations (
    source_occ_id    TEXT NOT NULL,
    op               TEXT NOT NULL,
    target_occ_id    TEXT NOT NULL,
    weight           REAL NOT NULL,
    routing_profile  TEXT NOT NULL DEFAULT '{}',
    interaction_mode TEXT NOT NULL DEFAULT '',
    interaction_vector TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (source_occ_id, op, target_occ_id)
);

CREATE TABLE IF NOT EXISTS inhibit_edges (
    token_a TEXT NOT NULL,
    token_b TEXT NOT NULL,
    weight  REAL NOT NULL,
    PRIMARY KEY (token_a, token_b)
);

CREATE VIRTUAL TABLE IF NOT EXISTS content_fts USING fts5(
    content,
    content=content_nodes,
    content_rowid=rowid
);
"""

# Triggers to keep the FTS index in sync with content_nodes inserts/deletes.
# Using "content=" FTS5 means updates must be managed manually.
_FTS_TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS content_nodes_ai
AFTER INSERT ON content_nodes BEGIN
    INSERT INTO content_fts(rowid, content)
    VALUES (new.rowid, new.content);
END;

CREATE TRIGGER IF NOT EXISTS content_nodes_ad
AFTER DELETE ON content_nodes BEGIN
    INSERT INTO content_fts(content_fts, rowid, content)
    VALUES ('delete', old.rowid, old.content);
END;

CREATE TRIGGER IF NOT EXISTS content_nodes_au
AFTER UPDATE ON content_nodes BEGIN
    INSERT INTO content_fts(content_fts, rowid, content)
    VALUES ('delete', old.rowid, old.content);
    INSERT INTO content_fts(rowid, content)
    VALUES (new.rowid, new.content);
END;
"""


# ── Vector packing ─────────────────────────────────────────────────────────

def _pack_vector(vec: List[float]) -> bytes:
    """Pack a float list to little-endian float32 blob."""
    return struct.pack(f"<{len(vec)}f", *vec)


# ── SqliteScribe ───────────────────────────────────────────────────────────

class SqliteScribe:
    """Writes HyperHunks and Nucleus results into a Cold Artifact SQLite database.

    Parameters
    ----------
    db_path : Path or str
        File path for the SQLite database.  Created if it does not exist.
    batch_size : int
        How many upsert operations to accumulate before flushing.
        Default 200.  Lower values reduce memory pressure on large corpora.
    """

    def __init__(self, db_path: "Path | str", batch_size: int = 200) -> None:
        self.db_path = Path(db_path)
        self.batch_size = batch_size
        self._conn: Optional[sqlite3.Connection] = None
        self._pending: int = 0
        self._open()

    def _open(self) -> None:
        log.debug("Opening Cold Artifact: %s", self.db_path)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript(_DDL)
        self._conn.executescript(_FTS_TRIGGERS)
        self._conn.commit()

    # ── Upsert operations ─────────────────────────────────────────────────

    def upsert_hunk(self, hunk: "Any") -> None:
        """Write a HyperHunk's content node and occurrence node.

        Uses INSERT OR IGNORE so duplicate hunk_ids are safe (CIS model).
        Occurrence nodes use INSERT OR REPLACE to allow vector_blob updates.

        Parameters
        ----------
        hunk : HyperHunk (Emitter extension)
            Must have: hunk_id, occurrence_id, node_kind, content,
            attention_weight, origin_id, structural_path.
            Optional: embedding (List[float] or None).
        """
        assert self._conn is not None

        attention = getattr(hunk, "attention_weight", 1.0)
        static_mass = len(hunk.content)
        embedding: Optional[List[float]] = getattr(hunk, "embedding", None)
        vector_blob: Optional[bytes] = _pack_vector(embedding) if embedding else None

        self._conn.execute(
            """INSERT OR IGNORE INTO content_nodes
               (hunk_id, node_kind, content, attention_weight, static_mass)
               VALUES (?, ?, ?, ?, ?)""",
            (hunk.hunk_id, hunk.node_kind, hunk.content, attention, static_mass),
        )

        self._conn.execute(
            """INSERT OR REPLACE INTO occurrence_nodes
               (occurrence_id, hunk_id, origin_id, structural_path, vector_blob)
               VALUES (?, ?, ?, ?, ?)""",
            (
                hunk.occurrence_id,
                hunk.hunk_id,
                hunk.origin_id,
                hunk.structural_path,
                vector_blob,
            ),
        )

        self._pending += 1
        self._maybe_flush()

    def write_relation(
        self,
        source_occ_id: str,
        op: str,
        target_occ_id: str,
        weight: float,
        routing_profile: Optional[Dict[str, float]] = None,
        interaction_mode: str = "",
        interaction_vector: Optional[List[float]] = None,
    ) -> None:
        """Write a single directed relation edge.

        Uses INSERT OR REPLACE — if the same (source, op, target) triple
        is encountered again, the newer weight wins.

        Parameters
        ----------
        source_occ_id, target_occ_id : str
            Must reference existing occurrence_nodes rows.
        op : str
            Edge predicate name (registered in relations.py).
        weight : float
            Coupling weight ≥ 0.
        routing_profile : dict or None
            {surface: float} Nucleus routing profile.
        interaction_mode : str
            InteractionType label from the Nucleus.
        interaction_vector : list[float] or None
            Raw [S_grammatical, S_structural, S_statistical, S_semantic, S_verbatim].
        """
        assert self._conn is not None

        profile_json = json.dumps(routing_profile or {})
        vector_json = json.dumps(interaction_vector or [])

        self._conn.execute(
            """INSERT OR REPLACE INTO relations
               (source_occ_id, op, target_occ_id, weight,
                routing_profile, interaction_mode, interaction_vector)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                source_occ_id, op, target_occ_id, weight,
                profile_json, interaction_mode, vector_json,
            ),
        )

        self._pending += 1
        self._maybe_flush()

    def write_inhibit_edge(
        self,
        token_a: str,
        token_b: str,
        weight: float,
    ) -> None:
        """Write a token-level inhibit edge (strong NPMI anti-correlation pair).

        Uses INSERT OR REPLACE — larger weight wins for duplicate pairs.
        Pair is canonicalized: token_a ≤ token_b lexicographically.
        """
        assert self._conn is not None

        ta, tb = (token_a, token_b) if token_a <= token_b else (token_b, token_a)

        # Take max weight if pair already exists
        existing = self._conn.execute(
            "SELECT weight FROM inhibit_edges WHERE token_a=? AND token_b=?",
            (ta, tb),
        ).fetchone()

        if existing is None or weight > existing[0]:
            self._conn.execute(
                """INSERT OR REPLACE INTO inhibit_edges (token_a, token_b, weight)
                   VALUES (?, ?, ?)""",
                (ta, tb, weight),
            )
            self._pending += 1
            self._maybe_flush()

    def update_vector(self, occurrence_id: str, vector: List[float]) -> None:
        """Update the vector_blob for an existing occurrence node.

        Use this for a second-pass embedding after the initial ingest.
        """
        assert self._conn is not None
        self._conn.execute(
            "UPDATE occurrence_nodes SET vector_blob=? WHERE occurrence_id=?",
            (_pack_vector(vector), occurrence_id),
        )
        self._pending += 1
        self._maybe_flush()

    # ── Training data export ───────────────────────────────────────────────

    def export_training_pairs(self) -> List[Dict]:
        """Export all relations as training tuples for Phase 2 FFN.

        Each tuple contains the routing_profile and interaction metadata
        needed to train the FFN Nucleus on Phase 1's edge decisions.

        Returns
        -------
        list of dict with keys:
            source_occ_id, target_occ_id, op, weight,
            routing_profile, interaction_mode, interaction_vector
        """
        assert self._conn is not None
        self.flush()
        rows = self._conn.execute(
            """SELECT source_occ_id, op, target_occ_id, weight,
                      routing_profile, interaction_mode, interaction_vector
               FROM relations"""
        ).fetchall()
        return [
            {
                "source_occ_id":    r[0],
                "op":               r[1],
                "target_occ_id":    r[2],
                "weight":           r[3],
                "routing_profile":  json.loads(r[4]),
                "interaction_mode": r[5],
                "interaction_vector": json.loads(r[6]),
            }
            for r in rows
        ]

    # ── Stats ──────────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, int]:
        """Return row counts for each table."""
        assert self._conn is not None
        self.flush()
        tables = ["content_nodes", "occurrence_nodes", "relations", "inhibit_edges"]
        return {
            t: self._conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for t in tables
        }

    # ── Flush / close ──────────────────────────────────────────────────────

    def _maybe_flush(self) -> None:
        if self._pending >= self.batch_size:
            self.flush()

    def flush(self) -> None:
        """Commit any pending writes to disk."""
        if self._conn is not None and self._pending > 0:
            self._conn.commit()
            log.debug("Flushed %d pending writes", self._pending)
            self._pending = 0

    def close(self) -> None:
        """Flush and close the database connection."""
        self.flush()
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            log.debug("Closed Cold Artifact: %s", self.db_path)

    def __enter__(self) -> "SqliteScribe":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
