"""
FILE:       tools/memory_flush/cli.py
ROLE:       Summarize a session memory log into a durable flush artifact.
DOMAIN:     tool
DOES:       Reads JSONL session events, builds a compact summary, and optionally writes it.
DEPENDS ON: tools._toolkit, tools.memory_workflow_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      PATTERN from _theCELL CognitiveMemoryMS flush hook, without vector DB dependency.
"""
from __future__ import annotations

import json

from tools import memory_workflow_shared as mw
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        name = str(args.get("session") or "default")
        paths = mw.session_paths(name, str(args.get("root") or ""))
        events = mw.read_jsonl(paths["memory"])
        summary = mw.summarize_events(events, limit=int(args.get("limit", 12)))
        markdown = [
            f"# Session Flush: {mw.slug(name)}",
            "",
            f"- Events: {summary['events']}",
            f"- Roles: {json.dumps(summary['roles'], sort_keys=True)}",
            f"- Kinds: {json.dumps(summary['kinds'], sort_keys=True)}",
            f"- Top terms: {', '.join(summary['top_terms'])}",
            "",
            "## Recent Highlights",
        ]
        for item in summary["highlights"]:
            markdown.append(f"- {item.get('role')} / {item.get('kind')}: {item.get('preview')}")
        body = "\n".join(markdown).rstrip() + "\n"
        out = mw.workspace_path(str(args.get("out"))) if args.get("out") else paths["flush"]
        written = False
        if args.get("write"):
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(body, encoding="utf-8")
            written = True
        return {"tool": "memory_flush", "session": mw.slug(name), "summary": summary,
                "markdown": body, "out": out.as_posix(), "written": written}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
