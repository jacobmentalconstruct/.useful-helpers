"""
FILE:       tools/genesis/cli.py
ROLE:       The "Start New" front door - begin a project from an INTENTION, not from existing code.
DOMAIN:     tool
DOES:       Records a durable workspace identity (id + name + intent + authority + profile hint) at
            <state_root>/workspace.json and seeds the first journal entry through the governed
            seam. No domain/profile is required. Preview-first; refuses to clobber an existing
            workspace identity without overwrite.
DEPENDS ON: tools._toolkit (state_root, seam_call); (stdlib) json, uuid, datetime
WIRES TO:   invoked by src/core/invoke.py; read by tools/attach (which surfaces the intent and maps
            the workspace at whatever evidence density it has). A future planner chains
            genesis -> scaffold_project -> journal. (The chain named a fourth step,
            `sidecar_install`, until T6 deleted it: installing a sidecar is the setup
            application's job, not a runtime tool's.)
NOTES:      Genesis writes ONLY sidecar state - workspace.json in the state root, plus the journal.
            It puts NOTHING into the target's own tree: the workspace's identity and intent are the
            sidecar's memory of what the project is trying to BECOME, not an artifact imposed on
            the project. Materializing real files is scaffold_project's job, a separate step the
            agent runs next. The journal seed goes THROUGH THE SEAM (subprocess), so genesis never
            imports the journal tool (seam_call) and the seed is audit-logged like any other write;
            best-effort, so a workspace is still created if the journal is momentarily unavailable.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from tools._toolkit import apply_with, confirmed, seam_call, state_root, tool_main

WORKSPACE_FILE = "workspace.json"
_AUTHORITIES = {"Observe", "Sandbox", "Apply"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _workspace_path():
    return state_root() / WORKSPACE_FILE


def _load_workspace() -> dict:
    p = _workspace_path()
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _seed_journal(name: str, intent: str) -> bool:
    """Write the first journal entry THROUGH THE SEAM. Best-effort: a workspace is still valid if
    the journal is momentarily unreachable, so genesis never fails on this."""
    args = {
        "action": "add",
        "title": f"Genesis: {name}",
        "phase": "genesis",
        "summary": intent,
        "decisions": ["Workspace initialized from intent via genesis (Start New)."],
        "backlog": ["Define/scaffold the initial structure (scaffold_project).",
                    "attach to map the workspace as artifacts accumulate."],
    }
    return seam_call("journal", args, timeout=60)["ok"]


@tool_main
def run(args: dict) -> dict:
    intent = str(args.get("intent") or "").strip()
    if not intent:
        return {"ok": False, "error": "intent is required - state in one sentence what this "
                "project is for. Genesis begins a project from that intention."}

    name = str(args.get("name") or "").strip() or "untitled-project"
    authority = args.get("authority")
    if authority is not None and str(authority) not in _AUTHORITIES:
        return {"ok": False, "error": f"authority must be one of {sorted(_AUTHORITIES)} or omitted"}
    profile_hint = str(args.get("profile") or "").strip() or None

    existing = _load_workspace()
    plan = {
        "tool": "genesis", "name": name, "intent": intent,
        "authority": str(authority) if authority else None,
        "profile_hint": profile_hint,
        "workspace_path": _workspace_path().as_posix(),
        "would_seed_journal": True,
    }

    if not confirmed(args):
        return {**plan, "dry_run": True, "created": False,
                "already_initialized": bool(existing),
                "note": ("A workspace identity already exists here; pass overwrite:true to replace "
                         "it (its recorded intent will change)." if existing else
                         "This records a new workspace identity and seeds the first journal entry."),
                "apply_with": apply_with()}

    if existing and not args.get("overwrite"):
        return {**plan, "ok": False, "created": False, "already_initialized": True,
                "error": "a workspace identity already exists; pass overwrite:true to replace it",
                "existing": {k: existing.get(k) for k in ("workspace_id", "name", "created_at")}}

    record = {
        "workspace_id": existing.get("workspace_id") or uuid.uuid4().hex,
        "name": name,
        "intent": intent,
        "authority": str(authority) if authority else None,
        "profile_hint": profile_hint,
        "created_at": existing.get("created_at") or _now(),
        "updated_at": _now(),
        "genesis_version": 1,
    }
    path = _workspace_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    journal_seeded = _seed_journal(name, intent)

    return {
        "tool": "genesis", "created": True, "workspace": record,
        "journal_seeded": journal_seeded,
        "next": [
            {"why": "Confirm the workspace identity and read the seeded intent.",
             "call": {"tool": "attach", "args": {}}},
            {"why": "Materialize the initial structure the intent implies (dirs/files/plan).",
             "call": {"tool": "scaffold_project",
                      "args": {"action": "archetypes"}}},
            {"why": ("For a multi-step build, open a RESUMABLE operation so the effort survives "
                     "interruption (pause/resume re-observes for drift)."),
             "call": {"tool": "operation",
                      "args": {"action": "start", "title": name, "goal": intent}}},
            {"why": "Record decisions as the project takes shape, so the thread stays unbroken.",
             "call": {"tool": "journal", "args": {"action": "add", "title": "...", "summary": "..."}}},
        ],
    }
