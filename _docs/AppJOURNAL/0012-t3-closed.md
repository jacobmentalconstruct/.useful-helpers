# 0012 — T3 Closed: The Live Channel

- **Date:** 2026-08-08
- **Tranche:** T3 — Live Channel
- **Status:** **PARKED. Four gates green, 80 assertions, from a fresh clone.**

---

## 1. Scope Was Narrowed Before Work Started

T3 originally claimed **E6a and E6b**. **E6b was already met** — presence answers
"what is true now", survives a CLI call, and is readable cross-process. It landed
in T2.

Claiming both would have credited this tranche with work already done, and made
the end-state scoreboard read better than the project actually is. Narrowed to E6a
alone, which is one question:

> How does a change announce itself?

---

## 2. The Decision, Made At Declaration

**Polled, single-writer, cursor-based.** Presence has exactly one writer — whoever
owns the session — and readers poll a monotonic tick.

This makes the read-modify-write race carried from T2 **unreachable rather than
handled**: no lock, no daemon, no port, no lifecycle to supervise, and it works
cross-process on any filesystem. The ledger is already append-only with SQLite
managing concurrent appends.

Accepted costs, stated rather than discovered: latency equals the poll interval,
and it does not cross machines. Both are fine for a local sidecar, and the
interface can sit unchanged in front of a socket if one is ever justified —
callers hold a *cursor*, not a connection.

**The interval was measured, not guessed.** A poll cycle is ~0.15–0.25 ms on the
slowest filesystem available here. At 150 ms that is roughly a tenth of one
percent of a core, which is why it can be short enough to feel immediate. The
same lesson as the per-event migration cost: a per-repetition cost is invisible
until measured.

---

## 3. Review Found Two Silent Failures

Both found by probing behaviour, neither visible to any analyser, and **both
silent** — no error, no log line, nothing.

### 3.1 A reset ledger blinded the observer permanently

An observer holds a position. If the ledger shrinks — a wiped state root, a
cleanup tool, a fresh engagement — that position sits beyond the end, `total >
seen` is never true again, and the observer stops seeing anything. Forever.

Now resynchronises from the beginning. Re-delivering a few rows is harmless;
missing everything is not.

### 3.2 The migration memo outlived its file — **self-inflicted**

Worse, and mine. The performance fix in journal 0010 memoised migration to stop it
running per event. But the memo keyed a *path*, and a path can stop existing.

Remove the ledger and `migrate()` returned early against a database that was no
longer there, so the table was never recreated, `record()` INSERTed into nothing,
and the `except Exception: pass` that keeps logging from breaking the seam
swallowed it. **Logging stopped, permanently and silently.**

Measured: 2 rows, remove the file, three more `record()` calls, **0 rows**.

The memo is now discarded when the file it describes is absent.

**Worth stating plainly: a fix for a performance problem introduced a durability
problem.** The optimisation was correct in isolation and wrong in composition —
the same shape as T2's presence bug, where a function that behaved perfectly when
called directly destroyed context through an entrance.

There is also a lesson about `except Exception: pass`. It is right there — logging
must never break the seam — but it converts *"the ledger is broken"* into
*"nothing happened"*, and nothing else was watching. Both bugs were invisible
because the failure mode was silence.

---

## 4. Verification

```
fresh clone -> 85 tests in 16.0s -> OK (skipped=8)
fresh clone -> t00 · t01 · t02 · t03 -> PASS, 80 assertions, 0 fail, 0 skip
ruff check .                     -> All checks passed
sidecar self-audit on src/       -> dead_code 0 · blocking_call 0 · domain_boundary 0
```

Both defects are now gate assertions: recording recovers after the ledger is
removed, and an observer resynchronises rather than going blind.

---

## 5. Park Point

**T3 is closed. E6a holds**: an action by one party is observed by the other,
across processes, through a real entrance, without being told to look — and an
observer can neither block, stall, nor corrupt the seam, nor write into the target.

**Scoreboard: five of twelve end-state conditions met** — E5, E6a, E6b, E8, E11.

**Next.** T4 — Cancellation and Progress. The seam still blocks on
`subprocess.run` with a fixed 120 s timeout and no cancel path; the live channel
now exists to carry progress once there is progress to carry.

**Carried:** `lint` tool (unscheduled by choice); `VERSION` not moving with tool
changes; `test_d1_p1` slow until the parts bin goes; Windows confirmation at close.
