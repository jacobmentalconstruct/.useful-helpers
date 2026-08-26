# Architecture

Status: **T2 IMPLEMENTATION REVIEW CANDIDATE - AWAITING OPERATOR APPROVAL**

## Charter relationship

The [Product Charter](PRODUCT_CHARTER.md) owns product identity, method/product boundary,
invariants, topology and dependency direction, runtime state classes, P1-P8, the
acceptance walk, Product STOP, and product non-goals. This document does not redefine
those facts. It maps the implementation currently present in the repository to the
Charter responsibilities it is intended to realize. The T1 mechanical-host boundary is
parked by operator approval. The T2 runtime memory implementation is a review candidate
and is not parked until the operator grants that terminal disposition.

## Current installed-instance realization

Charter product invariants 1 and 2 are currently approached with this emitted structure:

```text
TARGET/
    user-owned-content/
    .sidecar/
        instance.json
        bin/
        core/
        tools/
        state/
            workbench.sqlite3
            objects/
        logs/
```

`factory/installer.py` positively copies `product/bin`, `product/core`, and
`product/tools`, creates private state and log directories, then asks
`product/core/instance.py` and `product/core/storage.py` to create identity and storage.
It removes the incomplete `.sidecar` if attachment fails.

`product/core/instance.py` requires `instance.json` at an explicitly supplied instance
root. The manifest stores a UUID and `target_relation = ".."`; loading resolves the
target from that relation and rejects a missing, malformed, unsupported, or structurally
inconsistent instance. No fallback identity-discovery path is present.

## Current module responsibilities

- `product/bin/sidecar.py` is the installed composition root and delegates to the CLI
  adapter.
- `product/core/cli.py` translates CLI arguments and delegates tool calls to the control
  plane.
- `product/core/control.py` coordinates instance loading, catalog lookup, contracts,
  containment, child-process execution, and result envelopes.
- `product/core/registry.py` discovers tool manifests from the installed `tools/` tree.
- `product/core/containment.py` resolves manifest-declared path arguments.
- `product/core/runtime_records.py` owns runtime operation receipts and operational
  artifacts.
- `product/core/app_journal.py` owns deliberate runtime App Journal entries and their
  links to receipt or artifact identifiers.
- `product/core/tool_runtime.py` owns the product-neutral mechanical subprocess protocol,
  strict transported context, target-relative handles, excluded-root behavior, and
  deterministic error serialization.
- `product/core/storage.py` owns the current SQLite bootstrap and migration mechanics.
- `product/tools/<id>/` contains manifest-described deterministic capabilities.

T1 audited these measured locations and retained them because their responsibilities
match the approved ownership boundary; no cosmetic re-homing was needed.

## T1 mechanical-host seam realization

All five `product/tools/*/tool.py` modules now import only the product-neutral
`core.tool_runtime.MechanicalContext` and `run_tool` substrate. The context contains a
resolved `target_root` plus explicit `excluded_roots`; it rejects unknown fields, so an
instance UUID, instance root, or state root cannot silently return to the mechanical
contract.

`InstanceContext` retains the complete installed identity but no longer projects itself
to tools. `ControlPlane` validates the host context, manifest, authority, input, and path
containment before constructing the narrower mechanical context. Excluding the installed
host subtree is transported as an ordinary root capability, not interpreted by tools as
Sidecar identity.

## Current control-plane mechanics

The current implementation approaches Charter product invariants 3 and 4 through
`product/core/control.py`. Its invocation sequence is:

1. load an explicitly named instance root;
2. discover and validate the requested manifest;
3. compare requested and declared authority;
4. validate input shape;
5. resolve declared target or instance paths through containment;
6. shape product-neutral context from the already validated host facts;
7. establish a durable operation receipt after trusted state ownership is available;
8. invoke the tool in a child Python process with serialized arguments and context;
9. validate the structured result;
10. record a durable operational artifact supporting the receipt; and
11. return a common envelope containing receipt and artifact identifiers when recording
    succeeds.

The host resolves complete instance identity and containment before dispatch. The JSON
request transports only already-resolved mechanical facts; environment configuration
locates the installed Python modules but does not carry project identity.

If receipt creation fails, the control plane reports `receipt_persistence_failed` with
`durably_governed = false`. That failure happens before child-process launch, so a
state-changing tool does not silently proceed as durably governed when the required
operation record cannot be established.

Preview/apply governance, stale approval binding, governed mutation measurement,
target-native verification workflow, refresh, cancellation, and invalidation are not
present and receive no architectural or Product STOP credit in T2.

## Current substrate implementation

The current foundation for Charter product invariants 6 and 7 is
`.sidecar/state/workbench.sqlite3`. `product/core/storage.py` enables foreign keys, WAL,
and full synchronous writes; applies `PRAGMA user_version` migrations; and stores one
instance row whose UUID must agree with `instance.json` on re-entry.

Schema version 2 adds distinct T2 runtime tables:

- `operation_receipts` records governed invocation/event facts after trusted installed
  state ownership is resolved.
- `operational_artifacts` stores JSON artifacts that substantiate operation receipt
  facts, such as tool envelopes and captured process output.
- `app_journal_entries` stores deliberate project/work memory entries with entry type,
  status, title, and body.
- `app_journal_links` links App Journal entries to `operation:` or `artifact:`
  identifiers without turning receipts into journal entries.

These operational artifacts are evidence of runtime operations only. They are not the T3
epistemic evidence owner for target observations or claims. The database still does not
implement canonical resource inventory, observations, derived claims, provenance graph,
awareness revisions, or semantic/vector indexes. The objects directory is created but has
no accepted object-store contract.

## Current tool contract

Each `product/tools/<id>/manifest.json` declares identifier, description, authority,
input and output schemas, read/write domains, applicability, path arguments, and module
entry point. `product/core/registry.py` reads manifests directly, so no generated catalog
is authoritative. Tools receive resolved context and return JSON; they contain no CLI,
MCP, or caller-specific path.

Five tools are present: inventory, read file, exact text search, hash file, and write
file. Their manifests own machine-readable input, output, authority, domain,
applicability, path, and invocation contracts. Their mechanics depend only on the
standard library plus `core.tool_runtime`; no tool imports identity, CLI, control,
registry, storage, awareness, MCP, GUI, factory, tests, or tranche machinery.

## T1 review evidence

The fixtures report that a normal or empty target can be attached, re-entered
after process restart and relocation, inspected through discovered tools and one
CLI/control-plane path, protected from path escape, and left unchanged outside the
single `.sidecar` directory except for an explicitly authorized work product.

Direct subprocess fixtures also invoke all five mechanics with no Sidecar instance,
while a live host probe receives only `target_root` and `excluded_roots`. A malicious
child leaves no launch witness when identity, authority, input, or containment fails.
Dependency mutation proves the T1 gate rejects `core.containment`, `core.contracts`, and
`core.instance` when injected into both a mechanical tool and the shared runtime. Journal
entry `0015` records operator approval and parks T1. This document maps the approved
implementation state; Product STOP remains incomplete until P3-P8 are also proven.

## T2 review evidence

T2 product fixtures report that a fresh attach starts with blank runtime receipts,
operational artifacts, App Journal entries, and App Journal links. Successful reads,
authority refusals before child launch, malformed child JSON, child process failure, and
the existing immediate write route are recorded after state ownership is resolved.

Receipts and operational artifacts remain distinct from App Journal entries. Journal
entries are deliberate work-memory records with entry type and status, may link to
receipt or artifact identifiers, do not appear automatically after tool calls, and remain
available across process restart/re-entry without awareness or MCP.

A failure-injection fixture adds a SQLite trigger that rejects receipt creation and then
attempts an apply-authority write. The control plane returns `receipt_persistence_failed`
with `durably_governed = false`, and the target file is not created. This proves the T2
failure invariant without implementing the later T5 preview/apply loop.

Authoritative T2 gate evidence is expected to be recorded by the review submission
journal entry. Until operator approval, T2 remains an implementation review candidate;
P3 is not parked and Product STOP remains incomplete.
