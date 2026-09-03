# External Review: T7 Domain Truth (Text-Document Ratio Repair Candidate, `0050`)

Date: 2026-09-02T14:46:05Z
Reviewer: The Reviewer
Reviewed commit: `71db55c` (`Submit T7 text-document ratio repair for approval`); repair commit `59c4ab5`
Reviewed evidence: `.builder/journal/0050-t7-text-document-ratio-repair-awaiting-approval.md`;
prior reviews `20260902T120434Z` (with operator-ruling addendum) and `20260902T134914Z`;
T7 receipt `20260902T140854Z-09771121` and the cumulative receipts named by `0050`;
`product/core/substrate.py`, `.builder/gates/t7_domain_truth.py`,
`tests/test_t7_domain_truth.py`; Plan, Current State, Architecture, README; independent
re-run of all eight gates and canonical pytest on a clean off-repository copy at
`71db55c`; live probes on installed instances.

## Disposition

APPROVE CANDIDATE

## Executive Finding

Both items from the narrow return are repaired and verified on real and synthetic
targets, and nothing regressed. Text documents now enter the ratio test once they
outnumber software signals by more than 2:1, so a notes collection with helper scripts
reads `mixed` while a documented project still reads `software`; README-style names stay
ancillary regardless of count. `vendor`, `build`, and `dist` are untraversed only under a
software marker, so a records target's ordinary folders are observed. The T7 gate sets
`sys.dont_write_bytecode` for itself and passes 15/15 launched as plain `python` with no
flag and no environment variable, leaving no bytecode behind. All eight gates reproduce
PASS on a clean copy; pytest 72/72; the T3 gate is untouched; the T7 receipt is at
`59c4ab5` with an empty tree and the cumulative receipts differ from HEAD only by the
untracked receipts of earlier gates. The live repository is strong enough to justify
PARKED disposition and P7 credit.

## Correction to the Prior Review

The `20260902T134914Z` review stated that the gate's in-process import was "the
mechanism behind the hygiene-only FAIL receipts that `0042`, `0047`, and `0048` each
recorded." `0050` is right that this cannot be so: `_import_substrate` was introduced in
`cf4de91`, after those receipts existed. What I measured on `1c94cf5` was real and is
now fixed, but the earlier Windows receipts had a different, procedural cause (a manual
pytest or Ruff run without bytecode suppression between gate runs — I reproduced that a
plain `pytest` run writes `tests/`, `factory/`, and `product/__pycache__`). The prior
review's causal claim is withdrawn; its required action stands and is done.

## Findings

- [NOTE] The returned items are resolved.
  Evidence: `product/core/substrate.py::_text_documents_dominate`, `::_profile_decision`,
  `::_SOFTWARE_CONDITIONAL_PARTS`, `::_resource_records` (per-directory software
  context); `.builder/gates/t7_domain_truth.py` (`sys.dont_write_bytecode = True`, two
  new known-answer targets, two new executed mutations); probes below.
  Required action: none.

- [ADVISORY] `.html`, `.css`, and `.js` files establish software context for the
  conditional-folder rule.
  `_is_software_file` uses the full `_SOFTWARE_SUFFIXES` set, so a records target with a
  single `index.html` at its root (an exported document site, a SharePoint export)
  flips `vendor/` and `build/` to untraversed and the profile to `mixed`. Measured
  (probe B2): the same records target as probe B, plus one `index.html` → `mixed`, both
  folders untraversed. The limitation is disclosed, so this is honest; it is simply
  broader than intended. Recommend that only project-marker files (`_SOFTWARE_FILES`)
  and source suffixes other than web-asset suffixes establish software context.
  Required action: none for T7 closure; record as an accepted limitation or fold into
  T8 consolidation.

- [ADVISORY] Observations and relations still accrue per refresh (T3 design; recorded
  in `0049` and `0050`). Versions and evidence are stable (D1). No action.

- [NOTE] `0050` raises a point the pre-T8 ruling must settle: receipt SHA-256 values
  cited in journals through `0048` were computed over Windows working-tree bytes
  (CRLF); those from `0049` onward over Linux bytes (LF). Pinning line endings will
  change which family reproduces from a fresh checkout. The carried-findings ruling
  should say which bytes are canonical, and T8's sealing must compute digests over the
  canonical form. This is a good catch by the builder and belongs in the ruling, not in
  T7.

## Boundary Checks

- Confirmed: domain facts remain T3-owned; awareness reads only the T3 basis; no new
  target scanning, table access, or capability ownership was introduced.
- Confirmed: the software-context rule is computed inside `_resource_records` from
  directory contents during traversal; it creates no new state class and is disclosed
  through the existing untraversed-subtree limitation.
- Confirmed: no AI, embedding, vector, OCR, parser, cartridge, rollback, workflow, GUI,
  MCP-expansion, or mutation-expansion surface in the `59c4ab5` diff.
- Confirmed: the T3 gate file is byte-identical to `1c94cf5` and passes 12/12, so D1's
  stop rule continues to be satisfied.
- Confirmed: T0–T6 remain PARKED, P1–P6 credited, P7–P8 UNSCORED, T8 undeclared.

## Independent Measurement

Clean copy at `71db55c`, Linux 6.8 / CPython 3.13.15 / pytest 8.4.2 / Ruff 0.15.22:

- `pytest -q`: 72 passed. Ruff: passed. `git diff --check`: clean.
- T7 gate launched as plain `python` with `PYTHONDONTWRITEBYTECODE` unset: PASS 15/15,
  no `__pycache__` created.
- T6 11/11; T5 13/13; T4 14/14; T3 12/12; T2 13/13; T1 9/9; T0 13/13.

Probes (installed instances):

| Probe | Target | `1c94cf5` | `71db55c` |
|---|---|---|---|
| A | 60 `.md` + 3 `.py` | `software`, ancillary 60 | `mixed`, `mixed_text_documents_dominate` |
| A2 | 40 `.txt` + 1 `.py` | `software` | `mixed` |
| R1 | 10 `.py` + 20 `.md` (exactly 2:1) | — | `software`, ancillary 20 |
| R2 | 10 `.py` + 21 `.md` (>2:1) | — | `mixed` |
| R3 | 10 `.py` + 19 `.md` + `README.md` | — | `software` (README not counted toward dominance) |
| R4 | 5 `.md` + `Makefile` | — | `mixed` (marker present; honest) |
| B | records target with `vendor/`, `build/` PDFs + CSVs | untraversed | `records_documents`, 16 resources, both traversed |
| B2 | probe B + one `index.html` | — | `mixed`, both untraversed (advisory above) |
| B3 | `pyproject.toml` project with `vendor/lib/*.py` and `docs/build/` | — | `software`; `path:vendor/`, `path:docs/build/` untraversed, nothing beneath |
| H | this repository | `software`, 494 | `software`, 500 resources, 0.61 s, `.git` untraversed |
| H′ | H refreshed again unchanged | — | versions 504→504, evidence 803→803 (D1 holds); projection `100 of 4906` disclosed (D2 holds) |

## Requirement Matrix

All `0044` items 1–11 and `0045` items A1–A4: PASS. The declaration's three named
risks — overclaiming from weak signals, ownership drift, and software as the default
target shape — are each now rejected by an executed known-answer target in the gate and
by a fixture, and the third has been exercised in both directions (documents winning,
software winning) on real inputs.

Discrimination: the executed mutations in the T7 gate (generated traversal re-enabled,
vendor traversal re-enabled, `.json` as records, README-style docs as records, detect-
only profile, text always ancillary, conditional folders unconditional) each cause the
known-answer check to fail. Text-level checks remain as a secondary layer.

## Closure Review Pass

The live repository is strong enough to justify operator approval, PARKED disposition,
and P7 credit. The tranche proves what it declared — truthful breadth across
substantial software, mixed records/documents, empty/nascent, unobserved, and
weak-material targets — on real inputs, with T3 ownership, T4 projection, honest
limitations, no runtime-state side effects, entrance parity, correct provenance, and
executed discrimination. The remaining advisory is a disclosed edge, not a defect in an
accepted claim.

Recommended park-entry contents: the D1–D3 rulings as applied; the accepted prototype
limitations (size/mtime freshness for metadata-only material; per-refresh growth of
observations and relations; the `.html` software-context edge); and the statement that
all T7 closure receipts are Linux and Windows evidence is deferred to the pre-T8 work
below.

## Pre-T8 Position (unchanged, now the only open items)

1. `.gitattributes` and a renormalization commit; then one Windows T7 receipt. Until
   then Windows receipts are mechanically impossible because `working_tree_provenance`
   correctly refuses CRLF-only modifications, and P8 requires Windows.
2. A journal ruling on carried findings C1–C5 and H2–H3, pointed to from the Plan,
   including which byte form is canonical for receipt SHA-256 values.

Neither is a T7 surface. Both should precede the T8 declaration.

## Suggested Operator Action

Approve the `0050` candidate; direct the Builder to perform park closeout, credit P7,
and update the journal/Plan/Current State/Architecture/README chain; then, before any
T8 declaration, rule on the two pre-T8 items above.

This review is evidence, not a ruling. The operator grants approval, PARKED status, and
P7 credit; T0–T6 remain parked and are not reopened by anything here.
