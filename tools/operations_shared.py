"""
FILE:       tools/operations_shared.py
ROLE:       The operation ledger - make a multi-step effort DURABLE and RESUMABLE across crashes.
DOMAIN:     tool (shared substrate)
DOES:       A SQLite ledger of operations and their ordered steps. start/advance/pause/resume/
            finish/abandon an operation; each step carries an explicit status and, on failure, an
            explicit FAILURE CLASS (never a generic "failed"). Pause stores a durable park packet +
            a witness (a signature of the target at pause time); resume RE-OBSERVES first and
            reports drift (stale_witness) instead of blindly continuing. Idempotency keys stop a
            resumed operation from re-running a step whose effect already landed.
DEPENDS ON: (stdlib) hashlib, json, os, sqlite3, time, pathlib
WIRES TO:   tools/operation (the CLI surface). Sits ABOVE src/core/event_log (the raw per-call
            tape): an operation correlates calls into a resumable unit. SEPARATE storage from
            journal/evidence - different record class, different truth semantics.
NOTES:      Pure functions over an explicit db path (and, for the witness, an explicit root), so
            the whole lifecycle is testable without a display or a live target. The ledger records
            what HAPPENED; it does not execute steps itself - the agent/orchestrator runs the real
            tools through the seam and reports each outcome here. That separation is deliberate:
            the ledger's truth is "what occurred", not "what a tool claimed".
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path

# Explicit failure taxonomy - a generic "failed" is exactly the ambiguity recovery must remove.
FAILURE_CLASSES = {
    "proposal_rejected",              # authority/validator declined before any effect
    "capability_unavailable",         # the tool/resource was not available
    "timeout",                        # exceeded its time budget
    "no_effect",                      # ran, changed nothing it should have
    "partial_effect",                 # changed some but not all of the intended state
    "effect_ok_observation_failed",   # the change landed but we could not confirm it
    "observation_ok_validation_failed",  # observed, but the result failed validation
    "stale_witness",                  # the target drifted since the operation paused
    "malformed_output",               # the tool/Brain returned unusable output
    "runtime_crash",                  # the process died mid-step
}

OPEN, PAUSED, DONE, FAILED, ABANDONED = "open", "paused", "done", "failed", "abandoned"
_LIVE = {OPEN, PAUSED}

STEP_PENDING, STEP_RUNNING, STEP_DONE, STEP_FAILED = "pending", "running", "done", "failed"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS operations (
  op_id       TEXT PRIMARY KEY,
  title       TEXT NOT NULL,
  goal        TEXT,
  status      TEXT NOT NULL DEFAULT 'open',
  witness     TEXT,
  park_packet TEXT,
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS op_steps (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  op_id           TEXT NOT NULL,
  step_no         INTEGER NOT NULL,
  tool            TEXT,
  args_hash       TEXT,
  idempotency_key TEXT,
  status          TEXT NOT NULL DEFAULT 'running',
  failure_class   TEXT,
  result_ref      TEXT,
  note            TEXT,
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL,
  UNIQUE(op_id, idempotency_key)
);
"""

_SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "_artifacts", "_state",
              ".useful-helpers", "node_modules", ".pytest_cache"}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def open_db(path) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def witness(root) -> str:
    """A signature of the target's material NOW - sorted (relpath, size) hashed. Cheap enough to
    take on pause/resume; sensitive enough to catch an external edit. Bounded to keep a giant
    target from making park/resume slow."""
    root = Path(root)
    rows: list[str] = []
    for cur, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in _SKIP_DIRS)
        for name in sorted(files):
            p = Path(cur) / name
            try:
                rel = p.relative_to(root).as_posix()
                rows.append(f"{rel}:{p.stat().st_size}")
            except (OSError, ValueError):
                continue
            if len(rows) >= 20000:
                break
        if len(rows) >= 20000:
            break
    h = hashlib.sha256("\n".join(sorted(rows)).encode("utf-8")).hexdigest()
    return f"{len(rows)}:{h[:32]}"


# ---------------------------------------------------------------- lifecycle
def start_op(conn, title: str, goal: str = "", steps: list | None = None) -> dict:
    op_id = uuid.uuid4().hex
    now = _now()
    conn.execute("INSERT INTO operations(op_id,title,goal,status,created_at,updated_at) "
                 "VALUES(?,?,?,?,?,?)", (op_id, title, goal, OPEN, now, now))
    for i, s in enumerate(steps or [], start=1):
        tool = (s or {}).get("tool") if isinstance(s, dict) else str(s)
        note = (s or {}).get("note") if isinstance(s, dict) else ""
        conn.execute("INSERT INTO op_steps(op_id,step_no,tool,status,note,created_at,updated_at) "
                     "VALUES(?,?,?,?,?,?,?)", (op_id, i, tool, STEP_PENDING, note, now, now))
    conn.commit()
    return show_op(conn, op_id)


def _next_step_no(conn, op_id: str) -> int:
    row = conn.execute("SELECT MAX(step_no) AS m FROM op_steps WHERE op_id=?", (op_id,)).fetchone()
    return (row["m"] or 0) + 1


def record_step(conn, op_id: str, *, tool: str = "", args_hash: str = "",
                status: str = STEP_DONE, failure_class: str | None = None,
                result_ref: str = "", note: str = "",
                idempotency_key: str | None = None) -> dict:
    """Append or update a step. Idempotent: if a step with the same idempotency_key already exists
    for this operation, its record is RETURNED unchanged rather than re-applied - so a resumed
    operation never re-runs a step whose effect already landed."""
    op = conn.execute("SELECT status FROM operations WHERE op_id=?", (op_id,)).fetchone()
    if op is None:
        return {"ok": False, "error": f"no such operation {op_id}"}
    if failure_class is not None and failure_class not in FAILURE_CLASSES:
        return {"ok": False, "error": f"unknown failure_class {failure_class!r}",
                "known": sorted(FAILURE_CLASSES)}
    if status == STEP_FAILED and failure_class is None:
        return {"ok": False, "error": "a failed step requires an explicit failure_class"}

    # Normalize an empty key to NULL: SQLite allows many NULLs under UNIQUE but only ONE "" - two
    # keyless steps passed as "" would collide and raise. Only a real (truthy) key dedupes.
    idempotency_key = idempotency_key or None

    if idempotency_key:
        existing = conn.execute(
            "SELECT * FROM op_steps WHERE op_id=? AND idempotency_key=?",
            (op_id, idempotency_key)).fetchone()
        if existing is not None:
            return {"ok": True, "idempotent_hit": True, "step": dict(existing)}

    now = _now()
    step_no = _next_step_no(conn, op_id)
    conn.execute(
        "INSERT INTO op_steps(op_id,step_no,tool,args_hash,idempotency_key,status,failure_class,"
        "result_ref,note,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (op_id, step_no, tool, args_hash, idempotency_key, status, failure_class,
         result_ref, note, now, now))
    # a failed step fails the operation (with the class visible on the step)
    new_status = FAILED if status == STEP_FAILED else OPEN
    conn.execute("UPDATE operations SET status=?, updated_at=? WHERE op_id=? AND status=?",
                 (new_status, now, op_id, OPEN))
    conn.commit()
    return {"ok": True, "idempotent_hit": False, "step_no": step_no,
            "op_status": show_op(conn, op_id)["status"]}


def pause_op(conn, op_id: str, root, *, resume_hint: str = "", note: str = "") -> dict:
    op = conn.execute("SELECT status FROM operations WHERE op_id=?", (op_id,)).fetchone()
    if op is None:
        return {"ok": False, "error": f"no such operation {op_id}"}
    if op["status"] not in _LIVE:
        return {"ok": False, "error": f"cannot pause an operation in status {op['status']!r}"}
    w = witness(root)
    packet = {"resume_hint": resume_hint, "note": note, "witness": w, "paused_at": _now()}
    conn.execute("UPDATE operations SET status=?, witness=?, park_packet=?, updated_at=? WHERE op_id=?",
                 (PAUSED, w, json.dumps(packet), _now(), op_id))
    conn.commit()
    return {"ok": True, "op_id": op_id, "status": PAUSED, "park_packet": packet}


def resume_op(conn, op_id: str, root) -> dict:
    """Re-observe BEFORE continuing. If the target drifted since pause, report stale_witness with
    the evidence rather than resuming onto a changed world."""
    op = conn.execute("SELECT * FROM operations WHERE op_id=?", (op_id,)).fetchone()
    if op is None:
        return {"ok": False, "error": f"no such operation {op_id}"}
    if op["status"] != PAUSED:
        return {"ok": False, "error": f"operation is {op['status']!r}, not paused"}
    packet = json.loads(op["park_packet"] or "{}")
    then = packet.get("witness")
    now = witness(root)
    drifted = (then is not None and now != then)
    detail = show_op(conn, op_id)
    done_steps = [s for s in detail["steps"] if s["status"] == STEP_DONE]
    pending = [s for s in detail["steps"] if s["status"] == STEP_PENDING]
    if drifted:
        return {"ok": True, "resumed": False, "drift": True, "failure_class": "stale_witness",
                "witness_then": then, "witness_now": now,
                "message": "the target changed since this operation paused; re-observe and "
                           "reconcile before continuing",
                "park_packet": packet, "done_steps": done_steps, "pending_steps": pending}
    conn.execute("UPDATE operations SET status=?, updated_at=? WHERE op_id=?", (OPEN, _now(), op_id))
    conn.commit()
    return {"ok": True, "resumed": True, "drift": False, "park_packet": packet,
            "done_steps": done_steps, "pending_steps": pending,
            "already_done_keys": [s["idempotency_key"] for s in done_steps if s["idempotency_key"]]}


def set_status(conn, op_id: str, status: str, *, reason: str = "") -> dict:
    op = conn.execute("SELECT status FROM operations WHERE op_id=?", (op_id,)).fetchone()
    if op is None:
        return {"ok": False, "error": f"no such operation {op_id}"}
    now = _now()
    note = None
    if status == ABANDONED and reason:
        packet = {"abandoned_reason": reason, "at": now}
        note = json.dumps(packet)
        conn.execute("UPDATE operations SET status=?, park_packet=?, updated_at=? WHERE op_id=?",
                     (status, note, now, op_id))
    else:
        conn.execute("UPDATE operations SET status=?, updated_at=? WHERE op_id=?",
                     (status, now, op_id))
    conn.commit()
    return {"ok": True, "op_id": op_id, "status": status}


def list_ops(conn, status: str | None = None, limit: int = 50) -> list[dict]:
    if status:
        rows = conn.execute("SELECT * FROM operations WHERE status=? ORDER BY updated_at DESC LIMIT ?",
                            (status, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM operations ORDER BY updated_at DESC LIMIT ?",
                            (limit,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d.pop("park_packet", None)
        out.append(d)
    return out


def show_op(conn, op_id: str) -> dict:
    op = conn.execute("SELECT * FROM operations WHERE op_id=?", (op_id,)).fetchone()
    if op is None:
        return {}
    steps = conn.execute("SELECT * FROM op_steps WHERE op_id=? ORDER BY step_no", (op_id,)).fetchall()
    d = dict(op)
    if d.get("park_packet"):
        try:
            d["park_packet"] = json.loads(d["park_packet"])
        except (ValueError, TypeError):
            pass
    d["steps"] = [dict(s) for s in steps]
    return d
