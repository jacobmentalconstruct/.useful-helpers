# T2 Runtime Receipts and Work Memory Awaiting Approval

- Date: 2026-08-26
- Tranche: T2 Runtime Receipts + Work Memory
- Entry class: implementation review submission
- Transition: IMPLEMENTING -> VERIFYING -> AWAITING_APPROVAL
- Approved declaration: `0016-t2-runtime-receipts-work-memory-declaration.md`
- Approved scope amendment: `0017-t2-declaration-scope-amendment.md`
- Execution start: `0018-t2-execution-start.md`
- T2 outcome PARKED: no
- T3 started: no

## Declared outcome

T2 was narrowed to durable operation identity/receipts and operational artifacts for
governed calls after trusted installed state ownership is resolved, plus a blank-start
App Journal for deliberate project/work memory. T2 explicitly excludes preview-first
mutation, stale approval, governed apply-loop changed-path measurement, target-native
verification workflow, compatible update proof, removal proof, T3 epistemic substrate,
T4 awareness, MCP, GUI, and release packaging.

## What changed

The product SQLite schema advanced to version 2 and now creates distinct runtime tables
for `operation_receipts`, `operational_artifacts`, `app_journal_entries`, and
`app_journal_links`.

`product/core/runtime_records.py` owns operation receipts and operational artifacts.
`product/core/app_journal.py` owns deliberate App Journal entries and links. The CLI now
has minimal consumer commands to list/read receipts and artifacts, and to create, list,
read, and link App Journal entries.

`ControlPlane.invoke()` now establishes a durable operation receipt after trusted
instance/state ownership exists and before child-process launch. It records success,
host refusals, malformed child output, tool process failure, and current-route mutation
results as runtime operation facts. If receipt creation fails, it returns
`receipt_persistence_failed` with `durably_governed = false`; a state-changing tool is
not launched in that case.

The mechanical tool layer remains separated: tools still consume only
`core.tool_runtime`, and no receipt or App Journal responsibility moved into
`product/tools/*`.

## Deliberate non-changes

The existing write-file route still applies immediately when the host grants `apply`
authority and the tool contract receives `confirm = true`. T2 records that route; it
does not convert it into preview/apply. Reviewed previews, approval binding,
stale-preview refusal, independent changed-path measurement, target-native verification,
and refresh remain deferred to T5 Governed Mutation Loop.

Compatible update and deletion/removal proof remain deferred to T8 Release and STOP.
Operational artifacts produced in T2 are evidence of runtime operations only, not the T3
epistemic evidence owner for target observations or claims.

## Verification history

Focused T2 tests were first added red against the pre-T2 runtime: `receipts`, `artifacts`,
and `journal` CLI commands were absent, runtime memory tables were absent, and receipt
failure could not be tested. After implementation, the focused T2 tests passed.

A power interruption occurred after the initial implementation work and before the full
verification run completed. On resume, the repository was remeasured at commit
`8b019b6`, with the T2 implementation surviving as uncommitted work. The builder reran
focused T2 tests, canonical pytest, and Ruff before continuing.

The first T2 gate run `20260826T221102Z-a13fa693` failed 9/11 because the new gate's
static discovery scanned generated `tests/.runtime` fixture state and hygiene correctly
reported that fixture debris. Its preserved SHA-256 is
`5CBBAA95E0AFE4236806E80C72A9896971A46138ECF51AB76D17C209221BE9CA`.

After tightening the gate to ignore generated fixture state during static discovery and
removing fixture debris, T2 gate run `20260826T221208Z-d1ffacfc` passed 11/11 against a
dirty implementation tree. Its preserved SHA-256 is
`91473E2C4ECE0A8E6265E1D8AC28A8A4C89B1F206EEB9B3D91BFEFB7A2A12A22`.

Commit `2f7f3cf3056e89eed2c8bc36171f72856acd79f2` records the T2 implementation, tests,
gate, and provisional gate evidence.

Authoritative T2 run `20260826T221337Z-93739b8d` passed 11/11 from clean commit
`2f7f3cf`, with an empty recorded working tree and SHA-256
`4B784C6FCBF440F7C658D23A13D586049E473B38EB9EA3661DB94B333656A270`. Commit
`55f2d4c25f54d8a63aad541d49bf5609b9e12ece` preserves that receipt.

Cumulative T1 run `20260826T221441Z-b2684cf6` passed 9/9 from clean commit `55f2d4c`,
with SHA-256 `56350C3C5C3BC3C4C1C5282CBFF486F5292F3D530E9DB1417E047CD8E8C2DE30`.
Commit `dacd690` preserves that receipt.

Cumulative T0 run `20260826T221526Z-8a41f038` failed 12/13 because Architecture and the
T0 lifecycle-status check still recognized only the earlier T1 lifecycle wording. Its
preserved SHA-256 is
`355FB213D0B8BEF4DE87015283264FD26508D39338ED043185209654B1EA221A`.

Architecture and the T0 lifecycle-status check were synchronized without changing T2
runtime behavior. Cumulative T0 run `20260826T221803Z-a47fda50` then passed 13/13 from
clean commit `e0dc00a`, with SHA-256
`F06BF98C82265F1E7064EB89FA191736925458C7631E322ED6FD75E2A008991E`. Commit `9b9920c`
preserves that receipt.

Final T2 run `20260826T221856Z-b97a3845` passed 11/11 from clean commit `9b9920c`, with
an empty recorded working tree and SHA-256
`A190F0B6BBF646061B8183A2314E79FB37B778B8628A4BEB774DFA03A61DD308`. Commit `c308ced`
preserves that receipt.

## Review evidence summary

- Focused T2 product tests: 5 passed.
- Canonical pytest: 20 passed.
- Ruff/static discovery: passed.
- T2 gate: 11/11 passed.
- Cumulative T1 gate: 9/9 passed.
- Cumulative T0 gate: 13/13 passed after documented lifecycle-status synchronization.
- Discrimination witness: rejected journal/receipt table collapse, automatic
  receipt-to-journal projection, and missing receipt failure guard.

## Changed surfaces

- `product/core/storage.py`
- `product/core/runtime_records.py`
- `product/core/app_journal.py`
- `product/core/control.py`
- `product/core/cli.py`
- `product/core/constants.py`
- `tests/test_phase1.py`
- `tests/test_t2_runtime_memory.py`
- `.builder/gates/t2_runtime_receipts_work_memory.py`
- `.builder/gates/t0_bootstrap.py`
- `docs/ARCHITECTURE.md`
- `.builder/evidence/T0/`
- `.builder/evidence/T1/`
- `.builder/evidence/T2/`
- `.builder/TRANCHE_PLAN.md`
- `.builder/CURRENT_STATE.md`

## Remaining risks and deferred work

The T2 schema is intentionally minimal and does not yet include the T3 resource,
observation, claim, provenance, or epistemic evidence model. Operational artifact bodies
are JSON rows rather than content-addressed object-store blobs; that is sufficient for T2
runtime-operation evidence and remains open for T3.

The current mutation route is still immediate apply behind authority plus tool
confirmation. That is accepted T2 non-scope and must be addressed by T5 before Product
STOP can claim governed mutation.

T2 has not been operator approved or parked. P3 is not credited until the operator grants
terminal disposition. T3 has not begun.

## Review position

T2 is submitted for operator review at AWAITING_APPROVAL. The builder must stop here.
Do not park T2 and do not begin T3 without explicit operator approval.
