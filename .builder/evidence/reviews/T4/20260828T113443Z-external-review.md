# External Review: T4 Awareness Repair

Date: 2026-08-28T11:34:43Z
Reviewer: The Reviewer
Reviewed commit: 2953a1fda352eebebc820b5a4774f236acabf18d
Reviewed evidence: journal `0034-t4-acceptance-repair-awaiting-approval.md`; T4 gate `20260828T111925Z-d9548015`; prior acceptance audit `20260827T140828Z-acceptance-audit.md`; prior Reviewer follow-up `20260827T141302Z-external-review.md`; live focused/canonical pytest, Ruff, and diff-check commands

## Disposition

APPROVE CANDIDATE

## Executive Finding

The repaired T4 candidate resolves the three bounded return findings from `0032`: observed awareness now carries explicit limitation content, every emitted T3 source/provenance handle has a T3-owned read path, and public awareness-owned identifiers use the `awareness:` namespace without exposing the rejected `awareness-item:` prefix. I found no approval-relevant T4 boundary regression and recommend operator approval/PARK/P4 credit through the normal closeout chain.

## Findings

- [NOTE] No remaining bounded T4 repair finding identified.
  Evidence: `product/core/awareness.py::_observed_limitations`; `product/core/substrate.py::read_relation`; `product/core/substrate.py::_load_node`; `product/core/cli.py` substrate read commands; `tests/test_t4_awareness.py::test_all_emitted_t3_source_handles_round_trip_through_substrate_owner`; `.builder/gates/t4_awareness.py::_handle_round_trip_behavior`; T4 receipt `20260828T111925Z-d9548015`.
  Required action: none.

## Boundary Checks

- Confirmed: T4 consumes T3 through `substrate.py` APIs/handles; `awareness.py` calls `substrate.current_awareness_basis`, `substrate.target_signature`, and T3 read/trace APIs, and direct SQL is limited to awareness-owned tables.
- Confirmed: T4 owns awareness revisions/items only; no awareness owner writes T3 resources, versions, observations, evidence, claims, or relations.
- Confirmed: awareness refresh does not create T2 receipts/artifacts or App Journal entries; focused separation fixture asserts empty receipts and journal entries after awareness refresh.
- Confirmed: no MCP, GUI, local AI, embeddings/vector index, mutation governance, release/update/removal, or domain cartridges were introduced by T4.
- Confirmed: T0-T3 remain PARKED; T4 remains AWAITING_APPROVAL; P4 is not credited; T5 has not begun.

## Evidence Checked

- Read `.builder/evidence/reviews/REVIEWER_MANIFEST.md`.
- Inspected `.builder/CURRENT_STATE.md`, `.builder/TRANCHE_PLAN.md`, `docs/ARCHITECTURE.md`, and journals `0032`, `0033`, and `0034`.
- Inspected prior Acceptance Auditor and Reviewer findings: `.builder/evidence/acceptance/T4/20260827T140828Z-acceptance-audit.md` and `.builder/evidence/reviews/T4/20260827T141302Z-external-review.md`.
- Inspected T4 receipt `.builder/evidence/T4/20260828T111925Z-d9548015/t4-gate.json`: PASS 14/14 from committed candidate `cc0b39de0ec61ef3f7508d9569804fce9575f6c2`.
- Ran `git diff --name-status cc0b39de0ec61ef3f7508d9569804fce9575f6c2 HEAD`: later committed changes are documentation/evidence only, with no product, test, or gate source drift from the receipt candidate.
- Ran `python -B -m pytest tests\test_t4_awareness.py -q -p no:cacheprovider`: 9 passed.
- Ran `python -B -m pytest -q -p no:cacheprovider`: 40 passed.
- Ran `python -m ruff check . --no-cache`: passed.
- Ran `git diff --check`: passed.
- Ran `git status --short --branch` before saving this review: clean branch, ahead of origin by 2 commits.

## Discrimination Review

- Plausible wrong implementation: observed awareness could expose a `limitations` field while leaving observed revisions empty. Rejected by `awareness.py::_observed_limitations`, focused assertions for empty/non-empty observed revisions, and gate `handle_round_trip_behavior`.
- Plausible wrong implementation: awareness could emit provenance-looking T3 handles without owner resolution. Rejected by the all-prefix behavioral fixture, new substrate read APIs for versions/observations/relations, and `trace` support for `relation:`.
- Plausible wrong implementation: the old `awareness-item:` public identifier could remain while static checks only looked for generic awareness handles. Rejected by focused assertions and gate discrimination for `awareness-item:`.
- Plausible wrong implementation: T4 repair could widen into lower-layer ownership or T5 mutation. Rejected by source inspection, gate boundary checks, and focused separation fixture.

## Residual Risk

- `awareness:item:<id>` is a typed handle form under the canonical `awareness:` namespace. I do not treat it as the rejected second prefix, but future declarations may want to state whether typed subforms under `awareness:` are intentionally allowed.
- `current_awareness_basis()` still assembles a sequential prototype view without declaring concurrency behavior; this is not a T4 approval blocker unless concurrency is claimed.

## Suggested Operator Action

Approve the repaired T4 candidate, park T4 through the normal operator closeout, and credit P4. Do not begin T5 until the T4 park/credit entry is recorded and the T5 declaration is reviewed with the named migration-stamp precondition and other operator-directed scope items.
