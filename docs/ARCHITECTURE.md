# Architecture

Status: **T1 IMPLEMENTATION REVIEW CANDIDATE - AWAITING OPERATOR APPROVAL**

## Charter relationship

The [Product Charter](PRODUCT_CHARTER.md) owns product identity, method/product boundary,
invariants, topology and dependency direction, runtime state classes, P1-P8, the
acceptance walk, Product STOP, and product non-goals. This document does not redefine
those facts. It maps the implementation currently present in the repository to the
Charter responsibilities it is intended to realize. That implementation has not been
audited or approved by a product tranche.

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
- `product/core/tool_runtime.py` owns the product-neutral mechanical subprocess protocol,
  strict transported context, target-relative handles, excluded-root behavior, and
  deterministic error serialization.
- `product/core/storage.py` owns the current SQLite bootstrap.
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
7. invoke the tool in a child Python process with serialized arguments and context;
8. validate the structured result and return a common envelope.

The host resolves complete instance identity and containment before dispatch. The JSON
request transports only already-resolved mechanical facts; environment configuration
locates the installed Python modules but does not carry project identity. Preview/apply
governance, independent mutation
measurement, durable operation receipts, cancellation, and invalidation are not present
and receive no architectural or Product STOP credit.

## Current substrate implementation

The current foundation for Charter product invariant 5 is
`.sidecar/state/workbench.sqlite3`. `product/core/storage.py` enables foreign keys, WAL,
and full synchronous writes; applies a `PRAGMA user_version` migration; and stores one
instance row whose UUID must agree with `instance.json` on re-entry.

The database does not yet implement the Charter's required operational receipt/event
ledger, App Journal, resource, observation, evidence, claim, provenance, or awareness
records. Those are separate semantic owners even if later implemented in one SQLite
database. The objects directory is created but has no accepted object-store contract.

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
Dependency mutation proves the T1 gate rejects `core.instance` imported by a mechanical
tool. The candidate remains unapproved until the operator rules on journal entry `0011`;
this document does not grant P1/P2 or Product STOP credit.
