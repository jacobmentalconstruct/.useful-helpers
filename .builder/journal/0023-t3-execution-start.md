# T3 Epistemic Substrate Execution Start

- Date: 2026-08-27
- Tranche: T3 Epistemic Substrate
- Entry class: execution start
- Transition: DECLARED -> IMPLEMENTING
- Approved declaration: `0022-t3-epistemic-substrate-declaration.md`
- T3 outcome PARKED: no
- T4 started: no

## Operator direction

The operator approved the T3 declaration and directed implementation under the existing
BCC/Tranche Protocol. T3 must follow the declared gate-first evidence plan, preserve the
T0-T2 boundaries, stop at AWAITING_APPROVAL, and must not begin T4 or claim full P3
credit without operator review.

## Remeasured starting point

The repository started on branch `codex/t1-mechanical-host` at commit `5a0ea4f`, with
T0, T1, and T2 parked. The tracked tree was clean; `_projectmapper/` remained ignored
transient file-dump output from the prior operator ruling.

The parked T2 runtime storage is schema version 2 and creates only `instances`,
`operational_artifacts`, `operation_receipts`, `app_journal_entries`, and
`app_journal_links`. Persistent T3 tables such as `resources`, `resource_versions`,
`observations`, `epistemic_evidence`, `claims`, `relations`, and
`awareness_revisions` are absent. Existing resource records are transient inventory tool
output, not durable substrate state.

## Execution boundaries

T3 will implement only the declared epistemic substrate: durable resources, immutable
resource versions, deterministic observations, content-addressed epistemic evidence,
thin derived claims, and typed provenance relations. It will expose minimal CLI refresh
and inspection commands, preserve T2 receipts/App Journal ownership, and keep awareness,
MCP, mutation governance, domain cartridges, embeddings, release lifecycle, and T4 out of
scope.

## Initial implementation order

1. Add focused failing product tests for blank substrate state, empty and non-empty
   refresh, version history, evidence/claim provenance, trace traversal, and T2
   separation.
2. Add schema version 3 with distinct T3 tables owned semantically by a new substrate
   module.
3. Implement content-addressed evidence, resource/version/observation/claim/relation
   persistence, explicit refresh, and trace traversal.
4. Add minimal CLI access for substrate refresh and inspection.
5. Add the T3 gate and discrimination witness.
6. Consolidate, verify, synchronize review documentation, and submit T3 for operator
   approval without parking it or beginning T4.
