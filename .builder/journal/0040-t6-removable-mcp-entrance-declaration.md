# 0040 - T6 Removable MCP Entrance Declaration

Entry type: tranche declaration
Tranche: T6 Removable MCP Entrance
Status: DECLARED
Date: 2026-08-29

## Operator direction

The operator directed: declare T6 and then begin. This entry records the declaration.
Because the same instruction explicitly authorizes beginning after declaration, the next
builder action may record an execution-start entry and enter IMPLEMENTING if this
declaration exposes no contradiction or blocker. T6 must still stop at AWAITING_APPROVAL;
the builder may not park T6, credit P6, or begin T7 without later operator approval.

## Re-orientation and measured state

T0-T5 are PARKED. P1-P5 are credited. Product STOP remains incomplete because P6-P8 are
UNSCORED.

The live product has one installed composition root at `product/bin/sidecar.py`, one CLI
adapter in `product/core/cli.py`, one governed control plane in `product/core/control.py`,
manifest discovery in `product/core/registry.py`, five deterministic tools, runtime
receipts/artifacts, App Journal commands, T3 substrate commands, T4 awareness commands,
and T5 mutation commands. No MCP adapter or MCP runtime entry point currently exists.

The repository is clean at declaration measurement on branch `codex/t1-mechanical-host`.

## Declared outcome

T6 proves entrance parity and removability at prototype scale:

> A minimal MCP stdio entrance exposes the same host catalog, authority-governed tool
> calls, receipts, App Journal, substrate, awareness, and mutation world as the CLI,
> while CLI, the governed host, mechanical tools, and durable state remain usable when
> the MCP adapter is absent.

## Scope

T6 may add:

- a small MCP adapter module under `product/core/`;
- a small installed front-door command or CLI subcommand to run the MCP stdio server;
- manifest-to-MCP tool projection for the existing host catalog;
- MCP calls that delegate to the existing control plane and existing state owners;
- MCP-accessible operations for current/status-oriented runtime surfaces where needed to
  prove P6: host status, tool catalog, tool call, receipt read/list, App Journal
  read/list, substrate read/list/trace/status, awareness current/drill/status, and
  mutation status/history/links;
- focused T6 product tests and a T6 gate under `.builder/gates/`;
- minimal documentation updates needed for review.

The MCP adapter may implement the small JSON-RPC-over-stdio subset needed for these
tests rather than adopting a framework. If a framework is later warranted, that is a
future evidence-based decision.

## Non-goals

T6 does not implement a GUI, local AI, embeddings, domain cartridges, release/update or
removal lifecycle, rollback, workflow engine, autonomous agent, plugin marketplace,
remote/cloud service, broad MCP ecosystem integration, authentication, streaming
progress, resource subscriptions, prompts, sampling, or a second product backend.

T6 does not add new deterministic mechanical tools, widen the T5 mutation surface, create
new substrate facts, change App Journal semantics, redesign receipt storage, or make MCP
the owner of capabilities.

## Ownership and dependency rules

MCP is an adapter/projection only. It may import existing host/state owner APIs and route
through them. It must not directly write tool, receipt, journal, substrate, awareness, or
mutation tables. It must not invoke mechanical tools directly. It must not become a
required import of CLI, control plane, registry, tools, tool runtime, receipts, App
Journal, substrate, awareness, or mutation.

CLI remains the canonical low-level/debugging entrance. Removing the MCP module and any
MCP front door must leave CLI status, tools, governed tool call, and at least one durable
state read usable.

## Completion evidence

T6 is complete only when evidence proves:

1. Fresh attach has no inherited MCP state and CLI still works before MCP is used.
2. MCP `initialize`/tool discovery returns a projected catalog derived from the existing
   host/tool/state owners rather than a hard-coded private catalog.
3. MCP tool call for an observe tool routes through the existing `ControlPlane` and
   creates the same kind of durable operation receipt/artifact as CLI.
4. MCP read/list operations expose receipts, App Journal, substrate, awareness, and
   mutation records through their owning APIs rather than direct table ownership.
5. MCP and CLI inspect the same durable world across process restart/re-entry.
6. Removing or disabling the MCP adapter leaves CLI, host, registry, and mechanical tools
   usable.
7. Dependency checks prove lower layers do not import MCP and product source does not
   import construction history, tests, or factory runtime behavior.
8. A malformed or unknown MCP request fails truthfully without crashing the server or
   writing misleading durable state.
9. No T6 implementation introduces out-of-scope surfaces.
10. Canonical pytest, Ruff, `git diff --check`, T6 gate, and cumulative T5/T4/T3/T2/T1/T0
    gates pass.

## Discrimination plan

The T6 gate must reject plausible wrong implementations:

- a hard-coded MCP catalog that still passes because current tool IDs happen to match;
- direct mechanical tool launch from MCP that bypasses the control plane and receipts;
- MCP-private receipt/journal/substrate/awareness/mutation reads that bypass owners;
- CLI importing MCP or failing when the MCP adapter is removed;
- lower layers importing MCP upward;
- malformed JSON-RPC causing unstructured crashes;
- MCP automatically creating App Journal entries or new epistemic facts merely by
  observing.

## Ordered implementation plan

1. Add focused T6 fixtures that fail against the current repo: no MCP entrance, no MCP
   catalog, no MCP routed tool call, no removability witness.
2. Add a T6 gate with structural dependency, owner-use, no-out-of-scope, and
   discrimination assertions.
3. Add the minimal MCP adapter and installed entrance.
4. Route MCP catalog/tool calls through existing registry/control-plane behavior.
5. Add read/list projection operations through existing runtime owner APIs.
6. Prove restart/re-entry and removability through the real installed entrance.
7. Consolidate naming, error envelopes, boundary checks, docs, and generated debris.
8. Run focused tests, canonical pytest, Ruff, `git diff --check`, T6 gate, and cumulative
   T5/T4/T3/T2/T1/T0 gates.
9. Synchronize review documentation and submit T6 at AWAITING_APPROVAL.

## Risks

MCP protocol scope can expand easily. T6 intentionally proves the adapter boundary, not a
complete MCP platform. The first implementation should prefer a boring stdio JSON-RPC
loop and a small set of capability projections over framework adoption or broad protocol
coverage.

Another risk is making MCP names a second tool contract. The authoritative capability
contract remains the manifest and existing owner APIs; MCP names are projection handles
that must route back to those owners.

## Park condition

T6 can be parked only after operator approval of an AWAITING_APPROVAL submission with
the evidence above. P6 remains UNSCORED until that approval.
