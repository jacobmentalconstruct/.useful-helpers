# Product Charter

Status: **APPROVED FOR PROTOTYPE CONSTRUCTION**

This document owns what Sidecar Workbench is, its consumer-visible invariants,
prototype acceptance conditions, product boundary, and global product non-goals. It
does not own builder workflow, tranche mechanics, implementation status, or project
closure.

## Constitutional statement

> A self-contained local instrument attached to one directory. It observes that
> directory, builds durable evidence-backed knowledge about it, exposes deterministic
> capabilities over it, and allows humans or agents to make governed changes through
> the same control plane.

The experiential objective is **a calm workbench with receipts**. The product is a
local project instrumentation system. AI is a consumer and possible source of derived
claims, never canonical truth or authority.

## Product invariants

1. One sidecar belongs to one target through structural, relative identity.
2. Instrument-owned footprint remains inside `.sidecar`; approved target work products
   remain when the instrument is removed.
3. CLI, MCP, and future projections share one governed invocation boundary.
4. Deterministic manifest-driven tools are the hands; projections own no private backend.
5. SQLite is canonical structured state; immutable large evidence may use a local
   content-addressed object store.
6. Resources, observations, evidence, derived claims, and operations remain
   epistemically distinct and provenance-linked.
7. Unobserved means unknown, never absent.
8. Awareness revisions and evidence retain their historical meaning.
9. Important objects have resolvable canonical handles.
10. Independently measured reality outranks a mutating tool's self-report.

## Product topology

```text
human / external agent
          |
     CLI / MCP adapters
          |
      control plane
          |
 deterministic tools + subordinate local inference
          |
  durable project substrate
          |
         target
```

The composition root wires these owners. The control plane coordinates cross-domain
work. Domain managers own coherent policy domains only when those domains exist.
Components are cohesive deterministic mechanisms. Machines are reserved for genuine
stateful lifecycles such as preview-to-apply or awareness revision.

## Product and factory boundary

`product/` is the positive installed-runtime source boundary. Runtime identity,
orientation, control-plane behavior, substrate behavior, adapters, and installed
capabilities belong there. Installed product code may not import `factory/`, `.builder/`,
or `tests/`.

`factory/` owns manufacture, installation, packaging, update assembly, and release only.
Artifact format is deliberately undecided. Release composition must positively select
product surfaces; it must not ship construction history by subtracting an ever-growing
denylist.

`.builder/journal/` is immutable construction history for this repository. The product
journal is fresh runtime project memory inside an installed sidecar and begins empty.
Neither journal stores or projects the other.

## Prototype acceptance conditions

- **P1 Lifecycle:** Attach one structurally identified sidecar to an arbitrary target;
  relocate it with the target; minimally update compatible code while preserving UUID
  and durable state; remove the instrument cleanly.
- **P2 Governed hands:** Discover and invoke deterministic tools through one authority,
  contract, containment, process, attribution, and result-validation boundary.
- **P3 Durable memory:** Persist operations, evidence, a blank-start product journal,
  resources, versions, observations, claims, and typed provenance relations in the
  local substrate/object store.
- **P4 Orientation:** Produce compact immutable awareness revisions with freshness,
  limitations, provenance, and stable round-tripping handles; unknown remains explicit.
- **P5 Governed mutation:** Preview and diff before approval, bind approval to reviewed
  reality, reject stale previews, measure actual changed paths, verify honestly, refresh,
  and retain the complete historical chain.
- **P6 Projection parity:** CLI and MCP expose the same catalog, control plane, authority,
  substrate, awareness, operations, and journal rather than parallel implementations.
- **P7 Truthful breadth:** Degrade usefully across a substantial software target, a
  mixed records/document target, and an empty or nascent target; calibrate discriminating
  behavior with separate known-answer fixtures.
- **P8 Releasability:** One sealed release artifact passes the consumer walk on clean
  Windows and Linux environments and contains no construction history, parent lineage,
  sandbox paths, temporary fixtures, or construction state. macOS is UNSCORED.

## Acceptance walk

Install the same artifact into each target class; observe; orient; resolve handles;
drill into evidence; propose, preview, and approve one exact change; apply and
independently measure it; verify or report unavailable; refresh while preserving the
prior revision; inspect the same world through CLI and MCP; perform a compatible update;
remove the instrument; inspect the target and artifact boundaries.

## Product STOP

Product STOP is satisfied only when P1-P8 are each supported by their declared
consumer-visible evidence. Missing or inapplicable evidence is UNSCORED, not PASS.
Product STOP does not by itself close construction; project closure is owned by the
Tranche Plan.

## Global non-goals

The prototype excludes a GUI/IDE, autonomous or multi-agent runtime, workflow language,
graph database, vector-centered authority, universal plugin system, marketplace, remote
service, global sidecar registry, broad local-model platform, every parent capability,
every possible cartridge, speculative extension infrastructure, and optimization without
measurement.
