# 0013 — T4 Closed: Cancellation and Progress

- **Date:** 2026-08-08
- **Tranche:** T4 — Cancellation and Progress
- **Status:** **PARKED. Five gates green, 86 assertions, from a fresh clone.**

---

## 1. Result

```
fresh clone -> 85 tests in 16.7s -> OK (skipped=8)
fresh clone -> t00 · t01 · t02 · t03 · t04 -> PASS, 86 assertions, 0 fail, 0 skip
ruff check .                     -> All checks passed
cancel from another thread       -> ok=False, error='cancelled', exit=-2
```

---

## 2. Outcome

`subprocess.run` gave back no handle, so nothing could stop a running tool and the
only exit was to wait out a module-level 120 s constant. Now:

**Cancellable dispatch.** `Popen` plus a supervised wait. `running()` reports what
is in flight; `cancel(op_id)` stops it. Verified from a different thread — the
calling thread is blocked in `communicate()`, so cancellation from anywhere else is
the only shape that is actually useful.

**Cancellation is its own outcome**, `exit_code = -2`, not a generic failure. A
deliberate stop and a crash must never be indistinguishable in the ledger.

**Per-call timeout**, overriding the constant. A snapshot compile over a large tree
needs longer; a health probe should not wait two minutes.

**Diagnostics scrubbed on the return path.** `event_log` scrubbed before *storing*,
so the audit trail was clean while the value handed to a GUI or an agent still
carried absolute build-machine paths. The machinery existed; it was simply not on
that path.

**Coarse lifecycle progress** onto the live channel — `started` / `finished` /
`cancelled` / `timeout` via presence. Deliberately coarse: tools emit one JSON
envelope at completion, so per-tool progress would need all 95 changed and would
break the stdout contract the envelope depends on. Started/finished answers the
real question — *is it stuck, and can I stop it*.

---

## 3. The Defect The Gate Caught

Cancellation needs to reach **grandchildren**: killing the direct child leaves
anything it spawned running. So children are started in their own process group.

That fixed cancellation and broke something else. **Detaching to gain reach costs
the automatic cascade** — a child in its own group no longer dies with its parent.
The gate killed the seam process and found the tool still running afterwards.

In use that is a worker holding a file lock, or a server holding a port, long after
the thing that started it is gone.

`reap_all()` puts the cascade back deliberately, wired to `atexit` and to
SIGTERM/SIGINT from the composition root. `atexit` alone was not enough: the default
disposition for SIGTERM ends a process *without* running exit handlers, which is
exactly the case that orphaned the tool.

**This is the third time a fix has broken something at the seam it was welded to** —
the memoised migration that outlived its file, the presence clear that ran per
process, and now a process group that gained reach and lost cascade. Each was
correct in isolation. The pattern is that lifecycle changes have a partner effect,
and the partner is never in the same function.

---

## 4. A Fixture Bug Worth Recording

The gate first failed "observable while running" because the fixture tool was named
`_t04_slow_probe`. **`registry.discover()` skips `_`-prefixed directories** — that is
how `tools/_template` stays unregistered — so the fixture was never registered, and
the dispatch returned "unknown tool" instantly.

Which looks *exactly* like "the operation already finished". A test fixture that
fails to exist produces the same signal as the behaviour under test succeeding
quickly. Worth remembering when a timing assertion fails: check the thing is
running at all before adjusting the timing.

---

## 5. Park Point

**T4 is closed.** Long work is observable while it runs, can be stopped from
outside the calling thread, leaves no orphan, honours a per-call timeout, and
returns diagnostics with no host paths in them.

**Scoreboard unchanged at five of twelve** — T4 serves E3 and E7 rather than
completing a condition of its own. That is honest: not every tranche moves the
scoreboard, and pretending otherwise is how a plan starts flattering itself.

**Next.** T5a — One Surface: Observe and Select. The first tranche that builds UI,
and the first where the operator sees any of this.

**Carried:** `lint` tool (unscheduled by choice); `VERSION` not moving with tool
changes; `test_d1_p1` slow until the parts bin goes; CI workflow **unverified until
its first run**; Windows confirmation for process-group kill, which the sandbox
cannot exercise.
