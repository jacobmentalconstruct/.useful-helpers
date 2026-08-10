# 0022 — T4's Gate Reopened: The Windows Path Cannot Execute

- **Date:** 2026-08-09
- **Reopens:** T4 — Cancellation and Progress (parked 2026-08-08, journal 0013)
- **Status:** in progress

---

## 1. Justification, stated before work begins

Required by `TRANCHE_PROTOCOL.md` §5.2. The justification is **correctness of the
verification machinery**, not polish.

```python
gates/t04_cancellation.py:138
    leftover = subprocess.run(["pgrep", "-f", "t04slowprobe/cli.py"], ...)
```

`pgrep` does not exist on Windows. The call is unguarded, so it raises
`FileNotFoundError` — the gate **errors** rather than failing, which aborts the
entire Windows CI job. Nothing after `t04` is verified on the only host that runs
this suite with zero skips.

**This is not a hypothetical.** The workflow triggers `on: push: branches: [main]`,
the operator has pushed, and the run is executing against this defect now.

The sharp part: the assertion is *"cancelling reaps the child, leaving no orphan"*,
and **"Windows process-group kill unverified — `taskkill /F /T` untested"** has been
carried as a High-priority backlog item since T4 closed. The one check Windows most
needed to run is the one that cannot run there.

Reading the run before fixing this would only confirm the crash and leave the
question open a fifth tranche.

## 2. Scope

`gates/t04_cancellation.py` only. No product code. No other gate.

**Not** a skip. A `SKIPPED` would be honest and would leave the backlog item
permanently unprovable on the one platform where it matters.

---

## 3. The fix

Two defects, not one. The obvious fix — branch on `os.name` and shell out to a
Windows process lister — repairs the first and leaves the second.

**Defect 1: the command is POSIX-only.**

**Defect 2: the check matched on *command line text*.** `pgrep -f` searches command
lines. Windows has no equivalent that is both present and stable: `tasklist` filters
on image name, not command line; `wmic` is deprecated and removed from current
Windows images; the PowerShell CIM equivalent is a third syntax to maintain. Porting
the *matching strategy* would mean maintaining three implementations of one question.

So the question changed instead. Rather than *"is any process whose command line
mentions the fixture still running"*, the gate now asks *"is **this specific process**
still alive"* — the fixture records its own PID, and liveness is checked directly.

That is more precise on both platforms (no command-line substring collisions) and
reduces the platform-specific surface to one small function.

**Liveness, per platform:**

- POSIX — `os.kill(pid, 0)`.
- Windows — `tasklist /FI "PID eq <pid>" /FO CSV /NH`, the idiom already used by
  `tools/dev_server_manager/cli.py:89`. Reused rather than reinvented.

**`os.kill(pid, 0)` is deliberately not used on Windows.** CPython's `os.kill` on
Windows calls `TerminateProcess` for any signal other than `CTRL_C_EVENT` and
`CTRL_BREAK_EVENT` — including `0`. The POSIX idiom for *"does this process exist"*
would **kill the process it was asked about**, and the check would then pass by
having caused the condition it tests for. A false green that manufactures its own
evidence.

**Where the PID file goes.** The fixture writes beside itself, in
`tools/t04slowprobe/`, resolved from `__file__`. Not into the state root: the gate
sets `SUITE_PROJECT_ROOT` and `SUITE_STATE_ROOT` to the *same* temporary directory,
so a fixture writing to the state root would be writing to the bound target — and
the precept guard would correctly flag an Observe tool mutating the target. The
sidecar's own `tools/` directory is its own home.

---

## 4. Result

```
fresh clone, zero env vars, Linux:
  ruff check .          ->  All checks passed
  python gates/run.py   ->  t00 t01 t02 t03 t04 t05  SUITE: PASS
                            133 assertions, + 2 declared PARTIAL
  t04 orphan check      ->  PASS, via PID liveness rather than pgrep
```

**Windows remains unverified until the run reports.** That is the point of the fix,
and it is not a claim this entry may make on the runner's behalf.

---

## 5. Standing note

This is the sixth time a check has been found to prove less than its name claimed —
and the second in two days where the defect was *the platform the check could not
run on*, rather than the logic it contained.

`t04` reported `PASS` for a full tranche while being incapable of executing on the
platform its own backlog item named. A gate that cannot run is not a failing gate;
it is an absent one, and absence is invisible in a column of green.

The lesson generalises: **a check's coverage is part of its claim.** `gates/run.py`
now prints declared `[PARTIAL]` coverage for exactly this reason, and platform
reach belongs in the same category as sentinel-set completeness.

---

## 6. Re-park

T4 returns to **parked** with its gate unchanged in intent and repaired in reach.
The backlog item *"Windows process-group kill unverified"* stays open — the fix makes
it **answerable**, and only the CI run can answer it.
