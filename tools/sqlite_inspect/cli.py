"""
FILE:       tools/sqlite_inspect/cli.py
ROLE:       SQLite database schema inspector.
DOMAIN:     tool
DOES:       Read tables, columns, indexes, counts, and optional sample rows from a SQLite DB.
DEPENDS ON: tools._toolkit, (stdlib) sqlite3, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Read-only: schema, rows, counts. Writes live elsewhere.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from tools._toolkit import tool_main


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


@tool_main
def run(args: dict) -> dict:
    db = Path(args.get("db") or args.get("path") or "")
    if not db:
        return {"ok": False, "error": "'db' path is required"}
    db = db.resolve()
    project = Path.cwd().resolve()
    try:
        db.relative_to(project)
    except ValueError:
        return {"ok": False, "error": "db must stay inside the project workspace"}
    if not db.exists():
        return {"ok": False, "error": f"db not found: {db}"}

    include_samples = bool(args.get("include_samples", False))
    sample_limit = max(1, min(int(args.get("sample_limit", 3)), 20))
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    try:
        tables = []
        rows = conn.execute(
            "SELECT name, type, sql FROM sqlite_master WHERE type IN ('table','view') "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        for r in rows:
            name = r["name"]
            columns = [dict(c) for c in conn.execute(f"PRAGMA table_info({_quote(name)})").fetchall()]
            indexes = [dict(i) for i in conn.execute(f"PRAGMA index_list({_quote(name)})").fetchall()]
            count = None
            samples = []
            if r["type"] == "table":
                count = conn.execute(f"SELECT COUNT(*) AS n FROM {_quote(name)}").fetchone()["n"]
                if include_samples:
                    samples = [dict(x) for x in conn.execute(f"SELECT * FROM {_quote(name)} LIMIT ?", (sample_limit,)).fetchall()]
            tables.append({"name": name, "type": r["type"], "columns": columns,
                           "indexes": indexes, "row_count": count, "samples": samples})
        return {"tool": "sqlite_inspect", "db": db.as_posix(), "table_count": len(tables), "tables": tables}
    finally:
        conn.close()
