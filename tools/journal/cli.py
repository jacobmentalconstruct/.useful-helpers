"""
FILE:       tools/journal/cli.py
ROLE:       The canonical App Journal  -  append-only SQLite operational memory (cartridge sec E).
DOMAIN:     tool
DOES:       add: append a structured entry (title/phase/summary/files/decisions/backlog).
            list/show: read entries. close: seal an entry (open->closed|parked, closeout sec E).
            export: render the committed Markdown mirror. Store:
            <state_root>/journal.sqlite3 (override with `db` for tests).
DEPENDS ON: tools._toolkit, (stdlib) sqlite3, json, uuid, datetime, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Apply authority)
NOTES:      Content is append-only; only status transitions on close. PATTERN from
            original implementation. The SQLite store is authoritative; JOURNAL.md is the
            committed human-readable mirror (the DB is gitignored as *.sqlite3).
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from tools._toolkit import state_root, tool_main

_DB_NAME = "journal.sqlite3"
_MD_NAME = "JOURNAL.md"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS journal_entries (
  uid TEXT PRIMARY KEY,
  entry_no INTEGER UNIQUE,
  created_at TEXT NOT NULL,
  title TEXT NOT NULL,
  phase TEXT,
  summary TEXT,
  files_changed TEXT,
  decisions TEXT,
  backlog TEXT,
  status TEXT NOT NULL DEFAULT 'open',
  closed_at TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_list(v) -> list[str]:
    if v is None:
        return []
    return [str(x) for x in v] if isinstance(v, list) else [str(v)]


def _home() -> Path:
    # Durable memory lives in the STATE ROOT, not the work-target cwd and not among the
    # disposable artifacts (roots contract: tools._toolkit).
    return state_root()


def _conn(args: dict) -> sqlite3.Connection:
    db = Path(args["db"]) if args.get("db") else _home() / _DB_NAME
    db.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(db))
    c.execute("PRAGMA journal_mode=OFF")
    c.row_factory = sqlite3.Row
    c.execute(_SCHEMA)
    return c


def _row(r: sqlite3.Row) -> dict:
    d = dict(r)
    for k in ("files_changed", "decisions", "backlog"):
        d[k] = json.loads(d[k]) if d.get(k) else []
    return d


def _render_md(rows: list[sqlite3.Row]) -> str:
    out = ["# App Journal", "",
           "_Authoritative store: `<state_root>/journal.sqlite3`. Generated mirror  -  "
           "do not hand-edit; write via `tools/journal`._", ""]
    for r in rows:
        d = _row(r)
        head = f"## #{d['entry_no']} - {d['title']}  `{d['uid']}`  [{d['status']}]"
        meta = f"*{d['created_at']}*" + (f" - phase: {d['phase']}" if d["phase"] else "")
        out += [head, meta]
        if d["summary"]:
            out += ["", d["summary"]]
        if d["files_changed"]:
            out += ["", "**Files:** " + ", ".join(d["files_changed"])]
        if d["decisions"]:
            out += ["", "**Decisions:**"] + [f"- {x}" for x in d["decisions"]]
        if d["backlog"]:
            out += ["", "**Backlog:**"] + [f"- {x}" for x in d["backlog"]]
        out += ["", ""]
    return "\n".join(out)


@tool_main
def run(args: dict) -> dict:
    action = str(args.get("action", "list")).lower()
    c = _conn(args)
    try:
        if action == "add":
            title = str(args.get("title", "")).strip()
            if not title:
                return {"ok": False, "error": "'title' is required for add"}
            uid = uuid.uuid4().hex[:12]
            entry_no = c.execute("SELECT COALESCE(MAX(entry_no), 0) + 1 AS n FROM journal_entries").fetchone()["n"]
            c.execute(
                "INSERT INTO journal_entries "
                "(uid, entry_no, created_at, title, phase, summary, files_changed, decisions, backlog, status) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (uid, entry_no, _now(), title, str(args.get("phase", "")), str(args.get("summary", "")),
                 json.dumps(_as_list(args.get("files"))), json.dumps(_as_list(args.get("decisions"))),
                 json.dumps(_as_list(args.get("backlog"))), str(args.get("status", "open"))),
            )
            c.commit()
            return {"tool": "journal", "action": "add", "uid": uid, "entry_no": entry_no}

        if action == "list":
            limit = int(args.get("limit", 20))
            rows = c.execute("SELECT uid, entry_no, created_at, title, phase, status "
                             "FROM journal_entries ORDER BY entry_no DESC LIMIT ?", (limit,)).fetchall()
            return {"tool": "journal", "action": "list", "count": len(rows),
                    "entries": [dict(r) for r in rows]}

        if action == "show":
            if args.get("uid"):
                r = c.execute("SELECT * FROM journal_entries WHERE uid=?", (args["uid"],)).fetchone()
            elif args.get("entry_no") is not None:
                r = c.execute("SELECT * FROM journal_entries WHERE entry_no=?", (int(args["entry_no"]),)).fetchone()
            else:
                return {"ok": False, "error": "provide 'uid' or 'entry_no'"}
            if not r:
                return {"ok": False, "error": "entry not found"}
            return {"tool": "journal", "action": "show", "entry": _row(r)}

        if action == "close":
            uid = args.get("uid")
            if not uid:
                return {"ok": False, "error": "'uid' is required for close"}
            status = str(args.get("status", "closed"))
            if status not in ("closed", "parked"):
                return {"ok": False, "error": "status must be 'closed' or 'parked'"}
            cur = c.execute("UPDATE journal_entries SET status=?, closed_at=? WHERE uid=?",
                            (status, _now(), uid))
            c.commit()
            if cur.rowcount == 0:
                return {"ok": False, "error": f"no entry with uid {uid}"}
            return {"tool": "journal", "action": "close", "uid": uid, "status": status}

        if action == "export":
            rows = c.execute("SELECT * FROM journal_entries ORDER BY entry_no ASC").fetchall()
            out = _home() / _MD_NAME
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(_render_md(rows), encoding="utf-8")
            return {"tool": "journal", "action": "export", "entries": len(rows),
                    "path": _MD_NAME}

        return {"ok": False, "error": f"unknown action {action!r}; use add|list|show|close|export"}
    finally:
        c.close()
