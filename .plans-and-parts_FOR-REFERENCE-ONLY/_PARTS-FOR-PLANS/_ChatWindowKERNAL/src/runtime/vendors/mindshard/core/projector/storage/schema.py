"""
manifold_kernel.storage.schema — SQLite DDL for the canonical record tables.

Six core tables map one-to-one with the plan's record types:
artifacts, verbatim, structural, semantic, relations, sources.

Schema is initialised via init_schema() which is idempotent.
"""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 1

_DDL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ── Sources ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sources (
    source_id       TEXT PRIMARY KEY,
    path            TEXT NOT NULL,
    file_hash       TEXT NOT NULL,
    ingested_at     TEXT NOT NULL,
    metadata_json   TEXT NOT NULL DEFAULT '{}'
);

-- ── Artifacts ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id     TEXT PRIMARY KEY,
    source_id       TEXT NOT NULL,
    artifact_type   TEXT NOT NULL,
    content_hash    TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    metadata_json   TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);

-- ── Verbatim dimension ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS verbatim (
    artifact_id     TEXT PRIMARY KEY,
    raw_text        TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    byte_start      INTEGER NOT NULL DEFAULT 0,
    byte_end        INTEGER NOT NULL DEFAULT 0,
    char_start      INTEGER NOT NULL DEFAULT 0,
    char_end        INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id)
);

-- ── Structural dimension ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS structural (
    artifact_id         TEXT PRIMARY KEY,
    container_id        TEXT NOT NULL DEFAULT '',
    path                TEXT NOT NULL DEFAULT '',
    depth               INTEGER NOT NULL DEFAULT 0,
    ordinal             INTEGER NOT NULL DEFAULT 0,
    parent_artifact_id  TEXT,
    prev_artifact_id    TEXT,
    next_artifact_id    TEXT,
    FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id)
);

-- ── Semantic dimension ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS semantic (
    artifact_id       TEXT PRIMARY KEY,
    semantic_backend  TEXT NOT NULL DEFAULT 'none',
    feature_blob      BLOB NOT NULL DEFAULT x'',
    norm              REAL NOT NULL DEFAULT 0.0,
    summary_json      TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id)
);

-- ── Relations ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS relations (
    relation_id     TEXT PRIMARY KEY,
    from_id         TEXT NOT NULL,
    to_id           TEXT NOT NULL,
    relation_type   TEXT NOT NULL,
    weight          REAL NOT NULL DEFAULT 1.0,
    metadata_json   TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_relations_from ON relations(from_id);
CREATE INDEX IF NOT EXISTS idx_relations_to   ON relations(to_id);
CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation_type);
CREATE INDEX IF NOT EXISTS idx_artifacts_source ON artifacts(source_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_hash   ON artifacts(content_hash);

-- ── Schema metadata ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all tables if they don't exist. Idempotent."""
    conn.executescript(_DDL)
    conn.execute(
        "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?)",
        ("schema_version", str(SCHEMA_VERSION)),
    )
    conn.commit()


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Return current schema version or 0 if uninitialised."""
    try:
        row = conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema_version'"
        ).fetchone()
        return int(row[0]) if row else 0
    except sqlite3.OperationalError:
        return 0
