"""
FILE:       tools/session_replay/cli.py
ROLE:       Replay a recorded session memory log.
DOMAIN:     tool
DOES:       Reads workspace-local session JSONL and emits timeline/transcript summaries.
DEPENDS ON: tools._toolkit, tools.memory_workflow_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from _theCELL session restore/replay behavior.
"""
from __future__ import annotations

from tools import memory_workflow_shared as mw
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        name = str(args.get("session") or "default")
        paths = mw.session_paths(name, str(args.get("root") or ""))
        events = mw.read_jsonl(paths["memory"])
        role = str(args.get("role") or "")
        kind = str(args.get("kind") or "")
        if role:
            events = [e for e in events if e.get("role") == role]
        if kind:
            events = [e for e in events if e.get("kind", "message") == kind]
        limit = int(args.get("limit", 50))
        rows = events[-max(1, min(limit, 500)):]
        transcript = "\n\n".join(f"{e.get('role','note').upper()}: {e.get('content','')}" for e in rows)
        return {"tool": "session_replay", "session": mw.slug(name), "events": rows,
                "transcript": transcript, "summary": mw.summarize_events(events)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
