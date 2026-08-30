# External Review: T6 Removable MCP Entrance

Date: 2026-08-30T12:55:28Z
Reviewer: The Reviewer
Reviewed commit: 9ca89eb69432a4a4d8b03ea1558484296bfd8688
Reviewed evidence: .builder/journal/0040-t6-removable-mcp-entrance-declaration.md; .builder/journal/0041-t6-execution-start.md; .builder/journal/0042-t6-awaiting-approval.md; .builder/evidence/T6/20260830T101453Z-956b023b/t6-gate.json; cumulative gate receipts .builder/evidence/T5/20260830T101603Z-967e76c8/t5-gate.json, .builder/evidence/T4/20260830T101728Z-3e23e4f5/t4-gate.json, .builder/evidence/T3/20260830T101835Z-a4bbaa7a/t3-gate.json, .builder/evidence/T2/20260830T101945Z-42392a2b/t2-gate.json, .builder/evidence/T1/20260830T102005Z-8c3388b0/t1-gate.json, .builder/evidence/T0/20260830T102107Z-bdc96082/bootstrap-gate.json

## Disposition

APPROVE CANDIDATE

## Executive Finding

T6 appears complete and effective for operator approval: the repaired candidate now provides a removable MCP stdio entrance that projects the live manifest catalog, routes tool calls through the shared ControlPlane, reads durable state through owner APIs, survives adapter removal from the CLI side, and remains within the declared adapter boundary. I found no approval-relevant unresolved requirement.

## Findings

- [NOTE] The prior returned T6 findings appear resolved in the repaired candidate.
  Evidence: .builder/journal/0042-t6-awaiting-approval.md; product/core/mcp.py::_call_manifest_tool; product/core/cli.py::main; tests/test_t6_mcp_entrance.py; .builder/gates/t6_mcp_entrance.py::_discrimination_witness
  Required action: none
- [NOTE] T6 gate evidence was recorded before the final construction-state commit, but current HEAD shows no product, test, or T6 gate drift from the gate receipt commit.
  Evidence: .builder/evidence/T6/20260830T101453Z-956b023b/t6-gate.json; `git diff --name-status 3910503594de0b94da9d4703a0e90d278644d540 HEAD`
  Required action: none
- [NOTE] The candidate explicitly does not claim MCP exposure of the full T5 preview/approval/apply mutation workflow.
  Evidence: .builder/journal/0042-t6-awaiting-approval.md; product/core/mcp.py::_call_projection; tests/test_t6_mcp_entrance.py::test_mcp_apply_authority_uses_call_envelope_and_records_receipt
  Required action: none

## Boundary Checks

- T6 uses `product/core/mcp.py` as an adapter and delegates manifest tools through `ControlPlane(context).invoke`; it does not launch tools directly.
- MCP catalog projection is live from `registry.discover(context)` and preserves manifest `input_schema`; authority and timeout are call-envelope controls, not injected manifest schema fields.
- Durable reads route through owners: `runtime_records`, `app_journal`, `substrate`, `awareness`, and `mutation`.
- CLI lazy-loads MCP only for `sidecar mcp`; product lower layers do not import MCP.
- Removing `product/core/mcp.py` leaves CLI status, tool call, receipts, and read paths usable; `sidecar mcp` fails truthfully with `mcp_unavailable`.
- No new GUI, local AI, embeddings, domain cartridges, release/update/removal, rollback, workflow engine, autonomous agent, marketplace, remote/cloud, auth, streaming progress, or parallel backend surface was identified.
- T0-T5 remain parked; T6 remains `AWAITING_APPROVAL`; P6 is not credited; T7 has not begun.

## Evidence Checked

- Inspected `.builder/evidence/reviews/REVIEWER_MANIFEST.md`, `.builder/CURRENT_STATE.md`, `.builder/TRANCHE_PLAN.md`, `docs/ARCHITECTURE.md`, T6 journal entries `0040`-`0042`, prior T6 external review, T6 gate receipt, product MCP/CLI/host code, T6 tests, and T6 gate code.
- `git rev-parse HEAD` -> `9ca89eb69432a4a4d8b03ea1558484296bfd8688`.
- `git status --short --branch` before this review note -> clean branch state, `codex/t1-mechanical-host...origin/codex/t1-mechanical-host [ahead 2]`.
- `git diff --name-status 3910503594de0b94da9d4703a0e90d278644d540 HEAD` -> construction docs/evidence/journal/README/ARCHITECTURE drift only; no product/test/gate source drift.
- `python -B -m pytest tests\test_t6_mcp_entrance.py -q` -> passed, 8 tests.
- `python -B -m pytest -q` -> exit 0; gate receipt records 56 canonical tests passed.
- `python -m ruff check . --no-cache` -> passed.
- `git diff --check` -> passed.

## Discrimination Review

- A hard-coded MCP catalog could pass static existence checks while violating shared catalog ownership; current tests mutate an installed manifest and assert MCP sees the changed description, and the gate rejects removal of `registry.discover(context)`.
- A direct MCP tool launcher could produce receipts while bypassing host authority; current tests require receipt provenance for `client=mcp` and gate discrimination rejects replacing `ControlPlane(context).invoke`.
- A private MCP state reader could pass happy-path listings while owning lower tables; source inspection and gate checks reject SQL/table ownership terms in `product/core/mcp.py`.
- A non-removable CLI dependency could pass MCP behavior while breaking CLI without the adapter; current tests remove the adapter and assert status, call, read, receipts, and truthful MCP failure.
- A malformed JSON-RPC loop could pass normal calls while mishandling notifications/errors; current tests cover parse errors, unknown methods, and silent `notifications/initialized`.
- An MCP listing side effect could pass catalog checks while creating memory/state; current tests assert no App Journal entries, substrate resources, mutation records, or MCP sqlite state are created by initialize/list.

## Residual Risk

- MCP remains a minimal stdio adapter with a narrow JSON-RPC surface; broader MCP features are intentionally deferred and should not be inferred from P6 credit.
- MCP can call mechanical tools with an `apply` authority envelope, but the full T5 preview/approval/apply loop is not exposed through MCP in this candidate and is not claimed as a T6 closure condition.

## Suggested Operator Action

Approve the T6 candidate, then direct the Builder to perform park closeout, credit P6, update construction state through the normal journal/plan/current-state chain, and stop before any T7 declaration until separately instructed.
