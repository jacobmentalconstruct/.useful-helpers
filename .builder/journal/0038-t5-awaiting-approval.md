# 0038 - T5 Governed Mutation Loop Awaiting Approval

Entry type: awaiting approval
Tranche: T5 Governed Mutation Loop
Status: AWAITING_APPROVAL
Date: 2026-08-29

## Operator direction

The operator approved declaration entry `0036` and directed implementation under the full
BCC protocol. T0-T4 remain PARKED, P1-P4 remain credited, Product STOP remains
incomplete, and T5 must stop at AWAITING_APPROVAL without parking, granting P5 credit, or
beginning T6.

## Declared outcome

T5's declared outcome is the minimal governed mutation loop: current awareness, reviewed
preview, approval bound to that preview and basis, stale-state refusal, bounded mutation
through the existing governed host, independent changed-path measurement, honest
verification, substrate refresh, awareness refresh, and linked durable records.

## What changed

The migration-version-stamp defect was repaired before the schema bump. Storage now
supports schema version 5 and adds mutation-owned tables for previews, approvals,
mutation records, verifications, and mutation links.

`product/core/mutation.py` now owns the T5 mutation loop. It previews one bounded
`write_file` path without applying it, binds approval to the preview digest and T3/T4
basis, refuses stale or mismatched apply attempts before child launch, routes approved
apply through the existing `ControlPlane`, measures changed paths independently from
target snapshots, records honest unavailable verification when no target-native verifier
exists, refreshes T3 substrate and then T4 awareness after successful apply, and links
the resulting records without moving ownership out of receipts, App Journal, substrate,
or awareness.

The CLI now exposes `mutation status`, `mutation preview-write`, `mutation approve`,
`mutation apply`, `mutation history`, and `mutation links`. Child-process environment
containment was narrowed to the governed host boundary: mechanical tools receive the
runtime import path they need, while ambient Sidecar identity or operator-secret
environment values are not inherited.

## Scope held

The mutation surface is intentionally limited to a reviewed `write_file` path. T5 did not
implement MCP, GUI, local AI, embeddings, domain cartridges, release/update/removal,
rollback, a workflow engine, autonomous planning, broad software-project assumptions, or
construction-role runtime concepts.

T5 records honest verification absence; it does not create a target-native verifier or
claim PASS when none exists. P5 is a review candidate only until operator approval.

## Verification evidence

Focused T5 tests pass and exercise migration stamping, blank mutation state,
preview-without-apply, approval binding, stale refusal before child launch, successful
apply through the governed host, independent changed-path measurement, honest
verification absence, substrate/awareness refresh, child environment containment, and
non-software target behavior.

Canonical pytest passed. Ruff passed. `git diff --check` passed.

Authoritative T5 gate:

- Run: `20260829T095546Z-e30c36d7`
- Receipt: `.builder/evidence/T5/20260829T095546Z-e30c36d7/t5-gate.json`
- Status: PASS 13/13
- Head commit: `62e321e2abbe68da8693ca3562bbacafcf3ea5a1`
- Recorded working tree: clean
- SHA-256: `2F1B92BA6337AC84C43FDC6FD1F4F0653BC2C4BEDBDD61A6D917F98DB03D7437`

Cumulative gate receipts generated after the authoritative T5 receipt was preserved:

- T4: `20260829T095908Z-0024328c`, PASS 14/14, SHA-256 `13975994F417AA784DD21E40D5820CCBAB12CECCADBCD038BBDB2C03FB3CC6CF`
- T3: `20260829T100018Z-8db946ba`, PASS 12/12, SHA-256 `134056D6E1904E1C6E461C04799419ECA986947A4F8DD9BE6A298FCD8A7F2F28`
- T2: `20260829T100131Z-0431a9bf`, PASS 13/13, SHA-256 `5F828115423130E150FDC8A5DB2B042F5DFFD27BCCE712AEFDCE98A6EC528252`
- T1: `20260829T100153Z-73086b49`, PASS 9/9, SHA-256 `09C288B4326CCA0AE718DE100383DCA5238ED664A93B4D99FB4F43D38DB9BB13`
- T0: `20260829T100254Z-e375b5eb`, PASS 13/13, SHA-256 `82C3DF20FB50C7CC140790681B3899378AF059ECB7BDB85E0732FAA7F184D67E`

## Review position

T5 is submitted for operator review at AWAITING_APPROVAL. This entry supersedes `0037`
only as the current lifecycle position; it does not rewrite the execution-start history.
The builder must stop here unless the operator returns T5 for bounded repair or
explicitly approves parking and P5 credit.
