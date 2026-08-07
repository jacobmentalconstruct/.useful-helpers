# 0009 — T2 Closed: Ledger and Presence

- **Date:** 2026-08-06
- **Tranche:** T2 — Ledger and Presence
- **Status:** **PARKED. Three gates green from a fresh clone.**

---

## 1. Result

```
fresh clone -> 85 tests in 16.3s -> OK (skipped=9)
fresh clone -> t00 PASS · t01 PASS · t02 PASS
                             64 assertions, 0 fail, 0 skip
sidecar self-audit on new code: dead_code 0 · domain_boundary 0 · blocking_call 0
```

---

## 2. Outcome

The seam contract exists in code: **two channels, one seam.**

**The ledger** — durable, append-only, and now *readable*. `record()` was its
entire surface, which made it a write-only audit trail: nothing could show an
operator what an agent had done, or an agent what an operator had done. The shared
record existed but was unreadable by the parties it was for. Added `read()` with
bounded pagination and `count()`.

**Attribution** — `client` and `kind` columns, threaded from every entrance:
`cli`, `agent` (MCP), `gui`. Recorded, never used to grant privilege — a GUI click
and an agent call take the same path and meet the same ceiling. The point is that
each party can see what the other did, not that either is trusted more.

**Confirmation as a first-class event.** `record_decision()` captures a human
granting or refusing authority — the moment authority is actually exercised.
Previously a boolean buried inside a tool call, leaving no trace. Verified:
*"write_file, granted=False, operator declined 400-file rewrite"* is now a
permanent row.

**Presence** — `src/core/presence.py`. State, not events: one overwritten snapshot
with a monotonic tick, a closed field vocabulary, atomic writes, cleared at the
composition root on startup. An agent asking what the operator is looking at gets
an answer rather than replaying four hundred selection events to reconstruct one.

---

## 3. The Two Risks, Spent Rather Than Scheduled

Both were raised as risks *at declaration* and encoded as gate assertions before
implementation. Neither became a defect.

**The migration trap.** `CREATE TABLE IF NOT EXISTS` does nothing against an
existing database, so new code would have written into a schema lacking the
column — no error, just a silently missing attribution. And `_state/` is
gitignored, so every machine carries a different history. `migrate()` is additive
and idempotent; the gate builds a genuine pre-T2 database, migrates it twice, and
asserts the shape is identical both times.

Pre-existing rows read `unknown` rather than a guessed caller. Attributing an old
call to a client that was never recorded would be a fabricated audit trail — the
one thing an audit trail may not contain.

**The accumulation trap.** Presence could easily have grown a recent-selections
list or a focus history, becoming a second ledger with none of the ledger's
guarantees. The gate runs twelve updates and asserts the footprint does not grow,
rather than merely asserting presence exists. Unknown keys are dropped rather than
stored, because an open dict is how a snapshot quietly becomes a log.

**Recorded as method:** a hazard identified before work starts is not a defect to
schedule. Encoding it as an assertion is what stops it becoming one.

---

## 4. Tidiness Pass

**`command_profile` now detects lint.** It previously reported `smoke`, `unittest`,
`run_bat` and `setup_env` while `ruff.toml` sat at the root — so `project_run`
could not reach linting either, and the only path to it was a test that skips
silently when the linter is absent. Now detected from `ruff.toml`, `.ruff.toml`,
`setup.cfg`, `.flake8` or a `[tool.ruff]` block. Verified: five commands, lint
among them.

This is corollary 2 of the lint capability gap, closed at a fraction of the cost of
the tool itself. **Linting is now reachable through the seam.** The dedicated tool
remains recorded and high-priority; what it would add is structured findings,
Observe authority, scope derived from the manifest, and honest `UNAVAILABLE`.

Also re-verified: the vend still self-hosts at 276 → 276, E11 still holds, and the
sidecar's own analysers report nothing on the new code.

---

## 5. Deliberately Not Done

**No transport.** Presence is readable by any process through the state root, but
nothing subscribes. Polling versus socket versus tail is T3's question, and
splitting presence from the ledger has already made it easier — presence needs no
durable storage at all.

**No UI.** The backend is testable headlessly first, per the charter.

---

## 6. Park Point

**T2 is closed.** The ledger is readable and attributed, confirmation is a
first-class event, presence answers what is true now without growing, and the two
channels stay separate.

**Next.** T3 — Live Channel. **E6a and E6b**, the piece of the operator's vision
that had nothing under it. It now has a foundation.

**Carried:** Windows zero-skip run; the `lint` tool; `VERSION` not moving with
tool changes; `test_d1_p1` slow until the parts bin goes.
