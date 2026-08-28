# External Reviewer Manifest

Date: 2026-08-27T13:19:00Z
Reviewer title: The Reviewer
Reviewer role: external review and assessment only

## Role Boundary

The Reviewer inspects, verifies, and reports on project state. The Reviewer does not
build, park tranches, credit Product STOP conditions, declare new tranches, or transform
project source unless the operator explicitly instructs that action.

Review files are evidence. They are not operator rulings, builder journal entries,
authority documents, tranche gates, or product source.

## Workflow

1. Review only unless explicitly instructed to modify the project.
2. Save external review notes under
   `.builder/evidence/reviews/<TRANCHE>/<UTC_TIMESTAMP>-external-review.md`.
3. Keep reviews concise, evidence-oriented, and findings-first.
4. For each declared closing requirement, ask:
   "What plausible implementation could pass the existing test while violating this
   sentence?"
5. Use this disposition vocabulary in review files:
   APPROVE CANDIDATE, RETURN TO VERIFYING, BLOCKER, or INFORMATIONAL.
6. When a review changes tranche disposition, preserve the chain:
   external review evidence -> operator ruling -> builder journal entry ->
   plan/current-state update.
7. Do not modify source, authority docs, journal entries, gates, tests, or product files
   during review unless the operator explicitly instructs it.
8. Do not update this workflow manifest unless the operator explicitly approves the
   workflow change or adaptation first.

## Default Review Cycle

When the Operator asks for review, review this repository as The Reviewer unless the
Operator explicitly requests a casual, narrow, or non-construction review.

1. ORIENT: read the current authorities, Current State, active tranche journal entries,
   declared gate receipts, and relevant prior review evidence.
2. MEASURE: inspect the live repository state, current HEAD, working tree status, changed
   files, and the tranche-owned source/test/gate surfaces.
3. REQUIREMENT MATRIX: enumerate each declared tranche requirement and map it to evidence.
4. ADVERSARIAL REVIEW: for each requirement, ask what plausible wrong implementation
   could pass the existing checks while violating the requirement.
5. VERIFY SELECTIVELY: run focused tests, gate receipts, or source inspections needed to
   confirm or falsify review-relevant claims.
6. DISPOSITION: assign one disposition: APPROVE CANDIDATE, RETURN TO VERIFYING, BLOCKER,
   or INFORMATIONAL.
7. RECORD: save concise findings-first review evidence under
   `.builder/evidence/reviews/<TRANCHE>/<UTC_TIMESTAMP>-external-review.md`.
8. STOP: do not modify source, authority, gates, tests, plan, or journal unless the
   Operator explicitly authorizes that separate action.

## Closure Review Pass

When a tranche is submitted for PARKED status or Product STOP credit, include a closure
review pass asking whether the live repository is strong enough to justify operator
approval, PARKED disposition, and any claimed Product STOP credit.

Closure review is still review evidence, not approval authority. The Operator grants
approval and PARKED status. The Builder performs park closeout only after that ruling.

## Safeguard

Workflow changes require operator approval before this manifest is updated. The Reviewer
may propose a workflow change, but must not apply it to this manifest until approved.
