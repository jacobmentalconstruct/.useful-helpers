"""
FILE:       src/core/event_log.py
ROLE:       Governance event log  -  the append-only audit trail of every invoke() call.
DOMAIN:     core
DOES:       record() appends one row per invocation (tool, authority, category, ok, exit_code,
            duration, args HASH + top-level key names, truncated error, UTC timestamp) to an
            append-only SQLite ledger. Never stores argument VALUES (data hygiene).
DEPENDS ON: src.core.config (Paths), (stdlib) hashlib, json, os, sqlite3, datetime, pathlib
WIRES TO:   called by src.core.invoke after every dispatch; read by tools/event_log
NOTES:      The governance attachment point at the seam. Logging must NEVER break the seam  -  all
            failures are swallowed. DB path is <state_root>/event_log.sqlite3 (see Paths.state),
            overridable via SUITE_EVENT_LOG_DB (used by tests to isolate). The .sqlite3 file is
            gitignored runtime state.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.lib.common import relativize_paths

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
  event_id    INTEGER PRIMARY KEY AUTOINCREMENT,
  ts          TEXT NOT NULL,
  tool_id     TEXT NOT NULL,
  authority   TEXT,
  category    TEXT,
  ok          INTEGER,
  exit_code   INTEGER,
  duration_ms INTEGER,
  args_hash   TEXT,
  arg_keys    TEXT,
  error       TEXT,
  client      TEXT,
  kind        TEXT
);
"""

# Columns added after the table first shipped. `CREATE TABLE IF NOT EXISTS` does
# NOTHING against an existing database, so without this an old ledger would keep its
# original ten columns while new code wrote into fields that are not there - no
# error, just a silently missing attribution. `_state/` is gitignored, so every
# machine carries a different history and both shapes must be tolerated.
_ADDED_COLUMNS = {
    "client": "TEXT",
    "kind": "TEXT",
}

# What a row is. `invocation` is a tool call through the seam; `decision` is a human
# granting or refusing authority, which is the moment authority is actually exercised.
KIND_INVOCATION = "invocation"
KIND_DECISION = "decision"

# Rows written before attribution existed. They are marked, not guessed at: inventing
# a caller for a call that never recorded one would be a fabricated audit trail.
UNKNOWN_CLIENT = "unknown"


def db_path(paths) -> Path:
    override = os.environ.get("SUITE_EVENT_LOG_DB")
    if override:
        return Path(override)
    return Path(paths.state) / "event_log.sqlite3"


def _scrub_roots(paths) -> tuple:
    """Roots for the shared scrubber, taken from the live Paths (not env  -  record() runs in
    the PARENT process, where the seam's exported env vars are not set)."""
    return ((str(getattr(paths, "project_root", paths.root)), "<project>"),
            (str(paths.root), "<toolkit>"))


def migrate(db: "Path | str") -> None:
    """Bring an existing ledger up to the current schema. Idempotent.

    Additive only: columns are appended and pre-existing rows are backfilled with
    UNKNOWN_CLIENT. Nothing is rewritten and nothing is dropped - an append-only
    audit trail that edits its own history is not an audit trail.
    """
    db = Path(db)
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    try:
        conn.executescript(_SCHEMA)
        have = {row[1] for row in conn.execute("PRAGMA table_info(events)")}
        for column, decl in _ADDED_COLUMNS.items():
            if column not in have:
                conn.execute(f"ALTER TABLE events ADD COLUMN {column} {decl}")
        # Backfill only what predates attribution. Rows written since carry their own.
        conn.execute(
            "UPDATE events SET client = ? WHERE client IS NULL", (UNKNOWN_CLIENT,))
        conn.execute(
            "UPDATE events SET kind = ? WHERE kind IS NULL", (KIND_INVOCATION,))
        conn.commit()
    finally:
        conn.close()


def read(paths, *, limit: int = 100, offset: int = 0) -> list[dict]:
    """Read the ledger, oldest first. Bounded by construction.

    The ledger was write-only: `record()` was its entire surface. Nothing could show
    an operator what an agent had done, or an agent what an operator had done, so the
    shared record existed but was unreadable by the parties it was for.
    """
    db = db_path(paths)
    if not db.is_file():
        return []
    limit = max(1, min(int(limit), 1000))
    conn = sqlite3.connect(str(db))
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM events ORDER BY event_id LIMIT ? OFFSET ?",
            (limit, max(0, int(offset))),
        ).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def count(paths) -> int:
    """How many events the ledger holds."""
    db = db_path(paths)
    if not db.is_file():
        return 0
    conn = sqlite3.connect(str(db))
    try:
        return int(conn.execute("SELECT COUNT(*) FROM events").fetchone()[0])
    except sqlite3.Error:
        return 0
    finally:
        conn.close()


def record_decision(paths, *, tool_id: str, client: str, granted: bool,
                    reason: str | None = None) -> None:
    """Record a human granting or refusing authority.

    This is the human's equivalent of a tool call, and arguably the most significant
    act in the system: it is where authority is actually exercised. Today it is a
    boolean argument buried inside a tool call, so "the agent proposed rewriting 400
    files and the operator declined" leaves no trace at all.
    """
    try:
        db = db_path(paths)
        migrate(db)
        conn = sqlite3.connect(str(db))
        try:
            conn.execute(
                "INSERT INTO events (ts, tool_id, authority, category, ok, error, "
                "client, kind) VALUES (?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), tool_id, None, "decision",
                 1 if granted else 0,
                 (reason or None), client or UNKNOWN_CLIENT, KIND_DECISION),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:  # never break the seam over its own bookkeeping
        pass


def record(paths, *, tool_id: str, authority, category, args, ok, exit_code, error,
           duration_ms, client: str = UNKNOWN_CLIENT) -> None:
    """Append one governance event. Swallows every failure  -  must never break invoke()."""
    try:
        db = db_path(paths)
        db.parent.mkdir(parents=True, exist_ok=True)
        args = args if isinstance(args, dict) else {}
        args_json = json.dumps(args, sort_keys=True, default=str)
        args_hash = hashlib.sha256(args_json.encode("utf-8")).hexdigest()
        arg_keys = json.dumps(sorted(args.keys()))
        err = relativize_paths(str(error), roots=_scrub_roots(paths))[:500] if error else None
        migrate(db)   # tolerates both shapes; idempotent
        conn = sqlite3.connect(str(db))
        try:
            conn.execute(
                "INSERT INTO events (ts, tool_id, authority, category, ok, exit_code, "
                "duration_ms, args_hash, arg_keys, error, client, kind) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), tool_id, authority, category,
                 1 if ok else 0, exit_code, duration_ms, args_hash, arg_keys, err,
                 client or UNKNOWN_CLIENT, KIND_INVOCATION),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:  # governance logging is best-effort; never crash the seam
        pass
