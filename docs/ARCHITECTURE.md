# Architecture

Status: **PRE-BOOTSTRAP IMPLEMENTATION MAP - PROVISIONAL UNTIL T1**

## Charter relationship

The [Product Charter](PRODUCT_CHARTER.md) owns product identity, invariants, topology,
P1-P8, the acceptance walk, Product STOP, and product non-goals. This document does not
redefine those facts. It maps the implementation currently present in the repository to
the Charter responsibilities it is intended to realize. That implementation has not
been audited or approved by a product tranche.

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
- `product/core/tool_runtime.py` is the common child-process entry helper used by tools.
- `product/core/storage.py` owns the current SQLite bootstrap.
- `product/tools/<id>/` contains manifest-described deterministic capabilities.

These are measured locations, not an endorsement of their final ownership or naming.
T1 may re-home provisional code when it audits behavior and assigns an actual owner.

## Current control-plane mechanics

The current implementation approaches Charter product invariants 3 and 4 through
`product/core/control.py`. Its invocation sequence is:

1. load an explicitly named instance root;
2. discover and validate the requested manifest;
3. compare requested and declared authority;
4. validate input shape;
5. resolve declared target or instance paths through containment;
6. invoke the tool in a child Python process with serialized context;
7. validate the structured result and return a common envelope.

Environment variables transport already-resolved child context. They are not consulted
to discover instance identity. Preview/apply governance, independent mutation
measurement, durable operation receipts, cancellation, and invalidation are not present
and receive no architectural or Product STOP credit.

## Current substrate implementation

The current foundation for Charter product invariant 5 is
`.sidecar/state/workbench.sqlite3`. `product/core/storage.py` enables foreign keys, WAL,
and full synchronous writes; applies a `PRAGMA user_version` migration; and stores one
instance row whose UUID must agree with `instance.json` on re-entry.

The database does not yet implement the Charter's required resource, observation,
evidence, claim, operation, provenance, awareness, or product-journal records. The
objects directory is created but has no accepted object-store contract.

## Current tool contract

Each `product/tools/<id>/manifest.json` declares identifier, description, authority,
input and output schemas, read/write domains, applicability, path arguments, and module
entry point. `product/core/registry.py` reads manifests directly, so no generated catalog
is authoritative. Tools receive resolved context and return JSON; they contain no CLI,
MCP, or caller-specific path.

Five provisional tools are present: inventory, read file, exact text search, hash file,
and write file. Their contracts and behavior remain T1 audit subjects.

## Provisional implementation evidence

The existing fixtures report that a normal or empty target can be attached, re-entered
after process restart and relocation, inspected through discovered tools and one
CLI/control-plane path, protected from path escape, and left unchanged outside the
single `.sidecar` directory except for an explicitly authorized work product.

This is pre-bootstrap evidence available to T1. It is not a parked tranche, Product STOP
score, product-invariant finding, or architectural approval.
