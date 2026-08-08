# 0010 — T2 Review: Two Bugs Found After Parking

- **Date:** 2026-08-06
- **Tranche:** T2 (reviewed after parking; repairs are in scope, not new work)
- **Status:** **Both repaired. Three gates green, 65 assertions, suite green.**

---

## 1. Why This Entry Exists

T2 parked with a green gate. A review pass then found two defects the gate did not
cover. Both were real, one was serious, and neither would have been caught by
anything currently running.

The gate was not wrong about what it asserted. It asserted too little.

---

## 2. Bug 1 — Every CLI Call Wiped Presence · SERIOUS

`presence.clear(paths)` sat at the composition root, so it ran on **every process
start**. For the GUI that is a session. For the CLI, one process is one command.

So every `python -m src.app cli tool-call` destroyed the operator's presence.

An agent working through the CLI — the ordinary case — would wipe the operator's
context on every single call. That is the exact inverse of what E6b exists to
provide: the store built so each party can see the other's context was being
cleared by the other party's routine use.

Verified before and after:

```
before CLI call: operator/was/here.py
after  CLI call: None            -> BUG
after  the fix:  operator/was/here.py
```

**Repair.** Only session-owning entrances clear presence — `ui`, `map`, `install`,
`plan`. `cli` and `mcp` are *clients* of a session, not the start of one.

**Root cause worth naming:** "dropped on restart" was implemented as "dropped on
process start". Those are the same thing for a long-running GUI and completely
different for a per-invocation CLI. The specification was right; the mapping onto
a process model was wrong.

---

## 3. Bug 2 — Migration Ran On Every Event

`record()` called `migrate()` per event: a `PRAGMA table_info` plus two whole-table
`UPDATE` statements, on a **second connection**, on the hot path of every governed
action.

Correct, idempotent, and wasteful. Measured on a 2,000-row ledger:

| | per event |
| --- | --- |
| before | 6.63 ms |
| after | **2.90 ms** |

**Repair.** Memoised per process. A fresh process re-checks, which is the only
moment the shape could have changed underneath it.

---

## 4. The Gate Grew An Assertion

The presence bug existed because nothing asserted the CLI's behaviour — the gate
exercised `presence.clear()` directly and never through an entrance.

It now spawns a real `cli tool-call` and asserts presence survives it. That is the
shape of the fix: **the gate tested the unit and missed the wiring.** A check that
only calls functions directly cannot see how they are composed.

---

## 5. Recorded, Not Fixed

`presence.update()` is read-modify-write. The write itself is atomic — a temp file
plus `os.replace`, so no reader ever sees a half-written snapshot — but two
concurrent writers could interleave and one update could be lost.

Not fixed deliberately: nothing concurrent exists yet. Presence has exactly one
writer today, and the correct remedy depends on T3's transport decision. Fixing it
now would be designing against a mechanism that has not been chosen. **Carried to
T3, where concurrency actually arrives.**

---

## 6. Verification

```
fresh clone -> 85 tests in 16.4s -> OK (skipped=9)
fresh clone -> t00 · t01 · t02 all PASS, 65 assertions, 0 fail, 0 skip
sidecar self-audit: dead_code 0 · domain_boundary 0 · blocking_call 0
```

Complexity hotspots reported by `complexity_score` are pre-existing — `app.py::main`,
`invoke.py::_dispatch`, `cli.py::dispatch` — and none were introduced here.

---

## 7. Note On Method

Both bugs were found by **probing behaviour**, not by reading code: setting
presence, invoking the CLI, reading presence back; and timing `record()` against a
growing ledger. The static analysers reported zero findings on the same code, and
were right to — neither defect is visible in a single file. One is a lifecycle
mismatch across two modules, the other is a cost that only appears under repetition.

Worth carrying: **a green gate means the assertions passed, not that the code is
correct.** The gap between those two is exactly the size of what the gate does not
assert, and reviewing that gap is a different activity from running it.
