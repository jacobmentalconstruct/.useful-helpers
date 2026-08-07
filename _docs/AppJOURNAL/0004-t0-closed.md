# 0004 — T0 Closed

- **Date:** 2026-08-06
- **Tranche:** T0 — Foundation and Reset
- **Status:** **PARKED. Gate green on Windows — 23 assertions, no skips.**

---

## 1. Result

```
Ran 85 tests in 113.796s
OK

t00_foundation ... 23 PASS, 0 FAIL, 0 SKIP
SUITE: PASS
```

The suite check **executed** rather than skipping. That is the difference between
a closed tranche and a claimed one.

---

## 2. The Measurement That Matters

| | Before | After |
| --- | --- | --- |
| `sidecar_install` file count | **4,009** | **275** |
| Suite runtime | 170 s, 5 failures | 114 s, green |

The install figure is the whole point. A sidecar vended into a project was
carrying 4,009 files — the operator's twelve-application reference library,
this project's build records, its journal, its gates and its proving ground —
into every target it touched. It now carries 275: itself.

That number is the standing check on the vend manifest. If it climbs into the
thousands again, the boundary has leaked.

---

## 3. What Closed T0

Foundation (0001): one authority, one numbering, no inherited memory; the nesting
collapsed so the sidecar is the repository root; root resolution rewritten to
resolve by evidence with no fallthrough.

Baseline (0002): debris cleared, derived registry untracked, the BCC shipped inert
as a template, documents corrected to describe what the project actually is.

Repair (0003): five suite failures, all traced to one cause — **the ship boundary
had been implicit in the folder layout, and collapsing the layout erased it.**
Scanning, linting, doc-checking and vending each silently widened from ~136 files
to thousands.

---

## 4. Carried Into T1

**Converge the ship manifest.** Four places now describe what ships:
`_PAYLOAD_EXCLUDE` in the harness, `CLEAN_APP_STRIP` in `vendor_export`,
`extend-exclude` in `ruff.toml`, and two scoping sets in the test suite. Each was
fixed separately in 0003. One declared manifest, consumed by all four, is the
actual repair — and it is now a defect-prevention measure with five incidents
behind it, not a tidiness preference.

Also carried: ship a minimal payload `.gitignore` rather than the development one;
resolve `packaging/`, which is stripped from the vend while the installer is
deliverable #1; and gate E11 — vend to a scratch directory and assert no journal,
event log, evidence, development document, git history, build-machine path or
predecessor reference survives.

---

## 5. Standing Gaps

- `test_d1_p1` remains slow: `attach` full-remaps ~18,000 files twice because the
  self-test's target is the whole repository. Resolves when the parts bin is
  deleted at E11/E9.
- The suite cannot run on a filesystem that denies `unlink`. The gate detects this
  and skips honestly rather than reporting a false failure.
- `VERSION` still does not move when tools change.

---

## 6. Park Point

**T0 is closed.** The sidecar is one project, singly rooted, bound to nothing,
carrying no inherited memory or numbering, with an inert contract, documents that
describe what it is, a green suite, and a vend that ships only itself.

**Next.** Declare T1. It is not begun.
