# 0033 - T4 acceptance repair start

Date: 2026-08-28

Status transition: T4 Awareness AWAITING_APPROVAL -> VERIFYING.

## Operator ruling

The operator approved continuing from entry `0032` by returning T4 to bounded VERIFYING.
This is not approval to park T4, grant P4 credit, begin T5, or reopen T0-T3.

## Bounded repair scope

Repair only the three T4 acceptance findings recorded in entry `0032`:

1. Observed awareness revisions must emit explicit truthful limitations.
2. Every emitted T3 provenance/source handle must round-trip through a T3-owned resolver
   or be removed from the public projection contract.
3. Awareness-owned public identifiers must use one canonical `awareness:` handle
   namespace, not a second `awareness-item:` prefix.

## Evidence plan

Strengthen focused T4 tests and the T4 gate so they fail for the three defects above.
Then rerun focused T4 tests, canonical pytest, Ruff, the T4 gate, and cumulative lower
gates needed for review. Resubmit T4 at AWAITING_APPROVAL if the bounded repair passes.
