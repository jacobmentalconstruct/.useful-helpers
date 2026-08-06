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
  error       TEXT
);
"""


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


def record(paths, *, tool_id: str, authority, category, args, ok, exit_code, error, duration_ms) -> None:
    """Append one governance event. Swallows every failure  -  must never break invoke()."""
    try:
        db = db_path(paths)
        db.parent.mkdir(parents=True, exist_ok=True)
        args = args if isinstance(args, dict) else {}
        args_json = json.dumps(args, sort_keys=True, default=str)
        args_hash = hashlib.sha256(args_json.encode("utf-8")).hexdigest()
        arg_keys = json.dumps(sorted(args.keys()))
        err = relativize_paths(str(error), roots=_scrub_roots(paths))[:500] if error else None
        conn = sqlite3.connect(str(db))
        try:
            conn.execute(_SCHEMA)
            conn.execute(
                "INSERT INTO events (ts, tool_id, authority, category, ok, exit_code, "
                "duration_ms, args_hash, arg_keys, error) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), tool_id, authority, category,
                 1 if ok else 0, exit_code, duration_ms, args_hash, arg_keys, err),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:  # governance logging is best-effort; never crash the seam
        pass
