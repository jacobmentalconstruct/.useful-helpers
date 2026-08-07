# 0005 — T1 Declared: One Ship Manifest

- **Date:** 2026-08-06
- **Tranche:** T1 — One Ship Manifest
- **Status:** **DECLARED. Gate written, failing as expected. No implementation.**

---

## 1. Declaration

**Outcome.** Exactly one declared description of what the sidecar ships, consumed
by every place that needs it — and a vend that provably contains only the sidecar,
carrying none of its own history.

**Non-goals.** No UI. No chains. No ledger or presence work. No new tools. No
change to root resolution — that closed in T0.

**Expected changed surfaces.** A new manifest module; `tools/vendor_export/cli.py`;
`_harness/harness.py`; two scoping sets in `tests/test_smoke.py`; `ruff.toml`; a
payload `.gitignore`.

---

## 2. Why This Tranche Exists

Five defects trace to this boundary being undeclared.

The ship boundary used to be the nested `toolkit/` folder — implicit, but real.
Collapsing the sidecar to the repository root erased it, and four separate
mechanisms had each been silently relying on it:

| Consumer | Failure it produced |
| --- | --- |
| `vendor_export` / `sidecar_install` | vended 4,009 files into every target |
| `_harness::_PAYLOAD_EXCLUDE` | would have copied targets into themselves |
| `ruff.toml` | linted twelve predecessor applications |
| two test scopes | a hang, and nine false dangling-link failures |

Each was repaired individually in entry 0003. That left four descriptions of the
same rule, free to drift apart again. **Convergence is the actual fix**, and it is
defect prevention with an incident history, not tidiness.

---

## 3. Numbering

T1 originally read *Explicit Target and Root Safety*. That work was pulled forward
into T0 — collapsing the sidecar exposed the defect live, so root resolution was
rewritten and verified there. The slot is reused; **T2–T10 are unchanged.**
`TRANCHE_PLAN.md` has been corrected so it no longer describes a tranche that does
not exist.

---

## 4. The Gate, Written First

`gates/t01_ship_manifest.py` — authored before implementation, currently failing
at its first assertion, which is the intended state.

It asserts: one manifest module exists and names every development zone; each of
the three importing consumers derives from it rather than repeating it;
`ruff.toml` (static TOML, cannot import) has not drifted from it; a **real vend**
into a scratch directory leaks no development zone and does not recurse; **E11** —
no journal, event log, evidence, charter, plan, `.git`, build-machine absolute
path or predecessor project name survives; the payload ships its own minimal
ignore file rather than the development one; and the vended file count stays
within a declared bound.

That last one is the regression signal. It is the check that would have caught
4,009 files shipping where 275 belong.

---

## 5. Implementation Plan

1. Declare the manifest once — `src/core/payload.py`, exporting `NEVER_SHIP`,
   `EXCLUDE_SUFFIXES` and `MAX_PAYLOAD_FILES`.
2. Derive `vendor_export`'s `EXCLUDE_DIRS` and `CLEAN_APP_STRIP` from it.
3. Derive the harness's `_PAYLOAD_EXCLUDE` from it.
4. Derive both test scoping sets from it.
5. Reconcile `ruff.toml`; the gate enforces agreement, since TOML cannot import.
6. Ship a minimal payload `.gitignore` — the sidecar's own `_state`, `_artifacts`
   and `logs`, and nothing about the parts bin or harness. `vendor_export` already
   swaps documents on export via `CLEAN_APP_DOC_OVERRIDES`; the same mechanism
   fits.
7. Record the `packaging/` decision explicitly. It is stripped from the vend while
   the installer is deliverable #1 — the existing rationale is that the installer
   wraps the product from *outside* the payload, which appears correct but is
   currently only a code comment.
8. Implement and verify **E11**.

---

## 6. Known Risks

- **`packaging/` may be the wrong call.** If the installer must ship *with* the
  sidecar rather than wrap it, step 7 reverses. Decide on evidence.
- **The `.gitignore` swap adds a second export-time substitution.** Two
  substitutions are a pattern; three would be a mechanism wanting a name.
- **The predecessor-name scan may find false positives** in legitimately vendored
  code. If so, narrow it rather than delete it.
- **`ruff.toml` agreement is gated, not derived.** A generated lint config would be
  stronger; it is deliberately deferred as scope.

---

## 7. Stop Condition

`python gates/run.py` green — T0 and T1 — on a host with normal delete semantics.

Nothing is implemented. This entry declares only.
