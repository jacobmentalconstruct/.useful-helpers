"""
FILE:       tools/event_log/cli.py
ROLE:       Read the governance event log  -  the audit trail of invoke() calls.
DOMAIN:     tool
DOES:       recent: last N events. summary: counts per tool (calls, ok, authority).
            tool: events for one tool_id. rollup: a journal-ready governance summary
            (calls/ok/fail, denials, by-authority, top tools) + `markdown`. Read-only.
DEPENDS ON: tools._toolkit, (stdlib) os, sqlite3, pathlib
WIRES TO:   invoked by src/core/invoke.py; reads <state_root>/event_log.sqlite3
NOTES:      Pairs with src/core/event_log.py (the writer). Honors SUITE_EVENT_LOG_DB override.
            Never stores or exposes argument values  -  only hashes + key names are logged.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from tools._toolkit import state_root, tool_main


def _db() -> Path:
    override = os.environ.get("SUITE_EVENT_LOG_DB")
    if override:
        return Path(override)
    return state_root() / "event_log.sqlite3"


@tool_main
def run(args: dict) -> dict:
    db = _db()
    if not db.is_file():
        return {"tool": "event_log", "action": args.get("action", "recent"),
                "count": 0, "events": [], "note": "no events recorded yet"}
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    try:
        action = str(args.get("action", "recent")).lower()
        limit = int(args.get("limit", 50))

        if action == "summary":
            total = conn.execute("SELECT COUNT(*) n, COALESCE(SUM(ok),0) oks FROM events").fetchone()
            rows = conn.execute(
                "SELECT tool_id, authority, COUNT(*) n, COALESCE(SUM(ok),0) oks "
                "FROM events GROUP BY tool_id ORDER BY n DESC LIMIT ?", (limit,)).fetchall()
            return {"tool": "event_log", "action": "summary",
                    "total": total["n"], "ok_total": total["oks"], "fail_total": total["n"] - total["oks"],
                    "by_tool": [{"tool_id": r["tool_id"], "authority": r["authority"],
                                 "calls": r["n"], "ok": r["oks"], "fail": r["n"] - r["oks"]} for r in rows]}

        if action == "rollup":
            t = conn.execute("SELECT COUNT(*) n, COALESCE(SUM(ok),0) oks, MIN(ts) lo, MAX(ts) hi FROM events").fetchone()
            n, oks = t["n"], t["oks"]
            denials = conn.execute("SELECT COUNT(*) n FROM events WHERE error LIKE 'authority denied%'").fetchone()["n"]
            by_auth = conn.execute("SELECT authority, COUNT(*) n, COALESCE(SUM(ok),0) oks "
                                   "FROM events GROUP BY authority ORDER BY n DESC").fetchall()
            top = conn.execute("SELECT tool_id, COUNT(*) n FROM events GROUP BY tool_id ORDER BY n DESC LIMIT 8").fetchall()
            recent_denials = conn.execute("SELECT ts, tool_id, error FROM events WHERE error LIKE 'authority denied%' "
                                          "ORDER BY event_id DESC LIMIT 5").fetchall()
            md = ["## Governance rollup", "",
                  f"- Window: {t['lo']} -> {t['hi']}",
                  f"- Calls: {n} (ok {oks}, fail {n - oks})",
                  f"- **Authority denials: {denials}**",
                  "- By authority: " + ", ".join(f"{r['authority']}={r['n']}" for r in by_auth),
                  "- Top tools: " + ", ".join(f"{r['tool_id']}({r['n']})" for r in top)]
            if recent_denials:
                md += ["", "Recent denials:"] + [f"- {r['ts'][11:19]} {r['tool_id']}: {r['error']}" for r in recent_denials]
            return {"tool": "event_log", "action": "rollup",
                    "window": {"from": t["lo"], "to": t["hi"]},
                    "total": n, "ok_total": oks, "fail_total": n - oks, "denials": denials,
                    "by_authority": [{"authority": r["authority"], "calls": r["n"], "ok": r["oks"]} for r in by_auth],
                    "top_tools": [{"tool_id": r["tool_id"], "calls": r["n"]} for r in top],
                    "recent_denials": [dict(r) for r in recent_denials],
                    "markdown": "\n".join(md) + "\n"}

        if action == "tool":
            tid = args.get("tool_id")
            if not tid:
                return {"ok": False, "error": "action 'tool' requires 'tool_id'"}
            rows = conn.execute(
                "SELECT event_id, ts, tool_id, authority, category, ok, exit_code, duration_ms, "
                "arg_keys, error, client FROM events WHERE tool_id=? ORDER BY event_id DESC "
                "LIMIT ?",
                (str(tid), limit)).fetchall()
            return {"tool": "event_log", "action": "tool", "tool_id": tid,
                    "count": len(rows), "events": [dict(r) for r in rows]}

        # `client` is projected because WHO called is half of an audit trail. The seam has
        # always recorded it correctly - `cli` and `agent` are passed at both entrances and
        # `record` never writes NULL - but every read projection here omitted the column,
        # so the attribution was complete in the database and absent at the only interface
        # anyone reads it through. A ledger you cannot ask "who did this" is a log.
        rows = conn.execute(
            "SELECT event_id, ts, tool_id, authority, ok, duration_ms, error, client "
            "FROM events ORDER BY event_id DESC LIMIT ?", (limit,)).fetchall()
        return {"tool": "event_log", "action": "recent",
                "count": len(rows), "events": [dict(r) for r in rows]}
    finally:
        conn.close()
