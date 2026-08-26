# Builder Constraint Contract

Status: **APPROVED CONSTRUCTION AUTHORITY**

This contract owns builder behavior and general construction grammar. It does not own
product architecture, product acceptance facts, tranche sequence, or implementation
status.

## Authority map

| Fact class | One owner |
|---|---|
| Builder behavior, workflow grammar, root discipline | `.builder/BCC.md` |
| Product identity, invariants, P1-P8, product STOP | `docs/PRODUCT_CHARTER.md` |
| Repository tranche mechanics and transitions | `.builder/TRANCHE_PROTOCOL.md` |
| Sequence, status ledger, project closure | `.builder/TRANCHE_PLAN.md` |
| Approved implementation shape | `docs/ARCHITECTURE.md` |
| Current resumability summary | `.builder/CURRENT_STATE.md` (projection only) |
| Construction history | `.builder/journal/` |
| Mechanical closure evidence | `.builder/evidence/` |
| Tranche and closure gate implementation | `.builder/gates/` |
| Product behavior tests and fixtures | `tests/` |

An authority may reference another owner's identifiers but may not restate or silently
redefine their facts. Evidence proves claims; it does not become policy. Current State
orients; it does not become authority.

## Roots and boundaries

Writes are confined to this project root unless the operator explicitly names another
target. Parent/reference projects are read-only prior art and never runtime dependencies.
No parent state, history, identity, evidence, paths, or lineage enters product material.

`.builder/`, `tests/`, repository metadata, generated evidence, and construction output
never ship. `product/` is runtime source. `factory/` is manufacture/install/package/
release only. Product code must never import factory code. Release assembly is positive.

The pre-bootstrap baseline commit is historical provenance only. Its implementation is
PROVISIONAL until a declared tranche audits and proves it.

## Construction grammar

Use this ownership hierarchy only where a real owner exists:

```text
composition root -> orchestrator -> domain manager -> component or machine
```

The composition root wires. The orchestrator coordinates domains. A manager owns one
coherent policy domain. A component is small and cohesive. A machine owns meaningful
state transitions. Do not create ceremonial managers, empty layers, or machines around
helper functions. Adapters contain protocol translation, never private domain behavior.

## Tranche discipline

One tranche produces one observable product or construction property. Before substantive
implementation, declare outcome, scope, non-goals, changed surfaces, risks, completion
evidence, and ordered plan in a new journal entry. Measure the current source rather than
trusting remembered status.

During execution, work incrementally against the declared evidence. Verify risky
assumptions early. Keep discoveries separate: fix tranche-blocking issues and record
unrelated work for later instead of absorbing it.

Before review, perform a consolidation pass over correctness, failure paths, containment,
stale assumptions, duplicated ownership, dead code, coupling, debris, naming, and
readability. Run focused checks, the tranche gate, cumulative tests appropriate to risk,
the real consumer entrance where relevant, and one discovery activity capable of finding
an unplanned defect.

Submit completed work as AWAITING_APPROVAL and stop. The builder may not grant PARKED
status or begin the next tranche. Review defects return to the same tranche rather than
creating a cosmetic new tranche.

After operator approval only: reconcile authoritative documentation, record approval and
final evidence, update Current State, apply the operator-granted terminal state, and state
the next tranche synopsis without implementing it.

## Evidence discipline

Gate-first is preferred where an observable condition can be declared before code.
Consumer entrances outrank direct internal imports for consumer claims. Assertions must
discriminate against plausible wrong implementations using known answers, adversarial
inputs, mutation, failure injection, or independent measurement where practical.

No exception, exit zero, an empty list, or a stored value reading back is sufficient by
itself. A tool's report of its own mutation is not measurement. Missing evidence is
UNSCORED or UNKNOWN, never PASS. Verification cost scales with risk; cumulative
certification belongs at meaningful boundaries.

`.builder/gates/` is the only gate authority. `tests/` may supply product tests and
fixtures to a gate but never owns tranche closure logic. The canonical product-test
entrance is `python -m pytest`.

## Journal and state discipline

Construction journal entries are chronological, self-contained, and immutable after
creation. Corrections, amendments, reopens, supersessions, and approvals are new entries.
Never rewrite history to match later belief. Entries record what was believed, attempted,
changed, why, evidence, decisions, failures, and next action without duplicating authority
documents.

The construction journal and installed product journal are unrelated stores with distinct
subjects and lifecycles. Current State is a replaceable projection assembled from the
Plan, journal, evidence, and measured source.

## Closure and restraint

The builder cannot self-certify terminal disposition. Reopening requires evidence of
correctness, safety, security, architecture, usability, or maintainability debt sufficient
to invalidate or materially weaken an accepted claim. Low-value polish does not reopen
closed work. Product STOP and project closure are separate and owned by their declared
authorities.
