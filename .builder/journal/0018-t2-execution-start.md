# T2 Runtime Receipts and Work Memory Execution Start

- Date: 2026-08-26
- Tranche: T2 Runtime Receipts + Work Memory
- Entry class: execution start
- Transition: DECLARED -> IMPLEMENTING
- Approved declaration: `0016-t2-runtime-receipts-work-memory-declaration.md`
- Approved amendment: `0017-t2-declaration-scope-amendment.md`
- Product outcome PARKED: no
- T3 started: no

## Operator direction

The operator approved the amended T2 declaration and directed execution under the full
BCC protocol. T2 must re-orient, remeasure, follow the amended gate-first evidence plan,
consolidate, perform discriminating verification and discovery, synchronize review state,
and stop at AWAITING_APPROVAL. The builder must not park T2 or begin T3 without explicit
operator approval.

## Remeasured starting point

The repository was clean on branch `codex/t1-mechanical-host` at the start of execution.
Canonical pytest passed 15 tests. Ruff passed. The live product still has no durable
runtime receipt owner, no operational artifact owner, and no runtime App Journal owner.
SQLite storage still contains only the `instances` table at schema version 1. The CLI
still exposes `status`, `tools`, and `call`.

## Execution boundaries

T2 will implement only the amended scope from `0017`: durable operation receipts and
operational artifacts after trusted installed state ownership is resolved, blank-start
App Journal/work memory, minimal CLI access, restart/re-entry persistence, explicit
receipt persistence failure semantics, and preservation of T1's dependency boundary.

T2 will not implement preview-first mutation, reviewed approval, stale-preview refusal,
governed apply-loop changed-path measurement, target-native verification workflow,
compatible update proof, sidecar removal proof, T3 epistemic substrate, T4 awareness,
MCP, GUI, release packaging, or T3.

## Initial execution order

1. Add failing product tests that express the amended T2 evidence plan.
2. Implement minimal schema migration and runtime owners for receipts/artifacts and App
   Journal records.
3. Route host events through the receipt owner after trusted state ownership is resolved.
4. Add CLI inspection/creation commands for receipts, artifacts, App Journal entries,
   and links.
5. Add the T2 gate and discrimination witness.
6. Consolidate, verify, synchronize review documentation, and submit T2 for operator
   approval without parking it.
