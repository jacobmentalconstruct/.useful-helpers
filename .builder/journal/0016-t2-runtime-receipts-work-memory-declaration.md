# T2 Runtime Receipts and Work Memory Declaration

- Date: 2026-08-26
- Tranche: T2 Runtime Receipts + Work Memory
- Entry class: tranche declaration
- Transition: PROVISIONAL -> DECLARED
- Preconditions: T0 PARKED; T1 PARKED in `0015-t1-park.md`
- Implementation authorized by this entry: no
- T2 outcome PARKED: no

## Declared outcome

Previewed runtime work is reconstructable through distinct durable operational receipts
and runtime evidence while a blank-start App Journal records project/work memory without
collapsing into construction history, receipts, epistemic substrate, or awareness.

## Current measured state

The live product has a SQLite bootstrap with only the `instances` table and schema
version 1. `ControlPlane.invoke()` returns transient envelopes for tool calls but does
not persist call attempts, authority decisions, result validation, process failure, or
duration. The installed CLI exposes `status`, `tools`, and `call` only.

The current `write_file` tool performs immediate apply when authority and confirmation
are present. It has no reviewed preview object, no approval token, no stale-state guard,
no independent before/after measurement, and no durable operation record. Existing tests
prove that the current mutation route is singular and contained, but not receipt-bearing.

No runtime App Journal table, command, export, or entry semantics exist. The construction
journal under `.builder/journal/` is unrelated and must not ship or seed runtime project
memory.

## Scope

T2 will add the smallest runtime memory layer that makes the existing governed host
receipt-bearing:

- operational receipt/event tables for tool invocations, authority refusals, validation
  refusals, process results, previews, applies, changed-path measurements, and
  verification absence/results;
- immutable runtime evidence blobs or rows sufficient to reconstruct reviewed previews,
  diffs, tool envelopes, and measured mutation facts;
- a blank-start App Journal owner with explicit entry/decision/backlog semantics and CLI
  access;
- preview-first apply behavior for the existing `write_file` capability, including
  approval bound to the reviewed preview state and stale-preview refusal;
- independent changed-path measurement around apply, not trusting the mutating tool's
  self-report;
- honest verification reporting that records target-native verification when available
  and records unavailable verification as unavailable, not PASS; and
- updated tests, architecture notes, and one T2 gate under `.builder/gates/`.

## Non-goals

T2 does not implement the full epistemic project substrate: no resource inventory
persistence beyond mutation/receipt needs, no observations table as canonical project
map, no derived claims, no awareness revisions, no semantic/vector index, and no domain
cartridges.

T2 does not add MCP, GUI, autonomous agents, local AI, release packaging, updater UX,
new broad tool families, or standalone App Journal/tool-pack extraction. It may add
minimal CLI commands for receipts, evidence, journal, preview, apply, and verification
only where needed to prove the declared product behavior through a real entrance.

T2 does not make construction journal entries part of runtime state. `.builder/` remains
construction-only and excluded from shipped runtime.

## Changed surfaces expected

- `product/core/storage.py`: schema migration for receipt, evidence, journal, preview,
  mutation, and verification records.
- `product/core/control.py`: durable event recording, preview/apply coordination,
  mutation measurement, and verification reporting around governed invocation.
- `product/core/cli.py` and `product/bin/sidecar.py`: consumer entrance for the new
  receipt, evidence, App Journal, preview/apply, and verification operations.
- `product/core/*`: small cohesive modules only if needed to keep receipts, journal, or
  mutation workflow from becoming hidden behavior inside CLI code.
- `product/tools/write_file/*`: manifest or operation changes only if the existing
  apply contract must split into preview/apply mechanics without violating T1's
  dependency boundary.
- `tests/`: product fixtures proving durable runtime memory and governed mutation.
- `.builder/gates/t2_runtime_receipts_work_memory.py`: sole T2 closure gate.
- `docs/ARCHITECTURE.md`, `.builder/TRANCHE_PLAN.md`, `.builder/CURRENT_STATE.md`, and
  later T2 journal entries: review synchronization only.

## Completion evidence declared before implementation

The eventual T2 gate must prove the following through product tests, structural checks,
and consumer CLI exercises:

1. A fresh attach creates blank runtime receipt/evidence/App Journal state and does not
   import construction journal history.
2. Every CLI `call` attempt crosses the same host and leaves a durable operational
   receipt for success and for refusals before child launch.
3. Runtime receipts, runtime evidence, and App Journal entries are stored as distinct
   record classes with separate owners and identifiers.
4. An App Journal entry can be created, read after process restart, linked to operation
   or evidence identifiers, and exported or listed without requiring awareness or MCP.
5. The existing write-file mutation becomes preview-first: apply is refused without a
   matching reviewed preview approval.
6. Approval is bound to the reviewed state and a stale preview is refused after the
   target file changes.
7. Apply records independently measured changed paths and before/after facts rather than
   relying only on the tool result.
8. Verification records target-native command output when a declared command exists and
   records `unavailable` honestly when none exists.
9. Runtime state survives restart/re-entry and compatible replacement of product code in
   the installed `.sidecar` while preserving instance identity and prior receipts/journal
   rows.
10. Deleting `.sidecar` removes runtime receipts, evidence, and App Journal state while
    approved target work products remain.
11. The T1 mechanical dependency boundary remains intact: `product/tools/*` may import
    `core.tool_runtime` but no other `core.*`, and `core.tool_runtime` imports no higher
    Sidecar `core.*`.
12. Canonical pytest, Ruff, the T2 gate, and relevant cumulative T0/T1 boundary checks
    pass from the committed review candidate.

The gate must include at least one discriminating mutation or failure-injection witness
showing that a plausible wrong implementation, such as self-reported mutation without
independent measurement or journal/receipt table collapse, fails for the intended reason.

## Ordered implementation plan

1. Add focused failing product tests for blank runtime state, receipt persistence,
   distinct App Journal records, preview/apply refusal, stale-preview refusal, measured
   mutation, verification unavailable, and restart/re-entry.
2. Extend storage with minimal migrations and typed identifiers for receipts, runtime
   evidence, App Journal entries, previews, mutations, changed paths, and verifications.
3. Add small runtime owners for receipts/evidence and App Journal if storage/control
   would otherwise absorb their semantics.
4. Route `ControlPlane.invoke()` events through the receipt owner for success and refusal
   paths without bypassing the T1 host boundary.
5. Implement preview-first write-file flow and approval binding in the host, preserving
   mechanical-tool separability.
6. Add independent before/after measurement and honest verification recording.
7. Expose the minimal CLI commands needed for receipts, evidence, App Journal,
   preview/apply, and verification.
8. Implement the T2 gate and its discrimination witness.
9. Consolidate for correctness, containment, stale-state behavior, schema durability,
   naming, debris, dependency direction, and ownership separation.
10. Run canonical pytest, Ruff, T2 gate, relevant T0/T1 checks, and one discovery search
    for authority/state terminology collapse.
11. Synchronize review documentation and submit T2 AWAITING_APPROVAL without parking T2
    or beginning T3.

## Risks and decisions held for implementation evidence

- Schema versioning may need to move beyond the current one-step migration. T2 should
  keep migration mechanics minimal while preserving installed-state compatibility.
- Preview/apply may require either a host-level synthetic operation or a small adjustment
  to the write tool contract. The host must remain the owner of approval, staleness, and
  measurement.
- Verification discovery should be conservative. If no target-native verification signal
  is declared or safely detected, the correct result is `unavailable`, not PASS.
- The App Journal should be useful but small. It should not become a second event log or
  a premature project-management system.
- Runtime evidence in T2 should support receipts and preview reconstruction, not the full
  T3 epistemic evidence graph.

## Review position

This declaration is submitted for operator review. T2 is DECLARED, not IMPLEMENTING. No
product source, product tests, manifests, T2 gate, or runtime schema has been changed by
this entry. Implementation must wait for explicit operator approval of this declaration.
