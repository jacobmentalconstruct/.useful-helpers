"""
FILE:       tools/session_record/cli.py
ROLE:       Create sessions and append JSONL memory events.
DOMAIN:     tool
DOES:       Maintains workspace-local session metadata, tasks, and memory event logs.
DEPENDS ON: tools._toolkit, tools.memory_workflow_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      REHOME (rewritten) from _theCELL SessionManager and memory_path conventions.
"""
from __future__ import annotations

from tools import memory_workflow_shared as mw
from tools._toolkit import tool_main


@tool_main
def run(args: dict) -> dict:
    try:
        action = str(args.get("action") or "append")
        name = str(args.get("session") or "default")
        root = str(args.get("root") or "")
        if action == "list":
            base = mw.workspace_path(root) if root else mw.artifact_root() / "sessions"
            sessions = []
            if base.exists():
                for child in sorted(base.iterdir()):
                    if child.is_dir() and (child / "metadata.json").exists():
                        sessions.append(mw.session_status(child.name, root))
            return {"tool": "session_record", "action": action, "sessions": sessions,
                    "summary": {"sessions": len(sessions)}}
        if action == "status":
            return {"tool": "session_record", "action": action, **mw.session_status(name, root)}
        if action == "create":
            if not args.get("write"):
                return {"ok": False, "error": "create requires write:true"}
            meta = mw.ensure_session(name, str(args.get("description") or ""), root)
            return {"tool": "session_record", "action": action, "session": meta,
                    "summary": mw.session_status(name, root)}
        if action != "append":
            return {"ok": False, "error": f"unknown action: {action}"}
        event = {
            "id": mw.fingerprint({"session": name, "at": mw.utc_now(), "content": args.get("content", "")})[:16],
            "at": mw.utc_now(),
            "role": str(args.get("role") or "note"),
            "kind": str(args.get("kind") or "message"),
            "content": str(args.get("content") or ""),
            "metadata": args.get("metadata") or {},
        }
        if not args.get("write"):
            return {"tool": "session_record", "action": action, "session": mw.slug(name),
                    "would_write": True, "event": event}
        mw.ensure_session(name, str(args.get("description") or ""), root)
        paths = mw.session_paths(name, root)
        mw.append_jsonl(paths["memory"], event)
        return {"tool": "session_record", "action": action, "session": mw.slug(name),
                "event": event, "summary": mw.session_status(name, root)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
