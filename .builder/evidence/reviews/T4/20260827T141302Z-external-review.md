# External Review: T4 Awareness Follow-Up

Date: 2026-08-27T14:13:02Z
Reviewer: The Reviewer
Reviewed commit: a8dba976227a21aaca8cc1ba09c4313fe91f7ade
Reviewed evidence: Acceptance audit `.builder/evidence/acceptance/T4/20260827T140828Z-acceptance-audit.md`; prior Reviewer report `.builder/evidence/reviews/T4/20260827T133309Z-external-review.md`; T4 gate `20260827T121444Z-3713df86`; journals `0026`-`0031`

## Disposition

RETURN TO VERIFYING

## Executive Finding

The Acceptance Auditor identifies material T4 approval gaps that my earlier `APPROVE CANDIDATE` review missed. Current HEAD still matches those findings: observed awareness revisions can carry empty limitations, emitted `relation:` provenance handles do not round-trip through a T3 owner resolver, and public `awareness-item:` identifiers create a second awareness-owned handle form contrary to the amended T4 boundary.

## Findings

- [REQUIRED] Observed awareness revisions do not emit explicit limitations.
  Evidence: `product/core/awareness.py::refresh` sets `limitations = []` for observed bases; `tests/test_t4_awareness.py` asserts limitations only for missing-basis behavior; `.builder/evidence/acceptance/T4/20260827T140828Z-acceptance-audit.md`.
  Required action: Add truthful limitations for observed empty/thin and non-empty awareness and require focused/gate evidence that observed revisions cannot pass with empty required limitations.

- [REQUIRED] T4 emits `relation:` provenance handles that do not round-trip through T3.
  Evidence: `product/core/substrate.py::current_awareness_basis` emits `relation:<id>` handles; `product/core/substrate.py::trace` has no `relation` node support and raises unsupported trace node type; existing T4 tests round-trip path/claim handles only.
  Required action: Add a T3-owned relation resolver/CLI/API round trip, or stop emitting unresolved relation handles while preserving provenance traversal; add a behavioral witness over every emitted source-handle prefix.

- [REQUIRED] Public awareness item IDs use a second awareness-owned handle form.
  Evidence: `product/core/awareness.py::_awareness_id` uses `awareness:` while `_item_id` uses `awareness-item:`; `awareness drill` accepts item IDs; amendment `0027` directs one canonical awareness-owned `awareness:` form.
  Required action: Bring awareness revision and item identifiers under the canonical `awareness:` namespace and strengthen the gate to reject alternate awareness-owned prefixes.

## Boundary Checks

- Confirmed: the Acceptance Auditor's disagreement is material and approval-relevant.
- Confirmed: current HEAD differs from the audit's reviewed commit only by adding the acceptance audit file.
- Confirmed: T0-T3 remain parked; the identified defects are bounded T4 acceptance gaps.
- Confirmed: P4 remains uncredited and T5 has not begun.

## Evidence Checked

- Compared `.builder/evidence/acceptance/T4/20260827T140828Z-acceptance-audit.md` with `.builder/evidence/reviews/T4/20260827T133309Z-external-review.md`.
- Inspected `.builder/BCC.md`, `.builder/TRANCHE_PROTOCOL.md`, `.builder/TRANCHE_PLAN.md`, `.builder/CURRENT_STATE.md`, `docs/PRODUCT_CHARTER.md`, `docs/ARCHITECTURE.md`, and T4 journals `0026`-`0031`.
- Inspected `product/core/awareness.py`, `product/core/substrate.py`, `tests/test_t4_awareness.py`, and `.builder/gates/t4_awareness.py`.
- Ran `git rev-parse HEAD`: `a8dba976227a21aaca8cc1ba09c4313fe91f7ade`.
- Ran `git status --short --branch`: clean before this follow-up review file.
- Ran `git diff --name-status f7e58ea3f9f12e5e5109151474dd4527a939095c..HEAD`: only the acceptance audit file was added.

## Discrimination Review

- Plausible wrong implementation: observed awareness can satisfy structural tests while omitting required limitations. Current tests do not reject this.
- Plausible wrong implementation: awareness can emit provenance-looking handles that cannot resolve through their owning layer. Current tests do not enumerate all emitted handle prefixes.
- Plausible wrong implementation: the gate can reject `revision:` while still allowing another noncanonical awareness-owned prefix, `awareness-item:`.

## Residual Risk

- No broader T4 redesign risk identified.
- No parked prior-tranche reopen risk identified.

## Suggested Operator Action

Return T4 to VERIFYING for the bounded repairs identified by the Acceptance Auditor. Treat this follow-up as a material correction to the prior Reviewer `APPROVE CANDIDATE` disposition; do not park T4, credit P4, or begin T5 until the repaired candidate is resubmitted and reviewed.
