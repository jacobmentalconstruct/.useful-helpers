# T2 Declaration Scope Amendment

- Date: 2026-08-26
- Tranche: T2 Runtime Receipts + Work Memory
- Entry class: operator-returned declaration amendment
- Transition: DECLARED -> DECLARED
- Amends declaration: `0016-t2-runtime-receipts-work-memory-declaration.md`
- Implementation authorized by this entry: no
- T2 outcome PARKED: no

## Operator finding

The original T2 declaration correctly identified distinct durable operational receipts,
operational artifacts, and blank-start App Journal/work memory as the tranche center.
It also correctly preserved separation from construction history, T3 epistemic
substrate, T4 awareness, and the T1 mechanical boundary.

However, it absorbed later coherent outcomes into T2: preview-first mutation, reviewed
approval binding, stale-preview refusal, independent changed-path measurement as part of
a reviewed apply loop, target-native verification discovery/execution, compatible
product replacement/update proof, and sidecar deletion/removal proof.

## Amended declared outcome

T2 will establish durable runtime history for governed calls after a trustworthy
installed instance and state owner have been resolved, plus a blank-start App Journal for
deliberate project/work memory. Operational receipts answer what happened. App Journal
entries answer what mattered or was decided. Operational artifacts substantiate runtime
operation facts. None of these becomes construction history, T3 epistemic evidence, T4
awareness, or a reviewed mutation workflow.

## Amended T2 scope

T2 is narrowed to:

- durable operation identity and receipts for governed calls after valid runtime state
  ownership is resolved;
- truthful success, refusal, failure, and process-result recording;
- operational artifacts sufficient to substantiate receipt facts;
- blank-start App Journal records with deliberate entry, decision, backlog, and status
  semantics;
- optional journal links to receipt or artifact identifiers without automatically
  projecting receipts into journal entries;
- persistence across process restart and re-entry;
- minimal schema migration;
- real CLI consumer access sufficient to inspect and use receipts and App Journal;
- preservation of T1's mechanical dependency boundary; and
- discriminating verification and discovery.

T2 may record facts produced by the current mutation route. It must not redesign that
route merely to make receipts possible.

## Deferred outcomes preserved

The removed requirements remain in the finite outcome graph:

- preview-first mutation, approval bound to reviewed state, stale-preview refusal,
  independently measured changed paths, target-native verification, honest unavailable
  verification, and refresh after mutation move to the later Governed Mutation Loop
  tranche;
- compatible product replacement/update proof and sidecar deletion/removal proof remain
  lifecycle/release acceptance for the final release tranche.

These requirements are deferred, not deleted.

## Amended non-goals

T2 does not implement preview-first mutation, reviewed-preview approval, stale-preview
refusal, independent changed-path measurement as a governed apply-loop outcome,
target-native verification discovery/execution, compatible product update proof, or
sidecar removal proof.

T2 does not implement the full epistemic project substrate: no canonical target
resources, observations, derived claims, provenance graph, awareness revisions,
semantic/vector index, or domain cartridges.

T2 does not add MCP, GUI, autonomous agents, local AI, release packaging, updater UX,
new broad tool families, or standalone App Journal/tool-pack extraction. It may add
minimal CLI commands for receipts, operational artifacts, App Journal entries, and
journal links only where needed to prove the declared product behavior through a real
entrance.

## Amended completion evidence

The eventual T2 gate must prove the following through product tests, structural checks,
and consumer CLI exercises:

1. A fresh attach creates blank runtime receipt, operational artifact, and App Journal
   state and does not import construction journal history.
2. Governed calls for which a trustworthy installed instance and state owner have been
   resolved leave durable operational receipts for success and for host refusals or
   failures occurring after that point.
3. A pre-instance or untrusted-state failure is explicit and does not create a global
   sidecar-external receipt store solely to preserve an event.
4. Runtime receipts, operational artifacts, and App Journal entries are stored as
   distinct record classes with separate owners and identifiers.
5. An App Journal entry can be created, read after process restart, assigned a status or
   backlog/decision meaning, linked to receipt or artifact identifiers, and listed
   without requiring awareness or MCP.
6. Receipts do not automatically become App Journal entries, and App Journal entries can
   exist without being reducible to one tool call.
7. Successful read, governance refusal before child launch, malformed child result, tool
   process failure, and successful current-route mutation are recorded truthfully when
   they occur after state ownership is resolved.
8. A state-changing operation must not silently proceed or be reported as durably
   governed when its required durable operation record cannot be established. Receipt
   persistence failure must be explicit and testable.
9. Runtime receipts, operational artifacts, App Journal records, and links persist across
   process restart and re-entry.
10. Operational artifacts/evidence are clearly scoped as evidence of runtime operations,
    not the later epistemic evidence owner for target observations or claims.
11. The T1 mechanical dependency boundary remains intact: `product/tools/*` may import
    `core.tool_runtime` but no other `core.*`, and `core.tool_runtime` imports no higher
    Sidecar `core.*`.
12. Canonical pytest, Ruff, the T2 gate, and relevant cumulative T0/T1 boundary checks
    pass from the committed review candidate.

The gate must include at least one discriminating mutation or failure-injection witness
showing that a plausible wrong implementation, such as journal/receipt table collapse,
automatic receipt-to-journal projection, or silent state-changing execution after
receipt persistence failure, fails for the intended reason.

## Amended ordered implementation plan

1. Add focused failing product tests for blank runtime state, receipt persistence,
   operational artifact persistence, App Journal entry/link/status semantics,
   receipt/journal separation, receipt persistence failure, and restart/re-entry.
2. Extend storage with minimal migrations and typed identifiers for receipts,
   operational artifacts, App Journal entries, and journal links.
3. Add small runtime owners for receipts/artifacts and App Journal if storage/control
   would otherwise absorb their semantics.
4. Route host events through the receipt owner only after installed instance and state
   ownership are trustworthy, recording success, refusal, malformed output, process
   failure, and existing mutation-route results without bypassing the T1 boundary.
5. Ensure state-changing operations fail explicitly before child launch or before target
   mutation when required receipt creation cannot be established.
6. Expose minimal CLI commands to list/read receipts, list/read artifacts, create/list
   App Journal entries, and create/list journal links.
7. Implement the T2 gate and its discrimination witness.
8. Consolidate for correctness, containment, schema durability, failure semantics,
   naming, debris, dependency direction, and ownership separation.
9. Run canonical pytest, Ruff, T2 gate, relevant T0/T1 checks, and one discovery search
   for authority/state terminology collapse.
10. Synchronize review documentation and submit T2 AWAITING_APPROVAL without parking T2
    or beginning T3.

## Review position

This amendment is submitted for operator review with T2 still DECLARED, not
IMPLEMENTING. It narrows and corrects the declaration before implementation. No product
source, product tests, manifests, T2 gate, or runtime schema has been changed.
