"""
FILE:       tools/schema_diff/cli.py
ROLE:       SQLite schema diff tool.
DOMAIN:     tool
DOES:       Compare two SQLite schemas by table, column, and index names.
DEPENDS ON: tools._toolkit, (stdlib) sqlite3, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from tools._toolkit import tool_main


def _schema(path: Path) -> dict:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        tables = {}
        for r in conn.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'"):
            name = r["name"]
            cols = [c["name"] for c in conn.execute(f'PRAGMA table_info("{name.replace(chr(34), chr(34)+chr(34))}")')]
            idx = [i["name"] for i in conn.execute(f'PRAGMA index_list("{name.replace(chr(34), chr(34)+chr(34))}")')]
            tables[name] = {"type": r["type"], "columns": cols, "indexes": idx}
        return tables
    finally:
        conn.close()


def _workspace_path(value: str) -> Path:
    p = Path(value).resolve()
    try:
        p.relative_to(Path.cwd().resolve())
    except ValueError as e:
        raise ValueError("database paths must stay inside the project workspace") from e
    if not p.exists():
        raise ValueError(f"database not found: {p}")
    return p


@tool_main
def run(args: dict) -> dict:
    left_arg = args.get("left")
    right_arg = args.get("right")
    if not left_arg or not right_arg:
        return {"ok": False, "error": "'left' and 'right' database paths are required"}
    left = _workspace_path(str(left_arg))
    right = _workspace_path(str(right_arg))
    a = _schema(left)
    b = _schema(right)
    left_tables = set(a)
    right_tables = set(b)
    common = sorted(left_tables & right_tables)
    changed = []
    for table in common:
        ac, bc = set(a[table]["columns"]), set(b[table]["columns"])
        ai, bi = set(a[table]["indexes"]), set(b[table]["indexes"])
        if ac != bc or ai != bi or a[table]["type"] != b[table]["type"]:
            changed.append({
                "table": table,
                "type_changed": a[table]["type"] != b[table]["type"],
                "columns_added": sorted(bc - ac),
                "columns_removed": sorted(ac - bc),
                "indexes_added": sorted(bi - ai),
                "indexes_removed": sorted(ai - bi),
            })
    return {
        "tool": "schema_diff",
        "left": left.as_posix(),
        "right": right.as_posix(),
        "tables_added": sorted(right_tables - left_tables),
        "tables_removed": sorted(left_tables - right_tables),
        "tables_changed": changed,
        "changed": bool((right_tables - left_tables) or (left_tables - right_tables) or changed),
    }
