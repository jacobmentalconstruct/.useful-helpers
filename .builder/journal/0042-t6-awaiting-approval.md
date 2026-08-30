# 0042 - T6 Removable MCP Entrance Awaiting Approval

Date: 2026-08-30
Tranche: T6 Removable MCP Entrance
Status: AWAITING_APPROVAL

## Declaration

Entry `0040` declared T6 after T5 was parked and P5 was credited. Entry `0041` recorded
operator approval to enter IMPLEMENTING after the builder found no declaration
contradiction or blocker.

The declared outcome was a removable MCP stdio entrance that exposes the same host
catalog, governed tool calls, and durable world as the CLI without owning capabilities,
duplicating product logic, or making CLI/tools/lower layers depend on MCP.

## Review Return and Repair

External Reviewer evidence at
`.builder/evidence/reviews/T6/20260829T123032Z-external-review.md` returned the first T6
candidate to VERIFYING. The material findings were:

- the review submission journal entry cited by Plan, Current State, and Architecture was
  missing;
- T3 and T5 cumulative gate narrowing had not been recorded in construction history;
- MCP advertised manifest schemas that did not match the authority/timeout controls it
  accepted for manifest tool calls;
- `sidecar mcp` crashed with a traceback when the removable MCP adapter was absent;
- the JSON-RPC loop answered id-less notifications and rejected
  `notifications/initialized`.

The repair kept T6 inside its declared scope. MCP remains an entrance, not a capability
owner, and no T7/T8 domain or release work began.

## What Changed

- `product/core/mcp.py` now carries manifest-tool authority and timeout through the MCP
  `tools/call` envelope rather than hidden tool arguments. Manifest `inputSchema`
  remains the mechanical tool contract.
- `product/core/mcp.py` suppresses responses to id-less notifications and accepts
  `notifications/initialized` as a silent lifecycle notification.
- `product/core/cli.py` emits a normal JSON error envelope with code `mcp_unavailable`
  when `sidecar mcp` is invoked after the removable adapter is absent.
- `tests/test_t6_mcp_entrance.py` now proves MCP apply-authority write/refusal/receipt,
  notification handshake behavior, pure manifest input schema projection, and the
  removed-adapter CLI error.
- `.builder/gates/t6_mcp_entrance.py` now checks CLI eager MCP imports with AST,
  rejects missing apply-authority and notification witnesses, and reports external
  `--evidence-root` paths without crashing.
- The earlier T3/T5 cumulative gate narrowing remains bounded: T3 still forbids
  substrate/storage MCP ownership, and T5 still forbids mutation/control surfaces from
  growing MCP behavior, while permitting the later T6 adapter and CLI entrance to exist.

## Evidence

Focused and canonical checks from the repaired committed candidate:

- Focused T6 tests: `python -B -m pytest tests\test_t6_mcp_entrance.py -q` passed 8/8.
- Canonical tests: `python -B -m pytest -q` passed.
- Ruff: `python -m ruff check . --no-cache` passed.
- Whitespace check: `git diff --check` passed.

Authoritative T6 gate:

- T6: `20260830T101453Z-956b023b`, 11/11.

Cumulative gate receipts:

- T5: `20260830T101603Z-967e76c8`, 13/13.
- T4: `20260830T101728Z-3e23e4f5`, 14/14.
- T3: `20260830T101835Z-a4bbaa7a`, 12/12.
- T2: `20260830T101945Z-42392a2b`, 13/13.
- T1: `20260830T102005Z-8c3388b0`, 9/9.
- T0: `20260830T102107Z-bdc96082`, 13/13.

Intermediate failed receipts are preserved as evidence of discovery and discrimination:

- T6 `20260830T100455Z-05c75176` failed repository hygiene because concurrent pytest
  generated `__pycache__`; the gate was rerun serially after explicit cleanup.
- Prior Aug 29 T6/T5/T3 receipts exposed broad cumulative gate and fixture-runtime
  interactions before the final serial evidence cited above.

## Scope Held

T6 did not add GUI, local AI, embeddings, domain cartridges, release/update/removal,
remote service behavior, authentication, streaming protocol breadth, new deterministic
tools, a new mutation surface, new substrate facts, journal semantics changes, receipt
storage redesign, or construction-role runtime concepts.

MCP remains an entrance. It does not own tool contracts, host context, governance,
receipts, App Journal memory, substrate facts, awareness revisions, or mutation records.
The T5 governed mutation loop remains CLI-only at this boundary; exposing preview,
approval, and apply over MCP is deferred rather than silently claimed.

## Review Position

T6 is submitted for operator review. The builder does not park T6, credit P6, or begin
T7. Product STOP remains incomplete because P6-P8 are uncredited.
