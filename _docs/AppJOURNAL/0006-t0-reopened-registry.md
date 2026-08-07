# 0006 — T0 Reopened: a Clean Clone Cannot Pass Its Own Suite

- **Date:** 2026-08-06
- **Tranche:** T0 — Foundation and Reset (**reopened**)
- **Status:** Justification recorded. Work begins after this entry, per protocol §5.1.

---

## 1. Justification for Reopening

Protocol §5.1: a parked tranche is closed, and reopening requires a correctness,
security, containment, data-loss or maintainability justification **stated before
work begins**.

**The justification is correctness.** T0 was closed on the claim of a blank,
default, *cleanly installable* baseline. That claim is false:

> A fresh clone of this repository cannot pass its own test suite.

`config/registry.json` is absent from a clean checkout, because T0 untracked it as
derived state. Two tests then fail:

- `test_registry_json_matches_discovery` — `FileNotFoundError` reading it
- `test_invoke_operational_audit_pack` — `control_plane.registry` is false

This is not a new feature request. It invalidates a claim T0 itself made, so it
belongs to T0 rather than to T1, and T1's gate should not inherit a red suite.

## 2. Why It Was Missed

The suite passed on the operator's Windows machine because that working tree still
*contained* `registry.json` from before it was ignored. Untracking a file does not
delete it. Every subsequent green run was made against a tree that happened to
carry an artifact a new clone would not have.

**Only a clean clone could expose this**, and until today no clean clone had been
made. The sandbox's mount denies `unlink`, so the suite could not run there; the
Windows tree was never fresh. The gap was environmental, not analytical.

## 3. What Changed to Make It Findable

`/tmp` in the development sandbox is native storage with normal delete semantics
and 3.9 GB free, and GitHub is reachable from it. Cloning the repository there
gives a genuinely fresh tree that runs the suite in ~16 s. That is now the standard
verification loop, with Windows retained as the authority for a final green because
nine tests skip here for want of `ollama` and `ruff`.

This is worth recording as method: **a test suite run against the tree that
developed it is a weaker check than the same suite run against a fresh clone.**
The first cannot see missing build steps. The second cannot miss them.

## 4. Scope of the Reopening

Narrow and explicit.

- Make the derived registry regenerate on demand when absent, so a clean checkout
  works with no manual setup step.
- Add an assertion so the condition cannot regress unnoticed.
- Re-verify from a fresh clone, then re-close.

**Non-goals.** No change to what is tracked — the registry stays untracked; it is
genuinely derived and committing it would reintroduce drift. No T1 work. No
widening into the ship-manifest convergence.

## 5. Stop Condition

A clone made fresh from the repository, with no setup commands run, passes
`smoke_test.py` and `gates/run.py`.
