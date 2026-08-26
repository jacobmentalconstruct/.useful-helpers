# T0 Vision-Alignment Reopen Declaration

- Date: 2026-08-26
- Tranche: T0 Bootstrap
- Entry class: bounded reopen and alignment declaration
- Transition: PARKED -> REOPENED -> IMPLEMENTING
- Reopen authority: operator
- Preserved park revision: `91413b1` (`Park operator-approved T0 bootstrap`)

## What T0 originally established

T0 established repository construction authority, Product Charter and STOP ownership,
product/factory boundaries, a finite tranche plan, immutable construction history and
evidence, one gate authority, a canonical test entrance, and a preserved provisional
runtime baseline. Its original journal and gate receipts remain immutable.

## Later understanding

The intended product boundary is now more precise. Sidecar Workbench is one integrated
local instrumentation host, while Coherent Development is an independent product-neutral
method. Mechanical capabilities and App Journal semantics must remain lower-layer and
separable from host projections and construction machinery. Host binding is transported
context and policy, not tool identity. Runtime receipts, App Journal memory, and builder
history are three different record classes.

## Reconciliation table

| Current authority/clause | Finding | Evidence measured before amendment | Minimal amendment required |
|---|---|---|---|
| Charter constitutional statement | Partially aligned | Calls the product a local instrumentation system, but does not separate it from a general development method. | State that Coherent Development is independent and the workbench may support it without owning it. |
| Charter P1 Lifecycle | Partially aligned | Structural identity, update preservation, and removal are explicit; host ownership of binding is not. | Assign root/identity/policy resolution to the host and transport context to capabilities. |
| Charter P2 Governed hands | Conflicting | Says tools operate through one authority; current tools import `core.tool_runtime.ToolContext`, whose required document includes `instance_uuid`. | Distinguish portable mechanical contract from Sidecar-hosted governed invocation and require a minimal shared tool substrate. |
| Charter P3 Durable memory | Conflicting | Operations, evidence, blank-start product journal, resources, and claims are compressed into one condition. | Separate operational receipts/event ledger, App Journal project memory, epistemic evidence/substrate, and construction history. |
| Charter P4 Orientation | Aligned with missing seam | Awareness is compact and provenance-backed; no lower-layer independence statement exists. | Forbid tools and journal semantics from depending upward on awareness. |
| Charter P5 Governed mutation | Aligned with ambiguous terminology | Preview, stale rejection, measurement, verification, refresh, and history are explicit; “historical chain” does not name its owners. | Attribute calls/events to receipts, evidence to substrate, and decisions/park memory to App Journal. |
| Charter P6 Projection parity | Partially aligned | CLI and MCP share one world, but MCP removability and CLI sufficiency are unstated. | Define both as entrances; require MCP removal not to destroy host or mechanical capabilities. |
| Charter P7 Truthful breadth | Aligned | Software, mixed records/documents, and empty targets have separate known-answer fixtures. | Preserve unchanged. |
| Charter P8 Releasability and Product STOP | Partially aligned | Clean Windows/Linux artifact and construction exclusion are explicit; upward dependency protection is not. | Add sealed-artifact dependency-direction proof without requiring package extraction. |
| Product/factory and history boundary | Partially aligned | Factory separation and two journal lifecycles are explicit; receipts and App Journal are not separately owned. | Define construction history, runtime receipts, App Journal, evidence, and awareness as distinct authorities/lifecycles. |
| Plan T1 Bound Hands | Conflicting | Outcome says a structurally bound instance exposes capabilities, permitting identity to appear intrinsic to tools. | Rename/reframe T1 around portable mechanical hands plus host-resolved governed use. |
| Plan T2-T5 outcomes | Partially aligned | Receipts, substrate, awareness, and MCP are sequenced but history ownership and MCP removability are implicit. | Clarify record ownership and lower-to-upper dependency direction in outcomes and non-goals. |
| Clean install/update/removal | Aligned | P1 preserves UUID/state on compatible update; P8 excludes construction history; Charter says runtime journal starts empty. | Clarify that all engagement-owned runtime state starts blank and survives update, while removal deletes the instrument. |

## Declared outcome

Current product and construction authorities encode one integrated Sidecar Workbench,
an independent Coherent Development method, separable mechanical tools, host-owned
context transport, entrance parity, three distinct history/state classes, blank runtime
state, and downward-only dependency direction without expanding prototype scope.

## Scope and non-goals

Changed surfaces are limited to the BCC, Product Charter, Tranche Protocol, Tranche Plan,
Architecture, Current State, T0 gate checks, README orientation if needed, and new T0
journal/evidence. No product source, tool manifest, runtime schema, package extraction,
standalone distribution, T1 declaration, or T1 implementation enters this reopen.

## Completion evidence and ordered plan

1. Amend canonical owners rather than add another authority.
2. Make Architecture record the measured provisional coupling as T1 debt.
3. Add narrow gate assertions for method/product separation, history ownership,
   dependency direction, T1 wording, and adapter removability.
4. Run focused authority, AST/import, pytest, Ruff, and diff checks.
5. Commit the alignment candidate and run the authoritative T0 gate from a fresh clone,
   writing its immutable receipt to this repository.
6. Append a replacement awaiting-approval record, synchronize Plan/Current State with
   focused non-certification checks, and stop without beginning T1.
