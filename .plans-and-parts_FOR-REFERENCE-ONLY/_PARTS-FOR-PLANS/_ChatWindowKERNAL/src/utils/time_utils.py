"""
Owns: timestamp formatting helpers shared by runtime and persistence code.
Does not own: scheduling, lifecycle sequencing, or status semantics.
Collaborates with: logging, snapshots, and crash reporting.
"""

from __future__ import annotations

from datetime import datetime, timezone


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def compact_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
