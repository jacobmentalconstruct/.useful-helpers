"""
FILE:       tools/sqlite_exec/cli.py
ROLE:       Governed SQLite writes (the write half of sqlite_inspect).
DOMAIN:     tool
DOES:       Execute one parameterized write statement (INSERT/UPDATE/DELETE/REPLACE or DDL) against
            a SQLite DB confined to the roots. Preview-first: runs inside a transaction and reports
            the affected-row count, then ROLLS BACK unless applied  -  so the preview is accurate and
            non-destructive. SELECT is refused (use sqlite_inspect).
DEPENDS ON: tools._toolkit, (stdlib) sqlite3
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Apply authority)
            need governed writes)
NOTES:      One statement per call, parameterized (`params`) to avoid injection. The rollback-preview
            means `dry_run` tells you exactly how many rows an UPDATE/DELETE would touch, safely.
"""
from __future__ import annotations

import sqlite3

from tools._toolkit import confirmed, resolve_within_roots, tool_main

_WRITE_VERBS = ("insert", "update", "delete", "replace", "create", "drop", "alter")


def _verb(sql: str) -> str:
    return sql.strip().split(None, 1)[0].lower() if sql.strip() else ""


@tool_main
def run(args: dict) -> dict:
    sql = str(args.get("sql") or "").strip()
    if not sql:
        return {"ok": False, "error": "sql is required"}
    verb = _verb(sql)
    if verb == "select" or verb == "pragma":
        return {"ok": False, "error": "sqlite_exec is for writes; use sqlite_inspect to read"}
    if verb not in _WRITE_VERBS:
        return {"ok": False, "error": f"unsupported statement {verb!r}; use {list(_WRITE_VERBS)}"}
    db, err = resolve_within_roots(args.get("db", ""))
    if err:
        return {"ok": False, "error": err}
    params = args.get("params")
    if params is not None and not isinstance(params, (list, tuple)):
        return {"ok": False, "error": "params must be a list"}

    apply = confirmed(args)
    if not db.exists() and not apply:
        # A preview must not touch the filesystem  -  sqlite3.connect() would CREATE the file.
        return {"tool": "sqlite_exec", "dry_run": True, "db": db.as_posix(),
                "statement": verb, "would_affect_rows": None, "committed": False,
                "note": "database does not exist yet; it would be created on apply",
                "apply_with": {"apply": True}}
    # isolation_level=None -> no implicit transactions; BEGIN/COMMIT/ROLLBACK are ours alone,
    # so the rollback-preview is predictable across Python versions.
    conn = sqlite3.connect(str(db), isolation_level=None)
    try:
        conn.execute("BEGIN")
        try:
            cur = conn.execute(sql, list(params) if params else [])
        except sqlite3.Error as e:
            conn.rollback()
            return {"ok": False, "tool": "sqlite_exec", "error": f"{type(e).__name__}: {e}",
                    "sql": sql}
        affected = cur.rowcount  # -1 for DDL; row count for DML
        if apply:
            conn.commit()
            return {"tool": "sqlite_exec", "dry_run": False, "db": db.as_posix(),
                    "statement": verb, "affected_rows": affected, "committed": True}
        conn.rollback()
        return {"tool": "sqlite_exec", "dry_run": True, "db": db.as_posix(),
                "statement": verb, "would_affect_rows": affected, "committed": False,
                "apply_with": {"apply": True}}
    finally:
        conn.close()
