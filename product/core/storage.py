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
