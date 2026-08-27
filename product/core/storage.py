from __future__ import annotations

import sqlite3
from pathlib import Path

from .constants import DATABASE_SCHEMA_VERSION
from .instance import InstanceContext


class StorageError(RuntimeError):
    pass


def database_path(context: InstanceContext) -> Path:
    return context.state_root / "workbench.sqlite3"


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = FULL")
    return connection


def _migrate(connection: sqlite3.Connection) -> None:
    version = int(connection.execute("PRAGMA user_version").fetchone()[0])
    if version > DATABASE_SCHEMA_VERSION:
        raise StorageError(
            f"database schema {version} is newer than this runtime supports "
            f"({DATABASE_SCHEMA_VERSION})"
        )
    if version == 0:
        with connection:
            connection.execute(
                """
                CREATE TABLE instances (
                    instance_uuid TEXT PRIMARY KEY,
                    instance_schema_version INTEGER NOT NULL,
                    product_version TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    target_relation TEXT NOT NULL CHECK (target_relation = '..')
                )
                """
            )
            connection.execute("PRAGMA user_version = 1")
        version = 1
    if version < 2:
        with connection:
            connection.execute(
                """
                CREATE TABLE operational_artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    digest TEXT NOT NULL,
                    body_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE operation_receipts (
                    receipt_id TEXT PRIMARY KEY,
                    instance_uuid TEXT NOT NULL REFERENCES instances(instance_uuid),
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    client TEXT NOT NULL,
                    tool_id TEXT NOT NULL,
                    authority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_code TEXT,
                    result_ok INTEGER,
                    exit_code INTEGER,
                    duration_ms INTEGER,
                    manifest_digest TEXT,
                    artifact_id TEXT REFERENCES operational_artifacts(artifact_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE app_journal_entries (
                    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    entry_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE app_journal_links (
                    link_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    entry_id INTEGER NOT NULL REFERENCES app_journal_entries(entry_id)
                        ON DELETE CASCADE,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL
                )
                """
            )
            connection.execute("PRAGMA user_version = 2")
        version = 2
    if version < 3:
        with connection:
            connection.execute(
                """
                CREATE TABLE resources (
                    resource_id TEXT PRIMARY KEY,
                    handle TEXT NOT NULL UNIQUE,
                    path TEXT NOT NULL UNIQUE,
                    kind TEXT NOT NULL,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    latest_version_id TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE epistemic_evidence (
                    evidence_id TEXT PRIMARY KEY,
                    digest TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    body_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE resource_versions (
                    version_id TEXT PRIMARY KEY,
                    resource_id TEXT NOT NULL REFERENCES resources(resource_id),
                    observed_at TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    content_hash TEXT,
                    size_bytes INTEGER,
                    mtime_ns INTEGER,
                    evidence_id TEXT NOT NULL REFERENCES epistemic_evidence(evidence_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE observations (
                    observation_id TEXT PRIMARY KEY,
                    producer TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    subject_handle TEXT NOT NULL,
                    observation_type TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    evidence_id TEXT NOT NULL REFERENCES epistemic_evidence(evidence_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE claims (
                    claim_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    claim_type TEXT NOT NULL,
                    statement TEXT NOT NULL,
                    derivation_method TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    data_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE relations (
                    relation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    subject_type TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object_type TEXT NOT NULL,
                    object_id TEXT NOT NULL
                )
                """
            )
            connection.execute(f"PRAGMA user_version = {DATABASE_SCHEMA_VERSION}")
        version = 3
    if version < 4:
        with connection:
            connection.execute(
                """
                CREATE TABLE awareness_revisions (
                    awareness_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    basis_status TEXT NOT NULL,
                    basis_signature TEXT,
                    target_signature TEXT,
                    summary_json TEXT NOT NULL,
                    limitations_json TEXT NOT NULL,
                    unknowns_json TEXT NOT NULL,
                    source_handles_json TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE awareness_items (
                    item_id TEXT PRIMARY KEY,
                    awareness_id TEXT NOT NULL REFERENCES awareness_revisions(awareness_id),
                    item_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    statement TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    source_handles_json TEXT NOT NULL,
                    provenance_json TEXT NOT NULL
                )
                """
            )
            connection.execute(f"PRAGMA user_version = {DATABASE_SCHEMA_VERSION}")


def _instances_table_exists(connection: sqlite3.Connection) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'instances'"
        ).fetchone()
        is not None
    )


def _verify_existing_identity(connection: sqlite3.Connection, context: InstanceContext) -> None:
    if not _instances_table_exists(connection):
        return
    rows = connection.execute("SELECT instance_uuid FROM instances").fetchall()
    if rows and (len(rows) != 1 or rows[0]["instance_uuid"] != context.instance_uuid):
        raise StorageError(
            "SQLite instance identity does not agree with instance.json; refusing re-entry"
        )


def bootstrap(context: InstanceContext) -> Path:
    path = database_path(context)
    connection = _connect(path)
    try:
        _verify_existing_identity(connection, context)
        _migrate(connection)
        rows = connection.execute("SELECT * FROM instances").fetchall()
        if not rows:
            with connection:
                connection.execute(
                    "INSERT INTO instances VALUES (?, ?, ?, ?, ?)",
                    (
                        context.instance_uuid,
                        context.schema_version,
                        context.product_version,
                        context.created_at,
                        context.target_relation,
                    ),
                )
        else:
            _verify_existing_identity(connection, context)
    finally:
        connection.close()
    return path


def connect(context: InstanceContext) -> sqlite3.Connection:
    path = bootstrap(context)
    connection = _connect(path)
    try:
        _verify_existing_identity(connection, context)
    except Exception:
        connection.close()
        raise
    return connection
