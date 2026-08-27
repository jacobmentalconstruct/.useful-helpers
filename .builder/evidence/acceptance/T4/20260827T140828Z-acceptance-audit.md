# Acceptance Audit: T4 Awareness

Date: 2026-08-27T14:08:28Z
Auditor: Tranche Acceptance Auditor
Reviewed commit: f7e58ea3f9f12e5e5109151474dd4527a939095c
Reviewed tranche state: AWAITING_APPROVAL
Reviewed evidence: journals `0026`-`0031`; T4 gate `20260827T121444Z-3713df86`; cumulative T3 `20260827T121540Z-e2537cb9`, T2 `20260827T121638Z-c56e1983`, T1 `20260827T121715Z-4224b7b5`, and T0 `20260827T121805Z-76c89c89`; Reviewer report `20260827T133309Z-external-review.md`

## Verdict

RETURN TO VERIFYING - BOUNDED REPAIR

## Executive Finding

The repaired basis/freshness behavior is sound under the declared sequential witnesses, the live T4 source digest still matches the clean authoritative receipt, and all focused and cumulative tests pass. T4 is nevertheless not yet strong enough for operator approval, PARKED status, or P4 credit: observed awareness omits the explicit limitations required by the declaration, emitted `relation:` provenance handles do not round-trip through their T3 owner, and the public `awareness-item:` identifiers introduce a second awareness-owned handle form despite the operator-approved canonical `awareness:` boundary. These are bounded T4 acceptance defects, not grounds to redeclare T4 or reopen a parked tranche.

## Blocking Findings

- [REQUIRED] Observed awareness revisions report no explicit limitations.
  Requirement: P4 requires awareness with limitations; declaration `0026` scope and completion evidence 3 require explicit limitations and unknowns, especially for empty or thin targets.
  Evidence: `product/core/awareness.py::refresh` assigns `limitations = []` for every observed basis. A live non-empty consumer probe returned `"limitations": []`; `tests/test_t4_awareness.py` asserts limitations only for the missing-basis case and does not test them after an empty or non-empty substrate refresh.
  Required action: Emit truthful projection limitations for observed empty/thin and non-empty bases, and add focused plus gate assertions that reject an observed revision whose required limitations are empty.

- [REQUIRED] T4 emits provenance handles that its owning T3 layer cannot resolve.
  Requirement: Declaration `0026` completion evidence 4 requires stable handles that resolve through T3 CLI/API to resources, versions, observations, evidence, claims, and relations where applicable; P4 requires stable round-tripping handles.
  Evidence: `product/core/substrate.py::current_awareness_basis` appends `relation:<relation_id>` values to `source_handles`, but `product/core/substrate.py::trace` rejects the `relation` node type and the CLI exposes no relation read command. An adversarial live probe resolved the emitted `path:`, `version:`, `observation:`, `evidence:`, and `claim:` prefixes but received `SubstrateError: unsupported trace node type: relation` for `relation:`. Existing T4 tests round-trip only path and claim finding handles.
  Required action: Provide a T3-owned resolver/CLI round trip for emitted relation handles, or revise the projection contract so it emits only handles that the owning layer can resolve while preserving provenance traversal. Add a behavioral witness that enumerates every emitted source-handle prefix and resolves it through its owner.

- [REQUIRED] Public awareness item identifiers use a second awareness-owned handle form.
  Requirement: Operator amendment `0027` directs one canonical awareness-owned handle form, `awareness:<digest-or-id>`.
  Evidence: `product/core/awareness.py::_awareness_id` returns `awareness:<id>`, while `_item_id` returns `awareness-item:<id>` and that identifier is the public argument to `awareness drill`. The T4 gate's discrimination check rejects `revision:` but does not reject `awareness-item:`.
  Required action: Bring revision and item identifiers under the approved canonical `awareness:` form, then strengthen the gate to reject alternate awareness-owned handle prefixes.

## Acceptance Matrix

| Declared requirement | Result | Evidence | Gap, if any |
|---|---|---|---|
| 1. Fresh attach has blank awareness and lower state remains blank until explicit action | PASS | `test_fresh_attach_starts_with_blank_awareness_and_runtime_state` | None identified |
| 2. Missing substrate basis yields unknown, not fabricated orientation | PASS | `test_unobserved_target_refresh_reports_unknown_basis_without_rich_findings`; `awareness.refresh` missing-basis branch | None identified |
| 3. Empty observed target yields an immutable thin revision with explicit limitations and unknowns | FAIL | `test_empty_target_awareness_is_thin_and_immutable`; `awareness.refresh` | The revision is thin and immutable but its `limitations` list is empty |
| 4. Non-empty orientation exposes stable T3 handles that round-trip across applicable record classes | FAIL | Live prefix-resolution probe; `substrate.current_awareness_basis`; `substrate.trace` | Emitted `relation:` handles have no T3 resolver |
| 5. Later refresh preserves the prior revision and original basis/handles | PASS | `test_empty_target_awareness_is_thin_and_immutable`; insert-only owner inspection | Existing checks are adequate for the implemented path |
| 6. Target or observed-basis mismatch is not silently current | PASS | `test_freshness_becomes_stale_after_target_change_without_refresh`; `test_t3_basis_mismatch_is_stale_during_awareness_refresh`; gate `basis_freshness_behavior` | None identified for declared sequential behavior |
| 7. Awareness drill reaches T3 provenance without copying T3 authority | PARTIAL | `test_non_empty_awareness_exposes_resolvable_t3_handles_and_drill`; owner inspection | Claim/path drill works, but an emitted direct relation handle does not round-trip |
| 8. Awareness storage remains distinct from T3, receipts, artifacts, and App Journal | PASS | Schema inspection; `test_awareness_does_not_collapse_runtime_journal_or_substrate_owners` | None identified |
| 9. Awareness refresh does not create App Journal entries or collapse into receipts | PASS | Separation fixture and source inspection | None identified |
| 10. Lower layers do not import awareness | PASS | T4 gate structural check; live source search | None identified |
| 11. No MCP, GUI, vector/embedding, cartridge, or T5 mutation surface enters T4 | PASS | T4 gate and source inspection | None identified |
| 12. Focused, canonical, Ruff, T4, and cumulative lower-tranche checks pass from the candidate | PASS | Live 8/8 focused and 39/39 canonical pytest; live Ruff; T4 receipt PASS 13/13; cumulative receipts all PASS | The working tree contains only this requested audit outside HEAD; the live T4 source digest exactly matches the clean receipt digest |
| Amendment: T4 reads T3 semantics only through `substrate.py` APIs/handles | PASS | `awareness.py` imports/calls substrate owner and directly queries only awareness tables | None identified |
| Amendment: direct target signature is freshness-only | PASS | `awareness._freshness`; `substrate.target_signature`; source inspection | None identified |
| Amendment: T2 receipt/App Journal data is not an independent T4 input | PASS | Source inspection and separation fixture | None identified |
| Amendment: one canonical `awareness:` handle form | FAIL | `_awareness_id`; `_item_id`; CLI drill contract | `awareness-item:` is a second public awareness-owned form |

## Reviewer Agreement

This audit agrees with the Reviewer that entry `0030`'s basis/freshness defect was materially repaired, that no T4 product/test/gate source changed after the clean authoritative receipt, that T2/T3 ownership boundaries remain intact, and that T0-T3 should remain parked. It disagrees with `APPROVE CANDIDATE` because the Reviewer exercised path and claim handles but did not enumerate all emitted source-handle types, treated field presence as sufficient for limitations without checking observed revisions, and did not compare the public item identifier with amendment `0027`'s single-handle-form direction. The Reviewer inspected commit `3970edc`; current HEAD `f7e58ea` differs only by the Acceptance Auditor Manifest and the later commit of the Reviewer report itself, so the disagreement is evidentiary rather than caused by product-source staleness.

## Verification Performed

- Read the controlling BCC, Tranche Protocol, Tranche Plan, Product Charter, Architecture, Current State, T4 journal chain `0026`-`0031`, Reviewer report, T4 receipt, T4 owner/source, CLI, storage migration, focused tests, and authoritative gate.
- Confirmed final reviewed HEAD `f7e58ea3f9f12e5e5109151474dd4527a939095c`. During the audit, a repository-external action committed the previously untracked T4 Reviewer report and advanced HEAD from `46671a0` to `f7e58ea`; inspection of that one-commit diff found only the Reviewer report. Final status contains only this requested audit outside HEAD. Diff from receipt commit `ae5d5ac` contains evidence, journal/status documentation, README/Architecture synchronization, role manifests, and review evidence, with no T4 product, test, or gate change.
- Verified T4 receipt SHA-256 `55D7B8629A42AB9648942553F187167468B6E555219BB91F2A402B165164E923` and independently recomputed live gate source digest `c94528675c07347e31f13825e92758bc367c73c83f81ba633232cb97301ad5bf`, equal to the receipt.
- Ran `python -B -m pytest tests\test_t4_awareness.py -q` (8 passed), `python -B -m pytest -q` (39 passed), `python -m ruff check . --no-cache` (passed), and `git diff --check` (passed).
- Ran an isolated installed-target probe that refreshed T3 then T4, inspected limitations and both awareness-owned identifier prefixes, and attempted owner-layer resolution for every emitted T3 source-handle prefix. All prefixes except `relation:` resolved.
- Inspected cumulative clean receipts: T3 12/12, T2 13/13, T1 9/9, and T0 13/13; their file hashes agree with entry `0031`.

## Effect On Parked Prior Tranches

T0-T3 remain PARKED. The findings concern the T4 projection contract and its acceptance evidence; they do not invalidate a parked correctness, safety, architecture, usability, or maintainability claim in T0-T3. No reopen recommendation exists.

## Residual Risk

- `current_awareness_basis()` assembles its view across multiple SQLite reads without an explicit read transaction and opens a second connection for evidence lookup. Concurrent substrate refresh behavior is undeclared and untested; this is advisory for the current sequential prototype but should be made explicit before concurrency is claimed.

## Suggested Operator Action

Return T4 to VERIFYING for a bounded repair of observed limitations, complete T3-owner round trips for every emitted provenance handle, and the canonical awareness-owned handle namespace. Require adversarial fixtures and gate witnesses for those exact gaps, then rerun focused T4, canonical pytest/Ruff, T4, and cumulative T3/T2/T1/T0 checks from a clean committed candidate. Do not redeclare T4, reopen T0-T3, park T4, credit P4, or begin T5 before the repaired submission is reviewed.
