"""
FILE:       tools/evidence/cli.py
ROLE:       Bag of Evidence  -  content-addressed, verifiable evidence items grounding claims.
DOMAIN:     tool
DOES:       attach: hash a body, store it once (CAS dedup), record a typed evidence item
            (kind/summary/source/attached_to). verify: re-hash the stored body -> verified|
            corrupted. list/show/get: read items or retrieve a stored body. Store:
            <state_root>/evidence.sqlite3 (override with `db` for tests).
DEPENDS ON: tools._toolkit, (stdlib) sqlite3, hashlib, json, uuid, datetime, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Apply authority)
NOTES:      CAS integrity anchor + attach/verify. The fold/synthesis (graph-of-graphs)
            layer is deferred. Pairs with tools/journal (claim + proof).
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from tools._toolkit import state_root, tool_main

_DB_NAME = "evidence.sqlite3"

_VALID_KINDS = ("file_excerpt", "tool_output", "diff", "screenshot",
                "citation", "external", "scan_summary", "git_observation")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS blobs (
  hash TEXT PRIMARY KEY, content TEXT NOT NULL, content_type TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS evidence (
  evidence_id TEXT PRIMARY KEY,
  hash TEXT NOT NULL,
  kind TEXT,
  summary TEXT,
  source_path TEXT,
  source_line_range TEXT,
  attached_to TEXT,
  attached_to_type TEXT,
  status TEXT NOT NULL DEFAULT 'attached',
  created_at TEXT,
  verified_at TEXT,
  actor_id TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _home() -> Path:
    # Durable memory lives in the STATE ROOT, not the work-target cwd and not among the
    # disposable artifacts (roots contract: tools._toolkit).
    return state_root()


def _conn(args: dict):
    import sqlite3
    db = Path(args["db"]) if args.get("db") else _home() / _DB_NAME
    db.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(db))
    c.execute("PRAGMA journal_mode=OFF")
    c.row_factory = sqlite3.Row
    c.executescript(_SCHEMA)
    return c


@tool_main
def run(args: dict) -> dict:
    action = str(args.get("action", "list")).lower()
    c = _conn(args)
    try:
        if action == "attach":
            if args.get("body_json") is not None:
                body, content_type = json.dumps(args["body_json"], sort_keys=True), "application/json"
            elif args.get("body") is not None:
                body, content_type = str(args["body"]), str(args.get("content_type", "text/plain"))
            else:
                return {"ok": False, "error": "attach needs 'body' or 'body_json'"}

            kind = str(args.get("kind", "external"))
            warn = None if kind in _VALID_KINDS else f"non-standard kind {kind!r} (allowed)"
            h = _sha256(body)
            existed = c.execute("SELECT 1 FROM blobs WHERE hash=?", (h,)).fetchone() is not None
            if not existed:
                c.execute("INSERT INTO blobs(hash, content, content_type, created_at) VALUES (?,?,?,?)",
                          (h, body, content_type, _now()))
            evidence_id = "evd_" + uuid.uuid4().hex[:10]
            c.execute(
                "INSERT INTO evidence(evidence_id, hash, kind, summary, source_path, "
                "source_line_range, attached_to, attached_to_type, status, created_at, actor_id) "
                "VALUES (?,?,?,?,?,?,?,?, 'attached', ?, ?)",
                (evidence_id, h, kind, str(args.get("summary", "")), args.get("source_path"),
                 args.get("source_line_range"), args.get("attached_to"),
                 args.get("attached_to_type"), _now(), str(args.get("actor", "agent"))),
            )
            c.commit()
            out = {"tool": "evidence", "action": "attach", "evidence_id": evidence_id,
                   "hash": h, "kind": kind, "deduped": existed}
            if warn:
                out["warning"] = warn
            return out

        if action == "verify":
            eid = args.get("evidence_id")
            if not eid:
                return {"ok": False, "error": "verify needs 'evidence_id'"}
            row = c.execute("SELECT hash FROM evidence WHERE evidence_id=?", (eid,)).fetchone()
            if not row:
                return {"ok": False, "error": f"no such evidence: {eid}"}
            blob = c.execute("SELECT content FROM blobs WHERE hash=?", (row["hash"],)).fetchone()
            ok = blob is not None and _sha256(blob["content"]) == row["hash"]
            status = "verified" if ok else "corrupted"
            c.execute("UPDATE evidence SET status=?, verified_at=? WHERE evidence_id=?",
                      (status, _now(), eid))
            c.commit()
            return {"tool": "evidence", "action": "verify", "evidence_id": eid,
                    "hash": row["hash"], "verified": ok, "status": status}

        if action == "list":
            clauses, params = [], []
            if args.get("kind"):
                clauses.append("kind=?")
                params.append(str(args["kind"]))
            if args.get("attached_to"):
                clauses.append("attached_to=?")
                params.append(str(args["attached_to"]))
            where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
            params.append(int(args.get("limit", 50)))
            rows = c.execute(
                "SELECT evidence_id, hash, kind, summary, attached_to, status, created_at "
                f"FROM evidence{where} ORDER BY created_at DESC LIMIT ?", params).fetchall()
            return {"tool": "evidence", "action": "list", "count": len(rows),
                    "evidence": [dict(r) for r in rows]}

        if action == "show":
            eid = args.get("evidence_id")
            row = c.execute("SELECT * FROM evidence WHERE evidence_id=?", (eid,)).fetchone()
            if not row:
                return {"ok": False, "error": f"no such evidence: {eid}"}
            rec = dict(row)
            if args.get("include_body"):
                blob = c.execute("SELECT content FROM blobs WHERE hash=?", (row["hash"],)).fetchone()
                rec["body"] = blob["content"] if blob else None
            return {"tool": "evidence", "action": "show", "entry": rec}

        if action == "get":
            h = args.get("hash")
            if not h and args.get("evidence_id"):
                row = c.execute("SELECT hash FROM evidence WHERE evidence_id=?", (args["evidence_id"],)).fetchone()
                h = row["hash"] if row else None
            if not h:
                return {"ok": False, "error": "get needs 'hash' or 'evidence_id'"}
            blob = c.execute("SELECT content, content_type FROM blobs WHERE hash=?", (h,)).fetchone()
            if not blob:
                return {"ok": False, "error": f"no blob for hash {h}"}
            return {"tool": "evidence", "action": "get", "hash": h,
                    "content_type": blob["content_type"], "content": blob["content"]}

        return {"ok": False, "error": f"unknown action {action!r}; use attach|verify|list|show|get"}
    finally:
        c.close()
