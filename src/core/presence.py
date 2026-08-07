"""
FILE:       src/core/presence.py
ROLE:       Presence - what is TRUE NOW, as opposed to what happened.
DOMAIN:     core
DOES:       Holds a single overwritten snapshot of the current working context, with a
            monotonic tick, so either party can ask what the other is doing.
DEPENDS ON: src.core.config (Paths), (stdlib) json, os, pathlib, datetime
WIRES TO:   read by any client wanting the other's context; cleared at the composition
            root on startup
NOTES:      The second of the seam's TWO channels. The ledger answers "what happened":
            append-only, durable, audited, one row per governed action. Presence
            answers "what is true now": overwritten, ephemeral, unaudited, lossy.

            They are separated because they have opposite requirements, and merging
            them was the mistake waiting to happen. Tool calls are coarse and
            deliberate - a real engagement produced 143 of them - but UI state changes
            thousands of times an hour. Ledgering selection would have grown the audit
            trail by three orders of magnitude and buried the governed actions inside
            it.

            The decisive move is that presence is STATE, NOT EVENTS. An agent asking
            "what is the operator looking at" gets an answer, rather than replaying
            four hundred selection events to reconstruct one. State does not grow;
            that dissolves the size problem structurally instead of compressing it.

            EPHEMERAL BY DESIGN: it is dropped on restart. Nothing here is worth
            keeping - if it would still matter tomorrow it belongs in the ledger.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

# The whole vocabulary. A closed set on purpose: presence must stay a fixed-shape
# snapshot, and an open dict is how a snapshot quietly becomes a log.
FIELDS = (
    "target_root",           # which project is bound
    "browse_selection",      # what is being inspected - zero or one item
    "operation_inclusion",   # what the next operation may consider
    "active_chain",          # which chain is running, if any
    "active_step",           # where in that chain
)


def path(paths) -> Path:
    """Presence lives in the state root, as ONE file that is overwritten."""
    override = os.environ.get("SUITE_PRESENCE_FILE")
    if override:
        return Path(override)
    return Path(paths.state) / "presence.json"


def read(paths) -> dict | None:
    """The current snapshot, or None if nothing is present."""
    p = path(paths)
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def update(paths, **fields) -> dict:
    """Merge fields into the snapshot and bump the tick. OVERWRITES; never appends.

    Unknown keys are dropped rather than stored. That is what keeps presence a fixed
    shape: without it, one caller stashing a list here turns the snapshot into an
    accumulating log with none of the ledger's guarantees.
    """
    p = path(paths)
    p.parent.mkdir(parents=True, exist_ok=True)
    current = read(paths) or {}
    for key, value in fields.items():
        if key in FIELDS:
            current[key] = value
    current["tick"] = int(current.get("tick", 0)) + 1
    current["updated_at"] = datetime.now(timezone.utc).isoformat()
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(current, indent=1, sort_keys=True), encoding="utf-8")
    os.replace(tmp, p)      # atomic: a reader never sees a half-written snapshot
    return current


def clear(paths) -> None:
    """Drop presence. This is what a restart does.

    Called at the composition root so a new session never inherits the last one's
    context - stale presence is worse than none, because it answers confidently.
    """
    p = path(paths)
    try:
        if p.is_file():
            p.unlink()
    except OSError:
        # A filesystem that denies unlink cannot drop it; truncate to the empty
        # snapshot instead, so a stale context is never reported as current.
        try:
            p.write_text("{}", encoding="utf-8")
        except OSError:
            pass
