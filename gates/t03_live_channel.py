"""
FILE:       gates/t03_live_channel.py
ROLE:       Gate for T3 - Live Channel.
DOMAIN:     factory
DOES:       Asserts a client learns that the other party acted, without being told
            to look, in-process and out-of-process, without the observer being able
            to harm the seam.
NOTES:      Written during tranche declaration, BEFORE implementation, per
            .bcc/TRANCHE_PROTOCOL.md sec 3.2 rule 1.

            Scope is E6a ALONE. E6b was met by T2 - presence already answers "what
            is true now" and survives a CLI call. Claiming both would have credited
            this tranche with work already done.

            Rule 8: the cross-process assertions drive a REAL entrance
            (`python -m src.app cli tool-call`) rather than calling functions, because
            T2's presence bug lived in the wiring and passed every unit-level check.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

OUTCOME = "a change announces itself: each party sees the other act"


def _load(root: Path, dotted: str):
    sys.path.insert(0, str(root))
    try:
        return __import__(dotted, fromlist=["_"])
    except Exception:
        return None
    finally:
        if str(root) in sys.path:
            sys.path.remove(str(root))


def _paths(root: Path):
    sys.path.insert(0, str(root))
    try:
        from src.core.config import resolve_paths
        return resolve_paths(root)
    except Exception:
        return None
    finally:
        if str(root) in sys.path:
            sys.path.remove(str(root))


def check(r, root: Path) -> None:
    watch = _load(root, "src.core.watch")
    r.check("a watch surface exists", watch is not None,
            "expected src/core/watch.py - the channel by which a change announces itself")
    if watch is None:
        return
    for fn in ("cursor", "poll"):
        r.check(f"watch exposes {fn}()", hasattr(watch, fn))
    if not (hasattr(watch, "cursor") and hasattr(watch, "poll")):
        return

    if not r.filesystem_permits_unlink(root):
        r.skip("a change announces itself",
               "this filesystem denies unlink, so the ephemeral stores cannot be "
               "exercised or cleaned up here")
        return

    state = Path(tempfile.mkdtemp(prefix="t03-state-"))
    target = Path(tempfile.mkdtemp(prefix="t03-target-"))
    env = {**os.environ,
           "SUITE_STATE_ROOT": str(state),
           "SUITE_PROJECT_ROOT": str(target)}
    prev = {k: os.environ.get(k) for k in ("SUITE_STATE_ROOT", "SUITE_PROJECT_ROOT")}
    os.environ.update({"SUITE_STATE_ROOT": str(state), "SUITE_PROJECT_ROOT": str(target)})
    try:
        paths = _paths(root)
        if paths is None:
            r.check("the channel is exercisable", False, "could not resolve paths")
            return
        presence = _load(root, "src.core.presence")
        event_log = _load(root, "src.core.event_log")

        # --- 1. an OUT-OF-PROCESS action is observed --------------------------
        # Rule 8: a real entrance, not a function call. This is the assertion that
        # would have caught T2's presence bug, which passed every unit-level check.
        before = watch.cursor(paths)
        subprocess.run(
            [sys.executable, "-m", "src.app", "cli", "tool-call",
             "--tool", "ping", "--args-json", "{}"],
            cwd=root, capture_output=True, text=True, timeout=180, env=env,
        )
        after, changes = watch.poll(paths, before)
        events = changes.get("events") or []
        r.check("an out-of-process action is observed without being told to look",
                any(e.get("tool_id") == "ping" for e in events),
                f"observer saw {len(events)} events after a real CLI invocation")
        r.check("the cursor advances past what was seen",
                after != before, f"{before} -> {after}")

        # --- 2. polling again yields nothing new ------------------------------
        # A channel that re-reports the same change every poll is a busy-loop, not
        # an announcement.
        _, quiet = watch.poll(paths, after)
        r.check("a quiet channel reports nothing",
                not (quiet.get("events") or []) and not quiet.get("presence"),
                f"re-polling an unchanged channel returned: {quiet}")

        # --- 3. an IN-PROCESS presence change is observed ---------------------
        c0 = watch.cursor(paths)
        presence.update(paths, browse_selection="operator/looking/here.py")
        _, seen = watch.poll(paths, c0)
        snap = seen.get("presence") or {}
        r.check("a presence change is observed",
                snap.get("browse_selection") == "operator/looking/here.py",
                f"observer saw presence: {snap}")

        # --- 4. an observer cannot harm the seam ------------------------------
        # A dead or dropped observer is the normal case - a GUI closes, an agent
        # exits. It must be a non-event for everyone else.
        stale = watch.cursor(paths)
        for _ in range(5):
            event_log.record(paths, tool_id="ping", authority="Observe", category="x",
                             args={}, ok=True, exit_code=0, error=None,
                             duration_ms=1, client="test")
        del stale                      # the observer simply goes away
        ok_after = event_log.count(paths) >= 5
        r.check("a dropped observer does not block or corrupt the seam", ok_after,
                "the ledger must be unaffected by anyone having stopped watching")

        # --- 5. presence loss does not damage the ledger ----------------------
        # The two channels have different durability guarantees on purpose. Losing
        # the ephemeral one must not touch the durable one.
        n_before = event_log.count(paths)
        presence.clear(paths)
        r.check("presence loss leaves the ledger intact",
                event_log.count(paths) == n_before and watch.cursor(paths) is not None,
                "the ephemeral channel must not be able to damage the durable one")

        # --- 6. observation is READ-ONLY on the target ------------------------
        sig_before = sorted(p.name for p in target.rglob("*"))
        c = watch.cursor(paths)
        watch.poll(paths, c)
        watch.poll(paths, watch.cursor(paths))
        r.check("observing writes nothing into the target",
                sorted(p.name for p in target.rglob("*")) == sig_before,
                "watching is an Observe activity; it must leave the target untouched")

        # --- 7. the interval is measured, not asserted ------------------------
        t0 = time.perf_counter()
        for _ in range(50):
            watch.poll(paths, watch.cursor(paths))
        per = (time.perf_counter() - t0) * 1000 / 50
        r.check("a poll cycle is cheap enough to be frequent", per < 25.0,
                f"{per:.2f} ms per poll - measured, not guessed; the interval is "
                "chosen from this rather than from intuition")
    finally:
        for k, v in prev.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
