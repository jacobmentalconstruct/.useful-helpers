# External Review: T4 Awareness

Date: 2026-08-27T13:33:09Z
Reviewer: The Reviewer
Reviewed commit: 3970edca167ac7b322fc08f1450b5f506da975a3
Reviewed evidence: T4 `20260827T121444Z-3713df86`; T3 `20260827T121540Z-e2537cb9`; T2 `20260827T121638Z-c56e1983`; T1 `20260827T121715Z-4224b7b5`; T0 `20260827T121805Z-76c89c89`; `.builder/journal/0031-t4-basis-freshness-repair-awaiting-approval.md`

## Disposition

APPROVE CANDIDATE

## Executive Finding

T4 appears cleanly positioned for operator approval. The prior basis/freshness gap was returned in `0030`, repaired in the T3 substrate API plus T4 awareness composition path, and resubmitted in `0031` with behavioral gate evidence rather than static-only inspection. I found no approval-blocking T4 requirement gap.

## Findings

- [NOTE] The repaired T4 gate receipt was produced at commit `ae5d5ac`, while reviewed HEAD is `3970edc`; intervening changes are recorded evidence, review/status documentation, and manifests, not T4 product source or tests.
  Evidence: `.builder/evidence/T4/20260827T121444Z-3713df86/t4-gate.json`; `git diff --name-status ae5d5ac70989a934fa703f5dd1b118d7166cc516..HEAD`
  Required action: none

- [NOTE] The T4 state remains correctly unparked and P4 remains uncredited pending operator decision.
  Evidence: `.builder/CURRENT_STATE.md`; `.builder/TRANCHE_PLAN.md`; `.builder/journal/0031-t4-basis-freshness-repair-awaiting-approval.md`
  Required action: none

## Boundary Checks

- Confirmed: T4 consumes T3 through `substrate.py` APIs/handles rather than direct T3-table ownership.
- Confirmed: T4 owns awareness revisions/items only.
- Confirmed: T4 does not create or mutate T3 resources, versions, observations, epistemic evidence, claims, or relations.
- Confirmed: T4 does not create or mutate T2 receipts, operational artifacts, or App Journal entries.
- Confirmed: T4 does not introduce MCP, GUI, local AI, embeddings, mutation governance, release/update/removal, or domain cartridges.
- Confirmed: P4 is not credited and T5 has not begun.
- Confirmed: T0-T3 remain parked; no new failed parked premise was identified.

## Evidence Checked

- Inspected `.builder/evidence/reviews/REVIEWER_MANIFEST.md`.
- Inspected `.builder/BCC.md`, `.builder/TRANCHE_PROTOCOL.md`, `.builder/TRANCHE_PLAN.md`, `.builder/CURRENT_STATE.md`, `docs/PRODUCT_CHARTER.md`, and `docs/ARCHITECTURE.md`.
- Inspected T4 journal chain: `0026`, `0027`, `0028`, `0029`, `0030`, and `0031`.
- Inspected T4 gate receipt `.builder/evidence/T4/20260827T121444Z-3713df86/t4-gate.json`: PASS 13/13, SHA-256 `55D7B8629A42AB9648942553F187167468B6E555219BB91F2A402B165164E923`.
- Inspected source functions `product/core/substrate.py::current_awareness_basis`, `product/core/substrate.py::target_signature`, and `product/core/awareness.py::refresh`.
- Inspected tests `tests/test_t4_awareness.py::test_t3_basis_mismatch_is_stale_during_awareness_refresh` and `tests/test_t4_awareness.py::test_latest_empty_basis_does_not_leak_historical_resources_or_claims`.
- Inspected gate check `.builder/gates/t4_awareness.py::_basis_freshness_behavior`.
- Ran `python -B -m pytest -q`: 39 passed.
- Ran `python -m ruff check . --no-cache`: passed.
- Ran `git diff --check`: passed.
- Ran `git status --short --branch`: clean on `codex/t1-mechanical-host`, ahead of origin.

## Discrimination Review

- Plausible wrong implementation: awareness could compose from accumulated `list_resources()` / `list_claims()` and leak deleted historical records. Covered by `test_latest_empty_basis_does_not_leak_historical_resources_or_claims` and T4 gate `basis_freshness_behavior`.
- Plausible wrong implementation: awareness could compute freshness from live target state at T4 refresh and report `current` despite T3 basis mismatch. Covered by `test_t3_basis_mismatch_is_stale_during_awareness_refresh` and T4 gate `basis_freshness_behavior`.
- Plausible wrong implementation: awareness could bypass T3 ownership with direct SQL against T3 tables. Covered by `.builder/gates/t4_awareness.py::_awareness_owner` static scan and source inspection showing use of `substrate.current_awareness_basis()`.
- Plausible wrong implementation: awareness could create receipt, artifact, or App Journal side effects. Covered by `tests/test_t4_awareness.py::test_awareness_does_not_collapse_runtime_journal_or_substrate_owners`.
- No material T4 approval gap identified.

## Residual Risk

- Awareness remains compact and deterministic; richer semantic orientation is intentionally outside T4.
- Freshness is based on a coarse target/resource signature and is suitable for the declared prototype boundary, not a full watcher or mutation-governance mechanism.
- T4 does not address P5-P8; those remain later tranche work.

## Suggested Operator Action

Approve the repaired T4 candidate for PARKED disposition and P4 credit, then instruct the builder to perform normal T4 park closeout. Do not declare or implement T5 until after the park entry and state/plan synchronization are complete.
