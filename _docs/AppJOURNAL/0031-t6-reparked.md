# 0031 — T6 Re-Parked: The Updater Repair

- **Date:** 2026-08-14
- **Tranche:** T6 — Instance Identity and the Installation Core
- **Status:** **PARKED.** Reopened in 0028; both defects discharged.
- **Reopen history:** 0026 (awaiting approval) → 0027 (parked, prematurely) → 0028
  (reopened) → **0031 (parked)**. None of those entries is amended. The reopen record
  is the useful part.

---

## 1. Red before green, both defects

The two assertions were written first and **run against the unrepaired installer**.
All 24 pre-existing assertions passed; all three new ones failed.

```text
[FAIL] update over a broken manifest fails loudly
[FAIL] a failed update preserves durable memory
[FAIL] a failed update leaves the instance no less recoverable
VERDICT: FAILED
```

After the repair, 27/27 PASS. Protocol §5.1a is satisfied by observation, not by
argument: a check for an absent condition that has never been seen to fail is not
evidence, and these were seen to fail.

**A note on where they were run.** The development mount denies `unlink`, and
`gates/t06` skips its entire install half on such a filesystem — honestly, with a
stated reason, but it means every previous "t06 PASS" recorded in this sandbox
exercised only the eight static assertions. The red and green runs above were both
performed on a real-disk copy, where nothing skips. **Windows CI remains the
authority.**

---

## 2. Defect 1 — the repair

`_read_identity()` caught `Exception` and returned `None`; `create(identity=None)` then
minted a fresh UUID.

It no longer catches. `install()` catches at the decision point and **refuses**:

```python
try:
    carried_identity = _read_identity(dest)
except Exception as e:
    return {"ok": False, "status": "identity-broken", ...}
```

The error names the situation and the only safe alternative — reinstall, *"accepting
that it is a NEW instance and durable records keyed to the old identity will not be
associated with it."* Absent is still not malformed: no manifest returns `None` and the
caller decides.

---

## 3. Defect 2 — build beside, then swap

The old shape moved `_state` to a **system temp directory**, deleted the instance root,
copied, moved `_state` back — and cleaned that temp directory in a `finally` clause
that could not distinguish *cleanup after success* from *this is the last copy*. Any
failure inside the copy destroyed the instance and its durable memory together.

The repair is a change of order, not a rescue path:

```text
copytree(payload -> staging)        fail -> dest untouched
copy _state into staging            fail -> dest untouched   (COPIED, never moved out)
write identity into staging         fail -> dest untouched
move dest -> backup; staging -> dest    the only irreversible moment: two renames
rmtree(backup)                      only after the swap succeeds
```

**Nothing is destroyed until the replacement is complete.** Durable memory never leaves
the tree that owns it. If the swap itself fails, the error names the exact path where
the previous instance is intact rather than cleaning it away.

`memory_preserved` is now `(dest / _STATE).is_dir()` — an **observation**. It read
`mode == "update"`, which restates the request: it reported `true` when there was no
state to keep, and would have reported `true` on the run that lost it.

### Why the standard was the stronger one

The operator's wording did the work:

> **A failed update must not leave the installed instance less recoverable than it was
> before the update began.**

*"Do not lose `_state`"* is weaker and would have accepted a wrong fix. The first repair
considered here cleared the instance root while keeping `_state` in place — that
preserves the journal perfectly and leaves the instance **unstartable**, because `src/`
is gone. It passes the weak claim and fails the real one. The gate asserts both halves
separately for exactly that reason.

**One consequence recorded, not claimed as a fix:** identity is now written into the
staged tree, so `_instance_module()` is called on the new payload rather than the old
one. That happens to be what its docstring always said it did. The backlog item about
that docstring disagreeing with the `_read_identity` call order (0028 §4) **stands** —
it concerns a different call site and is still unexamined.

---

## 4. Certification after the repair

Not just the two new tests. The point was to show the repair did not break the
established product path.

| | Result |
| --- | --- |
| `ruff check .` | clean |
| `gates/t06` | **27/27 PASS** on real disk (install half exercised, nothing skipped) |
| `gates/t00`–`t05` cumulative | PASS |
| `smoke_test.py` | 84 tests; failures only from environment constraints, named below |
| real installer path | exercised by the gate — fresh install, rename, move, update, corrupt-manifest update, failed update |
| documented launcher | the gate parses the command the installer prints and **executes it** |
| containment / discovery | unchanged by this repair; `SUITE_DISABLE_CONTAINMENT` mutation is a Windows-only signal |

**Environment failures, named rather than folded away.** On the development mount,
`test_c1_hands` and `test_c4_data` fail with `PermissionError` on `Path.unlink()` —
the delete-denial recorded in Charter §7.5. On a real-disk copy those pass and
`test_git_inspect` fails instead, because a `tar`-copied tree has no `.git`. Neither is
a product defect, and neither reproduces on Windows CI, which has both capabilities.
That is why Windows is the authority for a zero-skip run.

---

## 5. Parked evidence

T6's outcome claim is now true as written:

> One installed instance is structurally bound to one target, knows its identity, root
> and state, **survives relocation and update**, and supplies canonical context to the
> human, agent and tool runtime.

Two regression assertions are part of the parked evidence and must stay green:

1. `update over a broken manifest fails loudly`
2. `a failed update preserves durable memory` + `a failed update leaves the instance no
   less recoverable`

**Carried, unchanged:** E8 and E11 remain **NOT MET** — T6 closed the install row of
E8's phase matrix and now the update row's failure-safety, not uninstall, startup or
self-maintenance. The **canonical payload assembler** remains deferred to
`P-install-packaging` and was not carried into this repair. The `_instance_module`
docstring finding remains in the backlog.

---

## 6. Next

**C1b — the Application Absorption Audit.** Diagnostic only: inspect, classify, identify
duplication, determine what T7 actually touches, **implement nothing.** Its deliverable
answers one question — *how small can T7 actually be?* — and T7 is declared from that
evidence.
