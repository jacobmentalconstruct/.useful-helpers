"""
FILE:       gates/t02_ledger_presence.py
ROLE:       Gate for T2 - Ledger and Presence.
DOMAIN:     factory
DOES:       Asserts the seam contract exists in code: a durable, readable, attributed
            ledger of what happened, and ephemeral constant-size presence of what is
            true now, with confirmation recorded as a first-class event.
NOTES:      Written during tranche declaration, BEFORE implementation, per
            .bcc/TRANCHE_PROTOCOL.md sec 3.2 rule 1.

            Two assertions here exist because they were raised as RISKS at
            declaration rather than discovered later - the migration trap and the
            presence-accumulation trap. Encoding a hazard as an assertion before the
            work starts is what stops it becoming a defect to schedule.
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

OUTCOME = "two channels, one seam: a readable attributed ledger, ephemeral presence"

# The columns the events table must carry after T2.
REQUIRED_COLUMNS = {"event_id", "ts", "tool_id", "authority", "category", "ok",
                    "exit_code", "duration_ms", "args_hash", "arg_keys", "error",
                    "client", "kind"}

# The pre-T2 shape, used to build an old database and prove the migration.
LEGACY_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
  event_id    INTEGER PRIMARY KEY AUTOINCREMENT,
  ts          TEXT NOT NULL,
  tool_id     TEXT NOT NULL,
  authority   TEXT,
  category    TEXT,
  ok          INTEGER,
  exit_code   INTEGER,
  duration_ms INTEGER,
  args_hash   TEXT,
  arg_keys    TEXT,
  error       TEXT
);
"""


def _load(root: Path, dotted: str):
    sys.path.insert(0, str(root))
    try:
        mod = __import__(dotted, fromlist=["_"])
        return mod
    except Exception:
        return None
    finally:
        if str(root) in sys.path:
            sys.path.remove(str(root))


def check(r, root: Path) -> None:
    ev = _load(root, "src.core.event_log")
    pr = _load(root, "src.core.presence")

    # --- 1. the ledger is readable, not write-only -------------------------
    r.check("the ledger has a read API", ev is not None and hasattr(ev, "read"),
            "event_log exposed only record(); a ledger nobody can read is a write-only "
            "audit trail, and E6a cannot be built on it")
    r.check("the ledger reports its size", ev is not None and hasattr(ev, "count"))

    # --- 2. attribution ----------------------------------------------------
    r.check("the schema declares client and kind",
            ev is not None and REQUIRED_COLUMNS <= set(_columns_of(ev)),
            f"missing: {sorted(REQUIRED_COLUMNS - set(_columns_of(ev))) if ev else 'module missing'}")

    # --- 3. THE MIGRATION TRAP (raised as a risk at declaration) -----------
    # CREATE TABLE IF NOT EXISTS silently does nothing against an old database, so
    # new code would write into a schema that lacks the column - no error, just a
    # field that is not there. _state/ is gitignored, so every developer has a
    # different history and both shapes must be tolerated.
    if ev is not None and hasattr(ev, "migrate"):
        tmp = Path(tempfile.mkdtemp(prefix="t02-mig-"))
        db = tmp / "legacy.sqlite3"
        con = sqlite3.connect(db)
        con.executescript(LEGACY_SCHEMA)
        con.execute("INSERT INTO events (ts, tool_id, ok) VALUES ('2026-01-01','ping',1)")
        con.commit()
        con.close()

        ev.migrate(db)
        cols1 = _db_columns(db)
        ev.migrate(db)                      # idempotence
        cols2 = _db_columns(db)

        r.check("an old-shape ledger is migrated, not silently ignored",
                "client" in cols1 and "kind" in cols1,
                f"columns after migrate: {sorted(cols1)}")
        r.check("migration is idempotent", cols1 == cols2,
                "running it twice must change nothing")

        con = sqlite3.connect(db)
        row = con.execute("SELECT client FROM events WHERE tool_id='ping'").fetchone()
        con.close()
        r.check("pre-existing rows read 'unknown', not a guessed attribution",
                row and row[0] == "unknown",
                f"legacy row client={row[0] if row else None!r} - attributing old rows "
                "to a caller that was never recorded would be a fabricated audit trail")
    else:
        r.check("the ledger exposes a migration", False,
                "expected event_log.migrate(db_path)")

    # --- 4. confirmation is a first-class event ----------------------------
    r.check("confirmation is recordable as its own event kind",
            ev is not None and hasattr(ev, "record_decision"),
            "approving or refusing an Apply operation is the moment authority is "
            "actually exercised; today it is a boolean buried in a tool call and "
            "leaves no trace")

    # --- 4b. EVERY caller attributes itself ---------------------------------
    # E5 says a human and an agent are indistinguishable to the seam - true only if
    # both SAY who they are. Seven of eight GUI call sites passed no client, and so
    # did every chain step in playbook.py, so most operator and workflow actions were
    # recorded as "unknown" while the scoreboard claimed E5 outright.
    #
    # Placed HERE, before any filesystem-dependent skip. An earlier revision sat after
    # the presence section's `return` and therefore never ran on a filesystem that
    # denies unlink - a static check silently gated behind an unrelated capability.
    #
    # Matched on the real call shape `invoke(<paths>, ...)` rather than on a module
    # prefix: the first version required `invoke_mod.invoke(` and would have missed
    # playbook.py's bare `invoke(` entirely - the same blind spot as the bug it was
    # written to catch, which is why it now scans all of src/.
    import re as _re
    call_re = _re.compile(r"\binvoke\(\s*(?:self\.)?paths\b(?:[^()]|\([^()]*\))*\)")
    unattributed = []
    for py in sorted((root / "src").rglob("*.py")):
        if py.name == "invoke.py":
            continue                      # the seam defines the parameter
        body = py.read_text(encoding="utf-8", errors="replace")
        for m in call_re.finditer(body):
            if "client=" not in m.group(0):
                unattributed.append(f"{py.parent.name}/{py.name}")
    r.check("every caller attributes itself", not unattributed,
            f"unattributed call sites in: {sorted(set(unattributed))}")

    # --- 5. presence exists, and is STATE not events -----------------------
    r.check("a presence store exists", pr is not None,
            "expected src/core/presence.py")
    if pr is None:
        return
    for fn in ("read", "update", "clear"):
        r.check(f"presence exposes {fn}()", hasattr(pr, fn))

    # --- 6. THE ACCUMULATION TRAP (raised as a risk at declaration) --------
    # It would be easy to let presence grow - a recent-selections list, a history of
    # focus changes. The moment it accumulates it is a second ledger with none of the
    # ledger's guarantees. Assert it does not grow, not merely that it exists.
    if not r.filesystem_permits_unlink(root):
        r.skip("presence does not accumulate",
               "this filesystem denies unlink, so the ephemeral store cannot be "
               "exercised or cleaned up here")
        return

    state = Path(tempfile.mkdtemp(prefix="t02-pres-"))
    env_backup = os.environ.get("SUITE_STATE_ROOT")
    os.environ["SUITE_STATE_ROOT"] = str(state)
    try:
        paths = _paths(root)
        if paths is None:
            r.check("presence is exercisable", False, "could not resolve paths")
            return
        pr.clear(paths)
        sizes = []
        for i in range(12):
            pr.update(paths, browse_selection=f"file_{i}.py", target_root=str(state))
            p = pr.path(paths)
            sizes.append(p.stat().st_size if p.is_file() else 0)
        r.check("presence does not accumulate across updates",
                max(sizes) - min(sizes) < 64 and sizes[-1] <= sizes[0] + 64,
                f"footprint grew {sizes[0]} -> {sizes[-1]} bytes over 12 updates; "
                "presence is STATE, not a second event log")

        snap = pr.read(paths)
        r.check("presence answers what is true NOW",
                isinstance(snap, dict) and snap.get("browse_selection") == "file_11.py",
                f"read back: {snap}")

        # A CLI call is a CLIENT of a session, not a new one. This assertion exists
        # because its absence let a real bug through: clearing presence at the
        # composition root ran on every process start, so every `cli tool-call` wiped
        # the operator's context - an agent working through the CLI destroyed the very
        # state E6b exposes.
        pr.update(paths, browse_selection="operator/was/here.py")
        subprocess.run(
            [sys.executable, "-m", "src.app", "cli", "tool-call", "--tool", "ping",
             "--args-json", "{}"],
            cwd=root, capture_output=True, text=True, timeout=180,
            env={**os.environ, "SUITE_STATE_ROOT": str(state),
                 "SUITE_PROJECT_ROOT": str(state)},
        )
        after = pr.read(paths) or {}
        r.check("a CLI invocation does not wipe presence",
                after.get("browse_selection") == "operator/was/here.py",
                f"presence after a cli tool-call: {after.get('browse_selection')!r} - "
                "only a session-owning entrance may clear it")

        # ephemeral: clear() is what a restart does
        pr.clear(paths)
        r.check("presence is dropped on restart", not pr.read(paths),
               "clear() models a restart; presence must not survive one")
    finally:
        if env_backup is None:
            os.environ.pop("SUITE_STATE_ROOT", None)
        else:
            os.environ["SUITE_STATE_ROOT"] = env_backup

    # --- 6b. structural cost, not timing ------------------------------------
    # migrate() once ran on EVERY event: a PRAGMA plus two whole-table UPDATEs on a
    # second connection, on the hot path of every governed action. A timing assertion
    # would be flaky across machines; the deterministic form of the same defect is
    # structural - one connection per event, not two.
    ev_src = (root / "src" / "core" / "event_log.py").read_text(encoding="utf-8", errors="replace")
    r.check("migration is not re-run on every event",
            "_MIGRATED" in ev_src,
            "record() must not pay for a schema check per event")

    # --- 7. the two channels stay separate ---------------------------------
    src = (root / "src" / "core" / "event_log.py").read_text(encoding="utf-8", errors="replace")
    r.check("no UI-state vocabulary leaked into the ledger",
            not any(w in src for w in ("browse_selection", "operation_inclusion", "focus")),
            "selection and focus belong to presence; ledgering them is the growth "
            "path that made the size question urgent in the first place")


def _columns_of(ev) -> set:
    import re
    schema = getattr(ev, "_SCHEMA", "") or ""
    return set(re.findall(r"^\s{2}(\w+)\s", schema, re.M))


def _db_columns(db: Path) -> set:
    con = sqlite3.connect(db)
    try:
        return {row[1] for row in con.execute("PRAGMA table_info(events)")}
    finally:
        con.close()


def _paths(root: Path):
    """Resolve paths for this gate WITHOUT leaving the variable behind.

    THE LEAK THIS CLOSES. `setdefault` here was never undone, so running this gate
    in-process permanently set SUITE_PROJECT_ROOT to the repo root for the whole
    process - and for every subprocess spawned afterwards. `certify.py` imports
    gates/run.py and runs the gates IN-PROCESS, then spawns the discovery harness. The
    harness drives an instance canonically bound to its own target, T6 refuses the
    conflicting inherited value, and `front_door`, `tool_health` and `enforcement` all
    die at once. Three certifications reported PASS on a discovery pass that never ran.

    The variable is still needed DURING the call: this repository is a source factory
    with no installed instance, so `_resolve_project_root` has no identity to read and
    needs an explicit target. Needing it during the call is not a reason to leave it set
    afterwards.

    `setdefault` is mirrored exactly - if the caller already had a value it is theirs and
    is left alone; only a value this function introduced is removed. Two functions above,
    SUITE_STATE_ROOT was already saved and restored, and `t03` does the same for both
    vars. This one line was the odd one out.
    """
    sys.path.insert(0, str(root))
    had = "SUITE_PROJECT_ROOT" in os.environ
    try:
        from src.core.config import resolve_paths
        os.environ.setdefault("SUITE_PROJECT_ROOT", str(root))
        return resolve_paths(root)
    except Exception:
        return None
    finally:
        if not had:
            os.environ.pop("SUITE_PROJECT_ROOT", None)
        if str(root) in sys.path:
            sys.path.remove(str(root))
