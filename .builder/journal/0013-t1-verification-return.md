# T1 Verification Return

- Date: 2026-08-26
- Tranche: T1 Mechanical Hands + Governed Host
- Entry class: operator review return
- Transition: AWAITING_APPROVAL -> VERIFYING
- Returned submission: `0011-t1-awaiting-approval.md`
- Prior review amendment: `0012-t1-review-document-amendment.md`
- Product scope changed: no

## Operator finding

The implementation and submitted review are accepted in principle, but the
`mechanical_dependency_direction` closure assertion encodes the lower-layer boundary as
a blacklist. Unlisted host-owned modules such as `core.containment` and `core.contracts`
could therefore be imported by mechanical code without failing the T1 gate.

## Bounded correction

The T1 gate will encode the positive invariant established by the tranche:

- `product/tools/*` may import `core.tool_runtime`, but no other `core.*` subsystem; and
- `product/core/tool_runtime.py` may import no higher Sidecar `core.*` subsystem.

Ordinary standard-library and tool-local/declarable mechanical dependencies remain
outside this narrow assertion. The assertion will be mutation-tested with
`core.containment`, `core.contracts`, and `core.instance`. No T1 product behavior,
manifest, runtime context, tool, or product test scope changes.

After repair and mutation evidence, the complete T1 review candidate will be committed,
the T1 gate will run from that clean commit, and the current T0 gate will run once because
entry `0012` changed its live implementation. A later immutable amendment will cite both
new receipts and return T1 to AWAITING_APPROVAL without beginning T2.

