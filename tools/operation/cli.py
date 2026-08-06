"""
FILE:       tools/operation/cli.py
ROLE:       Recovery surface - start, advance, PAUSE, and RESUME a multi-step effort across crashes.
DOMAIN:     tool
DOES:       action=start: open an operation (title + goal + optional planned steps).
            action=step: record a step outcome (idempotent by key; failed steps need a class).
            action=pause: park the operation with a witness of the target now.
            action=resume: RE-OBSERVE first - report stale_witness on drift, else continue.
            action=finish|abandon: close it. action=list|show: the recovery inspection surface.
DEPENDS ON: tools._toolkit (state_root, project_root), tools.operations_shared
WIRES TO:   invoked by src/core/invoke.py. Ledger at <state_root>/operations.sqlite3; sits above
            the event log (correlates raw calls into a resumable unit), separate from journal.
NOTES:      The ledger records what OCCURRED; it does not execute steps. An agent runs the real
            tools through the seam and reports each outcome here, so an interruption at any point
            leaves a durable, resumable record instead of a lost conversation. `list`/`show` are
            the read-only recovery surface; `resume` is the one that re-observes before trusting
            the paused world.
"""
from __future__ import annotations

from tools import operations_shared as ops
from tools._toolkit import project_root, state_root, tool_main

_DB = "operations.sqlite3"


def _conn():
    return ops.open_db(state_root() / _DB)


@tool_main
def run(args: dict) -> dict:
    action = str(args.get("action") or "list").lower()
    conn = _conn()
    try:
        if action == "start":
            title = str(args.get("title") or "").strip()
            if not title:
                return {"ok": False, "error": "title is required to start an operation"}
            op = ops.start_op(conn, title, str(args.get("goal") or ""),
                              args.get("steps") if isinstance(args.get("steps"), list) else None)
            return {"tool": "operation", "action": "start", "op_id": op["op_id"], "operation": op}

        if action == "step":
            op_id = str(args.get("op_id") or "")
            if not op_id:
                return {"ok": False, "error": "op_id is required"}
            r = ops.record_step(
                conn, op_id, tool=str(args.get("tool") or ""),
                args_hash=str(args.get("args_hash") or ""),
                status=str(args.get("status") or ops.STEP_DONE),
                failure_class=args.get("failure_class"),
                result_ref=str(args.get("result_ref") or ""),
                note=str(args.get("note") or ""),
                idempotency_key=args.get("idempotency_key"))
            if not r.get("ok"):
                return r
            return {"tool": "operation", "action": "step", **r}

        if action == "pause":
            op_id = str(args.get("op_id") or "")
            if not op_id:
                return {"ok": False, "error": "op_id is required"}
            r = ops.pause_op(conn, op_id, project_root(),
                             resume_hint=str(args.get("resume_hint") or ""),
                             note=str(args.get("note") or ""))
            return r if not r.get("ok") else {"tool": "operation", "action": "pause", **r}

        if action == "resume":
            op_id = str(args.get("op_id") or "")
            if not op_id:
                return {"ok": False, "error": "op_id is required"}
            r = ops.resume_op(conn, op_id, project_root())
            return r if not r.get("ok") else {"tool": "operation", "action": "resume", **r}

        if action in ("finish", "abandon"):
            op_id = str(args.get("op_id") or "")
            if not op_id:
                return {"ok": False, "error": "op_id is required"}
            status = ops.DONE if action == "finish" else ops.ABANDONED
            r = ops.set_status(conn, op_id, status, reason=str(args.get("reason") or ""))
            return r if not r.get("ok") else {"tool": "operation", "action": action, **r}

        if action == "list":
            rows = ops.list_ops(conn, args.get("status"), int(args.get("limit", 50)))
            return {"tool": "operation", "action": "list", "count": len(rows), "operations": rows}

        if action == "show":
            op_id = str(args.get("op_id") or "")
            if not op_id:
                return {"ok": False, "error": "op_id is required"}
            op = ops.show_op(conn, op_id)
            if not op:
                return {"ok": False, "error": f"no such operation {op_id}"}
            return {"tool": "operation", "action": "show", "operation": op}

        return {"ok": False, "error": f"unknown action {action!r}; "
                "use start|step|pause|resume|finish|abandon|list|show"}
    finally:
        conn.close()
