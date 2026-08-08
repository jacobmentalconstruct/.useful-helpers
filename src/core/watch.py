"""
FILE:       src/core/watch.py
ROLE:       The live channel - how a change announces itself.
DOMAIN:     core
DOES:       Hands a caller an opaque cursor, and reports what has happened since it.
DEPENDS ON: src.core.{event_log,presence}
WIRES TO:   any client wanting to observe the other party; the GUI event view (T5)
NOTES:      E6a: each party sees the other ACT. E6b - querying the other's CONTEXT -
            was met in T2 by presence, so this module is deliberately small.

            POLLED, SINGLE-WRITER, by decision at declaration rather than discovery.
            Presence has exactly one writer (whoever owns the session) and readers
            poll a monotonic tick. That makes the read-modify-write race carried
            from T2 UNREACHABLE rather than handled: no lock, no daemon, no port, no
            lifecycle to supervise, and it works cross-process on any filesystem.
            The ledger is already append-only, with SQLite managing concurrent
            appends.

            Accepted costs, stated rather than discovered: latency equals the poll
            interval, and it does not cross machines. Both are fine for a local
            sidecar, and this interface can sit unchanged in front of a socket if
            one is ever justified - callers hold a cursor, not a connection.

            MEASURED, not guessed: a poll cycle is ~0.15 ms on the slowest
            filesystem available here (event_log.count 0.115 + presence.read 0.027).
            At SUGGESTED_INTERVAL_MS that is roughly a tenth of one percent of a
            core, which is why the interval can be short enough to feel immediate.
"""
from __future__ import annotations

from typing import NamedTuple

from src.core import event_log, presence

# Chosen from the measurement above, not from intuition. Short enough that a human
# cannot distinguish it from immediate; long enough that the cost stays invisible.
SUGGESTED_INTERVAL_MS = 150

# How many ledger rows one poll will return. A burst larger than this is delivered
# across successive polls rather than in one unbounded read - an observer must never
# be able to pull the whole ledger into memory by having been away.
MAX_EVENTS_PER_POLL = 200


class Cursor(NamedTuple):
    """Where an observer has read up to. Opaque by intent: callers hold a position,
    not a connection, so the transport underneath can change without touching them."""
    events: int      # ledger rows already seen
    tick: int        # presence revision already seen


def cursor(paths) -> Cursor:
    """A cursor at 'now'. An observer starting here sees only what happens next."""
    snap = presence.read(paths) or {}
    return Cursor(events=event_log.count(paths), tick=int(snap.get("tick", 0)))


def poll(paths, since: Cursor) -> tuple[Cursor, dict]:
    """What has happened since `since`. Returns the new cursor and the changes.

    A quiet channel returns empty changes - re-reporting an unchanged world on every
    poll would make this a busy-loop rather than an announcement.
    """
    if not isinstance(since, Cursor):
        since = Cursor(*since)

    total = event_log.count(paths)
    events: list[dict] = []
    seen = since.events
    if total < seen:
        # The ledger SHRANK, so it is not the one this cursor was counting: a wiped
        # state root, a fresh engagement, a rotated log. Without this the observer
        # holds a position beyond the end forever, `total > seen` is never true
        # again, and it goes permanently and silently blind.
        #
        # Resynchronise from the beginning rather than guessing which rows are new.
        # Re-delivering a few is harmless; missing everything is not.
        seen = 0
    if total > seen:
        events = event_log.read(
            paths, limit=min(total - seen, MAX_EVENTS_PER_POLL), offset=seen)
    since = Cursor(events=seen, tick=since.tick)

    snap = presence.read(paths) or {}
    tick = int(snap.get("tick", 0))
    changed_presence = snap if tick != since.tick else None

    now = Cursor(events=since.events + len(events), tick=tick)
    return now, {"events": events, "presence": changed_presence}
