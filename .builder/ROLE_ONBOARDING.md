# Role Onboarding

Status: construction handoff index only. This is not authority, product source, a gate,
or a journal entry. If this file conflicts with the BCC, Protocol, Plan, Charter,
Architecture, or an operator ruling, those authorities win.

Use this file when a new or replacement agent enters the project.

## First Question

Identify your role before acting:

- **Operator:** human decision authority.
- **Builder:** implements approved construction work and submits it for review.
- **Reviewer:** performs broad external review and assessment.
- **Acceptance Auditor:** audits whether tranche closure/PARK/Product STOP credit is
  justified.

Only the Operator approves, parks, credits Product STOP, reopens, or changes scope.

## Required Read Order

All incoming agents should read:

1. `.builder/BCC.md`
2. `.builder/TRANCHE_PROTOCOL.md`
3. `.builder/TRANCHE_PLAN.md`
4. `.builder/CURRENT_STATE.md`
5. `docs/PRODUCT_CHARTER.md`
6. `docs/ARCHITECTURE.md`

Then read the role-specific manifest:

- Builder: `.builder/evidence/builder/BUILDER_MANIFEST.md`
- Reviewer: `.builder/evidence/reviews/REVIEWER_MANIFEST.md`
- Acceptance Auditor:
  `.builder/evidence/acceptance/ACCEPTANCE_AUDITOR_MANIFEST.md`

Then read the latest relevant journal entries and evidence named by `CURRENT_STATE.md`.

## Current Handoff Rule

Measure the live repository before acting. Chat memory, summaries, reports, tests, gates,
and documentation are useful context, but live state and authoritative surfaces determine
what may happen next.

At the time this index was created, the current work was T4 Awareness. T4 was not parked,
P4 was not credited, and T5 had not begun. `CURRENT_STATE.md` owns the current projection;
read it for the latest position.

## Role Flow

1. Builder submits tranche work at `AWAITING_APPROVAL`.
2. Reviewer records broad review evidence under `.builder/evidence/reviews/`.
3. Acceptance Auditor records closure audit evidence under `.builder/evidence/acceptance/`.
4. Operator issues the actual ruling.
5. Builder acts on the ruling and stops at the required boundary.

## Do Not

- Do not treat this onboarding file as authority.
- Do not modify files outside your role.
- Do not park, credit Product STOP, reopen, or begin the next tranche without explicit
  operator direction.
- Do not save construction review/audit material in the product App Journal.
- Do not collapse construction history, Reviewer evidence, Acceptance Auditor evidence,
  runtime receipts, App Journal memory, epistemic evidence, or awareness.
