# 0032 - T4 acceptance review return

Date: 2026-08-27

Status transition: none. T4 Awareness remains under review pending operator ruling.

## Review evidence received

After entry `0031` submitted the repaired T4 implementation for operator review, the
Acceptance Auditor and Reviewer produced additional review evidence:

- Acceptance audit:
  `.builder/evidence/acceptance/T4/20260827T140828Z-acceptance-audit.md`
- Reviewer follow-up:
  `.builder/evidence/reviews/T4/20260827T141302Z-external-review.md`

The acceptance audit recommends `RETURN TO VERIFYING - BOUNDED REPAIR`. The Reviewer
follow-up accepts that correction and changes the earlier Reviewer disposition from
`APPROVE CANDIDATE` to `RETURN TO VERIFYING`.

## Findings to repair before T4 can park

The review evidence identifies three bounded T4 acceptance gaps:

1. Observed awareness revisions can report empty limitations even though T4 requires
   explicit limitations for observed thin/non-empty awareness.
2. T4 can emit `relation:` provenance handles that do not round-trip through a T3-owned
   resolver.
3. Public awareness item identifiers use `awareness-item:` as a second awareness-owned
   handle form despite the amended T4 preference for one canonical `awareness:` form.

These findings concern T4 projection behavior and acceptance evidence. They do not
invalidate parked T0-T3 outcomes.

## Current position

T4 is not parked. P4 is not credited. T5 has not begun.

The next operator decision is whether to return T4 to VERIFYING for the bounded repairs
above. If returned, repair only those findings, strengthen focused tests and the T4 gate
for the missing witnesses, rerun the declared T4 and cumulative checks, and resubmit T4
for review.
