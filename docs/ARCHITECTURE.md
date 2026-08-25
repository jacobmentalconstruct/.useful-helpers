# Architecture Charter

This document is the architectural authority for Sidecar Workbench.

## Product identity

Sidecar Workbench is a self-contained local instrument attached to one directory. It
observes that directory, builds durable evidence-backed knowledge about it, exposes
deterministic capabilities over it, and allows humans or agents to make governed
changes through the same control plane.

It is a local project instrumentation system, not primarily an AI assistant. AI may
consume observations or produce derived claims, but it is neither authority nor
canonical storage.

The design optimizes for an intentional asymmetry: local compute and storage are
cheap; model context, remote calls, repeated rediscovery, and human attention are
expensive.

## Invariants

1. **One sidecar, one target.** An installed instance is a direct child of its target.
   Identity is a UUID plus a relative structural relationship, never an absolute path,
   current working directory, environment variable, or folder-name guess.
2. **Clean removability.** Instrument-owned code, state, logs, and artifacts live
   beneath `.sidecar`. Removing that directory removes the instrument. Approved target
   work products are separate and remain.
3. **One control plane.** CLI, MCP, a future panel, and other clients are adapters over
   one `invoke(tool, args, client, authority)` boundary. Projections own no private
   capabilities.
4. **Deterministic hands.** Tools are headless capabilities with strict, machine-readable
   manifests. They do not infer instance identity or caller type.
5. **SQLite is canonical.** Structured state belongs in one local SQLite database.
   Large immutable evidence may live in a content-addressed object store beside it.
6. **Epistemic types remain distinct.** Resources, observations, evidence, derived
   claims, and operations are not interchangeable records.
7. **Unknown is not absent.** Missing observation produces an explicit limitation, not
   an invented negative fact.
8. **History keeps its meaning.** Awareness revisions and evidence are immutable once
   addressed. Later reality produces later records.
9. **Handles round-trip.** Important objects have stable identifiers such as
   `path:src/app.py`, `evidence:<digest>`, and `operation:<id>`.
10. **Measured reality outranks self-report.** A mutating tool's account will eventually
    be compared with independently observed target changes.

## Layering and direction

```text
Human or agent
      |
CLI / MCP / future panel
      |
Control plane
      |
Tool host ---- local inference (later)
      |
Project substrate
      |
Target
```

Adapters translate protocols. The control plane owns discovery, contracts,
containment, authority, process execution, and eventually previews, measurement,
audit, cancellation, and invalidation. Tools perform capabilities. The substrate owns
durable truth. Dependencies point downward.

No projection owns a scanner, editor, inference backend, or alternate mutation path.
A useful behavior must be a tool, a composition, substrate/query behavior, or
projection behavior.

## Installed instance

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

`instance.json` establishes continuity and location. Its UUID identifies the durable
instance; `target_relation` resolves from the instance directory to its direct parent.
An absent manifest means "not an instance." A present malformed manifest is a hard
error and never falls through to inference.

The target has no pointer, configuration edit, ignore-file edit, external registry, or
required external identity state.

## Durable substrate

The eventual canonical record classes are:

- **Resources:** target entities and their versions.
- **Observations:** deterministic statements made by named producers.
- **Evidence:** immutable support, addressed by digest.
- **Derived claims:** interpretations linked to supporting observations and evidence,
  including model and method when inference is model-produced.
- **Operations and memory:** invocations, proposals, decisions, mutations,
  verifications, journal entries, and unresolved items.

SQLite stores identity and relationships. JSON columns may hold variable domain data;
identity and provenance remain relational. Full-text and semantic indexes are derived
retrieval aids, never canonical truth.

## Tool and control-plane contract

Each `tools/<id>/manifest.json` declares its identifier, purpose, authority, schemas,
read/write domains, applicability, path arguments, and executable entry point.
Discovery reads these manifests directly. There is no authoritative generated catalog.

The control plane:

1. resolves the canonical instance context;
2. discovers and validates the manifest;
3. validates caller authority and input shape;
4. resolves declared paths within their allowed roots;
5. transports the resolved context to a child process;
6. requires a structured JSON result matching the output contract;
7. returns a common envelope to every adapter.

Environment variables may be ordinary process input, but they are never instance
identity. Context is transported by the parent runtime after structural resolution.

## Work loop

The product grows toward:

```text
observe -> investigate -> propose -> preview -> diff -> approve -> apply
        -> measure -> verify -> refresh -> record
```

Approval must bind to the reviewed target state. Verification reports unavailable when
the target has no native verifier; it never invents PASS.

## Anti-goals

The initial product does not include an IDE, large GUI, autonomous agent framework,
graph database, vector-first store, plugin marketplace, workflow language, universal
ontology, projection-specific backends, or a broad catalog of speculative tools.

Domain-neutral mechanics come first. Python, web, documents, records, and data depth
will arrive as stateless cartridges only after use demonstrates the need.

## Initial acceptance

Phase 1 is accepted when fixtures prove that a normal or empty target can be attached,
re-entered after process restart and relocation, inspected through discovered tools and
one CLI/control-plane path, protected from path escape, and left unchanged outside the
single `.sidecar` directory except for an explicitly authorized work product.
