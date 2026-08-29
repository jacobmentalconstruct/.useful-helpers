# 0037 - T5 execution start

Date: 2026-08-29

Status transition: T5 Governed Mutation Loop DECLARED -> IMPLEMENTING.

## Operator approval

The operator approved the T5 declaration in entry `0036` and directed the builder to
enter IMPLEMENTING under that declaration.

## Re-orientation

Before this transition the builder re-read the required authority and handoff surfaces:
`.builder/BCC.md`, `.builder/TRANCHE_PROTOCOL.md`, `.builder/TRANCHE_PLAN.md`,
`.builder/CURRENT_STATE.md`, `docs/PRODUCT_CHARTER.md`, `docs/ARCHITECTURE.md`,
`.builder/ROLE_ONBOARDING.md`, `.builder/evidence/builder/BUILDER_MANIFEST.md`,
`0035-t4-park.md`, and `0036-t5-governed-mutation-loop-declaration.md`.

T0-T4 remain PARKED. P1-P4 remain credited. Product STOP remains incomplete because
P5-P8 are UNSCORED.

## Implementation boundary

T5 implementation is limited to entry `0036`: migration-version-stamp repair, governed
mutation preview/approval/apply/measurement/verification/refresh/linking for one bounded
`write_file` path, minimal child-process environment containment, focused tests, the T5
gate, cumulative verification, and review synchronization.

This entry does not park T5, grant P5 credit, begin T6, or change the parked status of
T0-T4.

## Next action

Begin with the migration-version-stamp repair and its forward-migration/interruption
fixture before adding any T5 schema bump or mutation-governance storage.
