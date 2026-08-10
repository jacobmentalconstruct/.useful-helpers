# 0014 — The Discovery Pass, Adopted And Immediately Useful

- **Date:** 2026-08-09
- **Tranche:** none — protocol change plus the repair it produced
- **Status:** **Closed.** Five gates green, 87 assertions, 85 tests OK, ruff clean,
  from a fresh clone **with no environment variables set at all**.

---

## 1. Why

The operator asked how a full test would be initiated that reveals what the builder
*is not looking for*.

It cannot be a gate. Every assertion in a gate encodes what its author already
suspected, which is why the attribution check missed `playbook.py`: it scanned where
the problem was expected to be. A gate is a hypothesis test, and it can only fail in
the ways its author imagined.

Four defects this project has already found had the same shape — a memoised
migration that outlived its file, a presence clear that ran per process, a process
group that gained reach and lost cascade, and a gate that inherited the blind spot
of the bug it was written to catch. Each was correct in isolation. Each was caught,
when it was caught, by **measuring rather than asserting**.

---

## 2. Protocol Change

`.bcc/TRANCHE_PROTOCOL.md` gains:

- **§3.2 rule 9** — a passing gate closes loop step 8 (`re-verify`). It does not
  close step 6 (`verify and review critically`).
- **§3.4 The Discovery Pass** — six techniques whose common property is that *none
  of them encode the builder's expectations*: run the harness; differential;
  perturbation; mutation; census; cross-environment.
- **§5 parking** — the discovery pass must have been run and its findings recorded,
  *including a finding of nothing*.

---

## 3. The Instrument Was Already Here

`_harness/` was written for exactly this and had been ignored for the whole of
T0–T4. It scores against the charter rather than the implementation, takes sha256
manifests before and after — catching *any* trace rather than a predicted one —
runs **every** mounted tool with default arguments, and carries **planted
false-positive bait**.

From a fresh clone:

```
PRECEPT      PASS  (install=0 runtime=0)
FRONT DOOR   PASS  domain=python-app expected=python-app correct=True mounted=24
TOOL HEALTH  12/12 ok
TRUTHFULNESS false_positives=0  (naive 1, policy prevented 1)  missed=0
CLEANLINESS  PASS  (0 lineage hits)
ENFORCEMENT  PASS  (seam rejected a target-writing Observe tool; write detected)
SEAM         seam_complete=True  ok=15 blocked=0 failed=0
```

The truthfulness line is the one worth keeping: a tool **would** have produced a
false positive under naive arguments, and the policy layer prevented it. No
correctness assertion reaches that, because a tool that lies returns successfully.

---

## 4. What The First Discovery Pass Found

**The suite fails three tests in its default configuration, and has for some time.**

```
fresh clone, no env vars   ->  FAILED (failures=3)
  test_target_is_never_modified   target overlaps the toolkit source tree
  test_sidecar_conditions         target overlaps the toolkit source tree
  test_seam_universal_apply       r.output.get("dry_run") is None
```

**Mechanism.** `setUpClass` redirects `tempfile` into the sidecar's own home. That
is right for ordinary scratch — the sidecar writing only inside itself is the
precept. But `sidecar_install` refuses a target that overlaps its own source tree,
also rightly: vending a copy of yourself into yourself is nonsense.

Two correct decisions. Composed, they make every install test's target illegal.

**Provenance.** The redirect used to read `home.parent`, correct while the sidecar
was nested one level down. The collapse to root made that wrong, so it was moved
inside `home` — and that move broke the install tests. **This is the fifth time a
fix has had a partner effect in a different file.**

**Why nobody saw it.** Every path used to verify this project sets `SUITE_TEST_TMP`
to somewhere outside the tree: the operator's command, my own sandbox runs (set for
speed on the mount), and *both CI jobs*. The variable that makes the suite fast is
the variable that hides the defect, so the configuration that actually ships was the
one configuration never tested.

That is worse than the bug. Three tranches were parked on the strength of "85 tests
OK", and that number was produced under a setting no user has.

---

## 5. Repair

**`tests/test_smoke.py`** — new `_foreign_target()` returns a directory genuinely
outside the toolkit tree, registered for cleanup. Both halves of the redirect have
to be undone for the call: the stashed pre-redirect `mkdtemp` still consults
`tempfile.tempdir`, which is also patched, so restoring one and not the other lands
straight back inside the tree. Four call sites moved onto it.

**`.github/workflows/verify.yml`** — the Windows *Suite* step no longer sets
`SUITE_TEST_TMP`. CI is on local disk and has no speed excuse, so **CI runs the
shipping default**. The variable stays available for network and FUSE checkouts.
This is the durable part: the fix above repairs the defect, but removing the setting
is what stops the verification path from concealing the next one.

**`gates/t02_ledger_presence.py`** — dead stub removed. §6c was a half-written
duplicate of the attribution check left behind when it moved to §4b; it re-imported
`re` and re-bound `unattributed` after the real check had already run. Harmless, and
exactly the residue this project exists to prevent.

---

## 6. Result

```
fresh clone, NO environment variables:
  ruff check .                 ->  All checks passed
  python -m unittest           ->  Ran 85 tests, OK (skipped=8)
  python gates/run.py          ->  t00 t01 t02 t03 t04 PASS, 87 assertions
  _harness run + seam          ->  6/6 sections PASS, seam_complete=True
```

---

## 7. Standing Note

**A green gate means the assertions passed. It does not mean the code is correct.**

The corollary earned here: **a green suite means the assertions passed *in the
configuration you ran them in*.** Record the configuration, and prefer the default.

---

## 8. Next

**T5a — One Surface: Observe and Select.** Declaration to follow, gate first.

**Carried:** `lint` tool (unscheduled by choice); `VERSION` not moving with tool
changes; `test_d1_p1` slow until the parts bin goes; CI **still unverified until its
first run** — and that run now matters more, because it is the only path that
exercises the default configuration on Windows; Windows confirmation for
process-group kill; scoreboard evidence pass, with **E8** to be re-derived.
