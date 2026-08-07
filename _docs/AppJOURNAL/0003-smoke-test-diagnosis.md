# 0003 — Smoke Test Diagnosis, and a Correction to 0002

- **Date:** 2026-08-06
- **Tranche:** T0 (correction)
- **Status:** **INCOMPLETE — fixes verified, suite unverifiable here.** See §5.
- **Corrects:** entry 0002, which declared T0 closed on a gate that never ran the
  test suite.

---

## 1. Why This Entry Exists

Entry 0002 parked T0 with a passing gate and recorded "smoke_test.py has never
been observed to pass" as a known gap. That framing was too generous. The suite
was not merely unobserved — **a test in it was failing, because of a change made
in T0**, and the gate was structurally incapable of noticing.

---

## 2. Why the Suite Does Not Finish

Three causes, compounding.

**2.1 All temp I/O is redirected onto the project's filesystem.**
`tests/test_smoke.py::setUpClass` sets `tempfile.tempdir` and monkey-patches
`tempfile.mkdtemp` to a directory beside the code. Tests that install whole
sidecar copies then `copytree` the full tree there, repeatedly. On local disk
that is fine; on a network or FUSE-mounted checkout it stalls past three minutes.

A supported override already existed — `SUITE_TEST_TMP` — and nothing documented
it. It is now referenced in the code comment and used by the gate.

**2.2 The collapse moved that directory outside the project.**
The line read `home.parent / ".useful-helpers-test-tmp"`, where `home` is the
directory above `tests/`. While the sidecar was nested, `home` was `toolkit/`,
so scratch landed at the repository root — which is where 40 stray files were
found during baseline preparation. After the collapse `home` **is** the root, so
`home.parent` pointed into the operator's staging folder. The suite had begun
writing outside the project it belongs to.

Changed to `home /`. This was a real defect introduced by T0 and not caught,
because the suite never ran.

**2.3 A test asserted the pre-T0 contract.**
`test_project_root_resolution` pinned the old behaviour: a plain home resolves to
itself, and a dot-prefixed folder name resolves to its parent. T0 removed both —
a name is not evidence of installation. Two of its four assertions were failing
by design.

Rewritten to assert the four evidence-only cases, plus a fifth the original
lacked: an invalid explicit root must raise rather than silently fall back.

**2.4 A test read 2,755 files where 136 ship.**
`test_d1_o1_single_inference_seam` asserts that exactly one module imports
`ollama`, by walking `root.rglob("*.py")` and reading every file. It skipped
`.venv`, `_artifacts`, `_state` and `tests` — but not the parts bin or the
harness targets.

While the sidecar was nested, `root` was `toolkit/` and the walk covered ~136
files. After the collapse `root` is the repository: **2,755 files, of which 95%
are reference material that does not ship.** Each is read in full. This was the
test the suite hung on.

Scoped to the payload. Measured before and after; the test now **passes**.

This is the third place describing what ships, after `_PAYLOAD_EXCLUDE` in the
harness and `CLEAN_APP_STRIP` in `vendor_export`. Convergence is a T1 item and
this entry raises its priority.

**2.5 `attach` full-remaps the whole repository, twice.**
`test_d1_p1_policy_overrides_survive_refresh` calls `attach {"refresh": true}`
twice. The self-test's work target is the repository, so each call re-maps
~18,000 files including the parts bin. Slow rather than wrong, and it resolves
when the parts bin is deleted at charter condition E9. Left alone.

---

## 3. A Structural Fault in the Gate

The T0 gate asserted that a test runner was **declared**, then pronounced the
baseline sound. It never executed the suite.

That is not a small omission. The gate exists so a tranche cannot be closed on
assertion alone, and it closed T0 while a test was red. A gate that does not run
the suite cannot report that the suite is broken.

The gate now runs `unittest discover` with `SUITE_TEST_TMP` on local storage, a
900-second ceiling, and an honest `SKIP` if it exceeds it — a skip is not a pass.

---

## 4. Also Corrected

`requirements-dev.txt` claimed the suite required `pytest`. It does not: the
suite is stdlib `unittest` throughout, run by a 25-line `smoke_test.py`. That
claim was made without checking, and is exactly the class of unverified assertion
this project's charter forbids.

---

## 5. Verification Standing

**Superseded by execution.** The sandbox returned with the project mounted and
everything below was run.

### 5.1 The suite cannot pass in this environment, and never will

The development mount **denies `unlink`**. Several tests delete files they
created under the project root, so they raise
`PermissionError: [Errno 1] Operation not permitted` — confirmed individually on
`test_c1_hands` (`_artifacts/_c1_probe.txt`) and `test_c4_data`
(`_artifacts/_c4.sqlite3`).

This is not a project defect and no amount of repair here will change it. **Full
suite verification requires a host with normal delete semantics — i.e. Windows.**

The gate now preflights this: it writes and deletes a probe file, and if unlink
is denied it records an honest `SKIP` naming the environmental cause rather than
accusing the project of a failure it does not have. A skip still blocks parking.

### 5.2 What was verified by execution

| Finding | Result |
| --- | --- |
| Suite runs at all with `SUITE_TEST_TMP` on local storage | yes — progressed steadily where it previously stalled |
| `test_d1_o1` payload scoping | **fixed — now passes** (was the hang) |
| `test_c1_hands`, `test_c4_data` errors | environmental: unlink denied, not project defects |
| Payload scan measurement | 2,755 files read vs 136 shipped — 95% waste |
| `_resolve_project_root` logic and rewritten assertions | 3 isolated tests, all passing |
| Full gate suite | 20 pass, 1 honest skip, exit 1 — correctly not parkable |

### 5.3 Two further gate self-corrections

The gate asserted `_artifacts` was absent. It is regenerable runtime output that
any tool run recreates — the same mistake already corrected for `_state` and
`logs`: a check the act of testing defeats. Scoped to `_design`, which is
archived and genuinely must not reappear.

That makes **five** gate assertions that were wrong rather than the state being
wrong. Every one was found by running the gate. The pattern is worth naming: an
assertion written from expectation is a hypothesis, and only execution
distinguishes a hypothesis from a fact.

What *was* verified: `_resolve_project_root` is self-contained, so it was
reproduced in isolation and exercised against the rewritten assertions plus two
edge cases the original test lacked. Three tests, all passing — the four
resolution cases hold, an invalid explicit root raises, an explicit root beats a
`.suite_sidecar` marker, and a whitespace-only override is treated as absent.

That verifies the *logic*. It does not verify the suite, the gate change, or the
temp-root fix.

### Uncommitted working-tree changes

| File | Change | Verified |
| --- | --- | --- |
| `tests/test_smoke.py` | temp root moved back inside the project | no |
| `tests/test_smoke.py` | `test_project_root_resolution` rewritten | logic only |
| `requirements-dev.txt` | pytest claim removed | no |
| `gates/t00_foundation.py` | gate now runs the suite | no |

### The baseline archive is stale

`useful-helpers-sidecar-baseline-v0.1.0-2026-08-06.zip` is a faithful snapshot of
the **committed** tree, but that tree contains the failing resolution test and the
temp root that escapes into the parent directory. **It should not be treated as
the saved project start state** until the suite runs green and the archive is
re-cut.

---

## 5.4 First real run — Windows, 85 tests, 170s

The suite completed for the first time. Every `unlink` error from the sandbox
disappeared, confirming those were environmental. `test_d1_o1` passed, confirming
the payload-scoping fix. Five genuine failures remained, all now repaired.

**The serious one: the vend shipped everything.** `CLEAN_APP_STRIP` excluded none
of the development zones, so `sidecar_install` copied **4,009 files** into a
target — `_harness`, `.bcc`, `_docs`, `gates`, `_trash`, and the entire parts bin.
The operator's reference library and this project's own build records would land
inside every project the sidecar is installed into. That breaks the precept
outright and makes E11 unmeetable.

The cause is the same one running through this whole entry: **the ship boundary
used to be the nested `toolkit/` folder.** Collapsing the sidecar to the root put
everything in scope and nothing re-drew the line. `test_target_is_never_modified`
was the symptom, failing on a `PermissionError` deep inside a copied `_harness`
target.

**Two further regressions from the collapse, both mine.** `paths.docs` still
pointed at `_docs/` after product documentation moved to `docs/`, so
`TOOLS.md` could not be found. And `test_seam_args_file_and_stdin` spawns the seam
from the source tree, which has no work target and correctly refuses — it tests
`--args-file` plumbing, not binding, so it now supplies an explicit root.

**Two from checking reference material.** `ruff` linted the parts bin, reporting
findings about predecessor code this project did not write and will delete; its
failure message was additionally lost to a cp1252 decode error on Windows pipes,
so the assertion reported `1 != 0` with nothing actionable. And
`test_docs_have_no_dangling_links` walked the whole repository — all nine dangling
links were predecessor READMEs citing absolute paths on another machine.

### The pattern, stated once

Four of the five failures, and the earlier hang, share one root cause: **a
boundary that was implicit in the folder layout became invisible when the layout
changed.** Scanning, linting, doc-checking and vending each had their own idea of
what "the project" meant, and each silently widened from ~136 files to thousands.

There are now four places describing what ships — `_PAYLOAD_EXCLUDE`,
`CLEAN_APP_STRIP`, `ruff.toml`, and the two test scopes. **Converging them on one
declared manifest is no longer a tidiness item; it is the fix for a defect class
that has now produced five separate failures.** T1.

---

## 6. Next Action

**Requires a Windows host — nothing further can be done in this sandbox.**

1. `set SUITE_TEST_TMP=%TEMP%\uh-test` then `python smoke_test.py`. This is the
   first environment where the suite can actually complete.
2. Repair whatever it surfaces. Expect the two `unlink` errors to disappear;
   anything else is a genuine finding.
3. `python gates\run.py` — the suite check will execute rather than skip, and the
   gate should reach 21 passing with no skips.
4. Re-cut the baseline archive only then.

Expect `test_d1_p1` to remain slow until the parts bin is deleted at E9 (§2.5).

T0 is **not** closed. Entry 0002's park stands corrected: it was closed against a
gate with a hole in it. The hole is closed, but the gate now honestly reports
that it cannot finish the job here — which is the correct outcome, not a
substitute for one.
