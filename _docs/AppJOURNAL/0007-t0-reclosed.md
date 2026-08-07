# 0007 — T0 Re-Closed

- **Date:** 2026-08-06
- **Tranche:** T0 — Foundation and Reset (reopened in 0006, now closed)
- **Status:** **PARKED. Verified from a clean clone with no setup step.**

---

## 1. Stop Condition, Met

> A clone made fresh from the repository, with no setup commands run, passes
> `smoke_test.py` and `gates/run.py`.

```
fresh clone -> 85 tests in 16.5s -> OK (skipped=9)
fresh clone -> t00_foundation    -> 24 PASS, 0 FAIL, 0 SKIP
```

The nine skips are environmental — `ollama` and `ruff` are absent from the
sandbox. Windows remains the authority for a zero-skip run; it reported 85 pass,
0 skip, earlier today.

---

## 2. What Was Repaired

**The derived registry.** `registry.ensure_manifest()` generates
`config/registry.json` when absent — idempotent, a no-op once present — called
from the composition root so every entrance works out of the box, and from the
test fixture, which runs in-process and never reaches `src/app.py`.

The registry **stays untracked**. It is genuinely derived, and committing a build
artifact would reintroduce the drift that untracking removed. The fix is to
generate it, not to ship it.

**The gate was polluting the repository it gates.** The unlink preflight writes a
probe file into the repository root and deletes it. On a filesystem that denies
unlink — precisely the condition it exists to detect — the delete fails and the
file lingers. One was swept into a commit by `git add -A`.

A check must not change the thing it measures. Probe names are now ignored and the
stray file is untracked.

---

## 3. The Method Change That Found Both

Neither defect was findable in the trees being tested.

`config/registry.json` existed in every working tree that had ever generated one,
including the operator's, so the suite passed everywhere it was run. **Untracking
a file does not delete it.** And the probe file could only linger on a filesystem
that denies unlink, which is the one the repository lived on.

What changed: `/tmp` in the sandbox is native storage with normal delete semantics
and 3.9 GB free, and GitHub is reachable. Cloning there produces a genuinely fresh
tree that runs the full suite in ~16 seconds.

**Recorded as method: a suite run against the tree that developed it is a weaker
check than the same suite run against a fresh clone.** The first cannot see a
missing build step. The second cannot miss one. Every future tranche should verify
from a clone, not from the working tree.

---

## 4. Changed Files

| File | Change |
| --- | --- |
| `src/core/registry.py` | `ensure_manifest()` — generate the derived registry when absent |
| `src/app.py` | call it at the composition root |
| `tests/test_smoke.py` | call it in the fixture; in-process tests bypass `app.py` |
| `gates/t00_foundation.py` | assert on-demand generation is wired |
| `.gitignore` | gate probe names; untrack the stray probe |

---

## 5. Park Point

**T0 is closed.** The claim it was originally closed on — a blank, default,
cleanly installable baseline — is now true and demonstrated from a clean checkout
rather than asserted from a developed one.

**Next.** T1 — One Ship Manifest, declared in 0005. Its gate is written and
failing at the first assertion, which is the intended pre-implementation state.
Nothing of T1 has begun.
