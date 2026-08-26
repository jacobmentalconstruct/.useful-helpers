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
            connection.execute(f"PRAGMA user_version = {DATABASE_SCHEMA_VERSION}")


def bootstrap(context: InstanceContext) -> Path:
    path = database_path(context)
    connection = _connect(path)
    try:
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
        elif len(rows) != 1 or rows[0]["instance_uuid"] != context.instance_uuid:
            raise StorageError(
                "SQLite instance identity does not agree with instance.json; refusing re-entry"
            )
    finally:
        connection.close()
    return path


def connect(context: InstanceContext) -> sqlite3.Connection:
    path = database_path(context)
    connection = _connect(path)
    try:
        _migrate(connection)
    except Exception:
        connection.close()
        raise
    return connection
