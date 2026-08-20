# 0042 — Closure Gate 1 (Parity) **CERTIFIED**

- **Date:** 2026-08-20
- **Gate:** Closure gate 1 of 2 — parity certification
- **Record:** `20260820-102959-windows-3b2ecdb-parity-closure.json` — **PASS**, clean tree
- **Preceded by:** T8 parked at `445a68c` (0040); coverage rule (0041)

---

## 1. The certified state

```text
VERDICT   PASS      commit 3b2ecdb    dirty=False    763.3s    Windows
lint      ok
suite     ok        88 tests, 1 skipped, 0 failures
gates     ok        262/262 assertions, ZERO SKIPPED
discovery ok        12 tools exercised, no failed axes
            precept pass | front_door pass | enforcement pass | cleanliness pass
```

Two closure certifications were run. The first (`9b0e651`, 87 tests) certified the parity
state; the second (`3b2ecdb`, 88 tests) certifies it *with the post-parity audit folded
in*. The second is the record of reference — it is the one whose suite contains the
regression guard over the five new behaviours.

Three axes report **unscored**, correctly and by design: `composition` and `truthfulness`
have no oracle on an adopted target, and `tool_health` has no declared threshold. None is
counted as a pass. That distinction is the C4a rule doing its job in a real record.

---

## 2. Parity, final

| disposition | rows |
| --- | --- |
| Retained — direct | 36 |
| Retained — composed | 17 |
| Superseded | 15 |
| Retained — FAILING | **0** |
| open / deferred | **0** |
| **TOTAL** | **68** |

- 53 retained rows executed through the governed runtime, each recording fixture,
  invocation, expected useful product, observed evidence and verdict
- six repaired rows plus five discriminating checks — 11/11
- both suites re-run with `.plans-and-parts_FOR-REFERENCE-ONLY` **physically moved out of
  the tree**, then restored

**The donor corpus is no longer load-bearing.** The only references to it anywhere in
`src/`, `tools/`, `apps/`, `gates/`, `config/` or `packaging/` are exclusion declarations
and one gate reading a provenance archive.

---

## 3. What this gate cost, and what that says

Three defects were found by *executing* rows the census had marked satisfied, and none of
them was visible by reading:

- **`projectmapper` emitted two of four declared markdown exports.** The donor contract
  names tree, filedump, combined and manifest; only the first two were ever written. The
  manifest existed as a JSON sidecar and a one-line blurb inside the database — neither is
  a document a human opens to see what a snapshot *is*.
- **`patch` had no path containment at all**, while `edit` and `write_file` both resolved
  within the roots. Census row 11.5 claimed containment "on every file read and store
  write"; that claim was false for this tool. Later mutation-testing showed the tool would
  otherwise **open `/etc/hostname`** — it returned "search block not found", which is what
  reading a real file looks like.
- **My own `pull --ff-only` was safe and useless.** `sync` commits before pulling, so any
  remote advance is a divergence, so the pull always refused and the push never happened.
  Pull-before-push that can never integrate anything is a ceremony. Caught only because
  the assertion demanded *repository* evidence — a second clone advancing the remote —
  rather than command text.

And one found by asking what certification actually runs: **the five new parity behaviours
had zero coverage in the certified suite.** A closure gate proves a thing was delivered
once; a regression guard proves it is still there. Parity did the first only.

---

## 4. Standing debts, none of them STOP blockers

| item | disposition |
| --- | --- |
| 26 Apply tools declare no `writes` field | bounded manifest-truth pass; `patch` and `git` corrected as they came due |
| `tool_health` reports a rate with no threshold | acceptance walk decides the bar, or declares it informational |
| `composition` / `truthfulness` need oracle controls | **C4a — required by the acceptance walk**, fixtures already exist and are mutation-tested |
| `secret_audit` exceeds `DEFAULT_TIMEOUT_S = 120` on this tree | Charter §7.4's module-level timeout, now observed rather than theorised |
| `dead_code` reports 8 false positives scoped to `src/` | informational; the callers are in `gates/` |
| `domain_boundary_audit`: 38 crossings, no policy | unchanged since 0034 |
| ProjectMapper dot-directory pruning | parked; not part of any row that has come due |

---

## 5. Remaining before STOP

**Closure gate 2 — release certification.** One question, narrowly:

> Can this repository become an artifact another machine installs and uses without the
> development checkout?

Clean clone → release artifact → fresh Windows *and* Linux → install into a code, records
or empty target → documented launcher → `attach` → external MCP agent → parity products →
the T8 change loop → update preserves UUID and state → deleting an untouched sidecar
leaves target-owned content unchanged. And inspect the distribution: no parts bin, no
harness, no journals, no accumulated state, no source history, no build-machine paths.

**The acceptance walk still owes C4 coverage**: only `_theCELL` is adopted. B (mixed
records/documents) and C (empty/nascent) do not exist yet, and the two oracle controls
must run beside them under the C4a rule.

Use the existing payload and vend mechanism first. Build an assembler only if a real
release attempt proves the existing one cannot produce a clean release.
