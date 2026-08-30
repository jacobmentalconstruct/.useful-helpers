# Architecture

Status: **T6 AWAITING_APPROVAL IMPLEMENTATION MAP**

## Charter relationship

The [Product Charter](PRODUCT_CHARTER.md) owns product identity, method/product boundary,
invariants, topology and dependency direction, runtime state classes, P1-P8, the
acceptance walk, Product STOP, and product non-goals. This document does not redefine
those facts. It maps the implementation currently present in the repository to the
Charter responsibilities it is intended to realize. T1, T2, T3, and T4 are parked by
operator approval. T5 Governed Mutation Loop is parked by operator approval and P5 is
credited. T6 Removable MCP Entrance is implemented and awaiting operator approval; P6 is
not credited. Product STOP remains incomplete because P6-P8 are unscored.

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
- `product/core/substrate.py` owns T3 resources, resource versions, deterministic
  observations, epistemic evidence, derived claims, provenance relations, and trace
  traversal.
- `product/core/awareness.py` owns T4 compact immutable awareness revisions, awareness
  items, freshness status, limitation/unknown projection, and drill mapping over T3
  substrate handles.
- `product/core/mutation.py` owns the T5 governed mutation loop records and policy:
  preview, approval binding, stale refusal, apply coordination, changed-path
  measurement, verification status, refresh links, and mutation history.
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
2. bootstrap SQLite state and verify that the persisted instance UUID agrees with
   `instance.json`;
3. establish a durable operation receipt for the requested invocation after trusted
   state ownership exists;
4. validate client, authority, and input shape;
5. discover and validate the requested manifest;
6. compare requested and declared authority;
7. resolve declared target or instance paths through containment;
8. shape product-neutral context from the already validated host facts;
9. invoke the tool in a child Python process with serialized arguments and context;
10. validate the structured result;
11. record a durable operational artifact supporting the receipt in the same persistence
    operation that completes the receipt; and
12. return a common envelope containing receipt and artifact identifiers when recording
    succeeds.

The host resolves complete instance identity and containment before dispatch. The JSON
request transports only already-resolved mechanical facts; environment configuration
locates the installed Python modules but does not carry project identity.

If receipt creation fails, the control plane reports `receipt_persistence_failed` with
`durably_governed = false`. That failure happens before child-process launch, so a
state-changing tool does not silently proceed as durably governed when the required
operation record cannot be established.

If receipt completion fails after a child process has already run, the control plane also
reports `receipt_persistence_failed` with `durably_governed = false`. Artifact insertion
and receipt completion occur in one SQLite transaction, so completion failure must not
leave an orphan artifact whose envelope claims durable governance.

T5 mutation governance sits above this invocation path and uses it for approved apply.
T2 did not credit preview/apply governance, stale approval binding, mutation
measurement, target-native verification workflow, refresh, cancellation, or invalidation;
T5 parks the bounded preview/apply portion by operator approval and P5 credit.

## Current substrate implementation

The current foundation for Charter product invariants 6 and 7 is
`.sidecar/state/workbench.sqlite3`. `product/core/storage.py` enables foreign keys, WAL,
and full synchronous writes; applies `PRAGMA user_version` migrations; and stores one
instance row whose UUID must agree with `instance.json` on re-entry.

Every T2 runtime-memory entrance uses verified storage. `storage.connect()` delegates to
`storage.bootstrap()`, and `bootstrap()` rejects an existing database whose instance UUID
does not agree with `instance.json` before applying migrations. Receipts, artifacts, and
App Journal CLI commands therefore share the same state-owner check as the control plane.

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
epistemic evidence owner for target observations or claims.

Schema version 3 adds distinct T3 epistemic substrate tables:

- `resources` records target-relative resource handles such as `path:docs/readme.txt`.
- `resource_versions` records immutable resource versions linked to resources and
  epistemic evidence.
- `observations` records deterministic producer statements with structured data and
  evidence links.
- `epistemic_evidence` stores content-addressed JSON support for resource versions,
  observations, and claims.
- `claims` records derived interpretations with derivation method, confidence, and
  structured data.
- `relations` records typed provenance edges such as `version_of`, `supported_by`,
  `concerns`, and `derived_from`.

`product/core/substrate.py` performs explicit refreshes against trusted instance context,
excludes the `.sidecar` subtree, records path-based resource identity, and preserves
historical resource versions instead of overwriting them. It exposes a T3-owned current
awareness basis view for projection consumers: the latest coherent refresh basis,
resource handles current at that refresh, related claims, observations, evidence handles,
provenance handles, and a stable basis signature. It currently generates only thin
deterministic claims: observed empty target, or observed text-like files. Those are
derived claims, not awareness findings and not deterministic facts beyond their stated
support.

The database still does not implement semantic/vector indexes, domain cartridges, or a
graph database. The objects directory is created but has no accepted object-store
contract.

## Current awareness implementation

Schema version 4 adds distinct T4 awareness projection tables:

- `awareness_revisions` records immutable compact projection envelopes with an
  `awareness:` identifier, creation time, basis status/signature, target freshness
  signature, summary, limitations, unknowns, and source handles.
- `awareness_items` records compact findings inside an awareness revision with item
  type, title, statement, priority, T3 source handles, and provenance metadata.

`product/core/awareness.py` composes awareness revisions through the coherent current
basis exposed by `product/core/substrate.py` rather than querying T3-owned tables
directly or reading accumulated substrate history. It uses verified storage only for
awareness-owned tables. Its freshness baseline is the T3-observed target signature from
that basis; the live target signature is an ephemeral comparison signal that can mark a
revision `current`, `stale`, or `unknown`, but cannot create substrate facts or awareness
findings.

Awareness refresh on an unobserved target records an immutable revision with missing
basis, no findings, explicit limitations, and explicit unknowns. Awareness refresh after
a T3 substrate refresh records compact findings from only the latest coherent T3 basis,
so non-empty to empty, deletion, replacement, and similar transitions do not leak
historical substrate records into current orientation. Prior awareness revisions remain
inspectable after later refreshes. `awareness current` recomputes freshness against the
current target signature and can report `stale` after a target change independently of
the T5 mutation loop.

The CLI exposes `awareness status`, `awareness refresh`, `awareness current`,
`awareness revisions list/read`, and `awareness drill`. Drill resolves awareness items
back through T3 substrate APIs such as claim trace and resource lookup. Awareness does
not create App Journal entries, operational artifacts, or operation receipts for its
projection records.

## Current mutation implementation

Schema version 5 adds T5 mutation tables for previews, approvals, mutation records,
verifications, and typed mutation links. `product/core/mutation.py` is the semantic owner
of those records; T2 receipts/artifacts, T2 App Journal entries, T3 substrate records,
and T4 awareness records remain owned by their original modules.

The initial mutation surface is intentionally narrow: a reviewed `write_file` path. The
CLI exposes `mutation status`, `mutation preview-write`, `mutation approve`,
`mutation apply`, `mutation history`, and `mutation links`. Preview records the proposed
write, expected path set, payload digest, current awareness revision, T3 basis signature,
and target signature without changing the target or creating a control-plane receipt.
Approval binds to that exact preview digest and basis, and may optionally link to an
existing deliberate App Journal entry without creating one automatically.

Apply refuses before child launch when approval is missing, the caller-provided preview
does not match the approval, the target signature has changed since preview, or the
awareness/basis is stale. Successful apply routes the bounded write through the existing
control plane, then independently snapshots target files before and after to measure
changed paths rather than trusting the tool's self-report. Verification is recorded as
`unavailable` with the explicit statement that no target-native verification mechanism is
available; T5 does not invent PASS. A successful apply refreshes T3 substrate first and
then T4 awareness, preserving prior revisions and linking preview, approval, receipt,
artifact, verification, pre/post awareness, and optional journal records.

The child-process environment is allowlisted for explicit runtime needs and excludes
ambient project identity or operator secrets. This containment is scoped to the governed
host boundary; it does not turn mechanical tools into Sidecar-specific tools.

T5 does not implement MCP, GUI, local AI, embeddings, domain cartridges, release/update
or removal lifecycle, rollback, a workflow engine, autonomous planning, broad
software-project assumptions, or construction-role runtime concepts.

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
implementation state; Product STOP remains incomplete until P6-P8 are also proven.

## T2 review evidence

T2 product fixtures report that a fresh attach starts with blank runtime receipts,
operational artifacts, App Journal entries, and App Journal links. Successful reads,
authority refusals before child launch, malformed child JSON, child process failure, and
the existing immediate write route are recorded after state ownership is resolved. The
successful write fixture inspects the completed receipt and artifact rather than relying
only on the target file appearing.

Receipts and operational artifacts remain distinct from App Journal entries. Journal
entries are deliberate work-memory records with entry type and status, may link to
receipt or artifact identifiers, do not appear automatically after tool calls, can exist
in a fresh runtime with zero operation receipts, and remain available across process
restart/re-entry without awareness or MCP.

A failure-injection fixture adds a SQLite trigger that rejects receipt creation and then
attempts an apply-authority write. The control plane returns `receipt_persistence_failed`
with `durably_governed = false`, and the target file is not created. This proves the T2
failure invariant without implementing the later T5 preview/apply loop.

Additional failure-injection fixtures corrupt SQLite instance ownership and prove T2
receipt/artifact/journal CLI entrances refuse before reading, writing, or migrating that
state. A receipt-completion trigger proves finalization failure after a child write does
not leave an orphan operational artifact claiming durable governance.

Authoritative T2 gate evidence is recorded in journal entries `0020` and `0021`. Entry
`0021` records operator approval and parks T2. T2 parks the runtime receipts/artifacts
and App Journal portion of P3; P3 remains incomplete pending T3's epistemic substrate
outcome, and Product STOP remains incomplete.

## T3 review evidence

T3 product fixtures report that a fresh attach starts with blank resources, resource
versions, observations, epistemic evidence, claims, and relations while T2 receipts and
App Journal entries remain blank. Explicit substrate refresh on an empty target records a
thin truthful inventory observation and an observed-empty derived claim without fake
richness. Explicit refresh on a non-empty target records target resources while excluding
`.sidecar`, persists immutable resource versions, and stores content-addressed epistemic
evidence.

A changed-file fixture proves that a later refresh creates a new version while the prior
version and evidence remain inspectable. A trace fixture resolves a derived claim through
`derived_from`, `supported_by`, and `concerns` relations to observations, epistemic
evidence, and target resources. Separation fixtures prove substrate observation does not
create App Journal entries or T2 operational artifacts.

Authoritative T3 gate evidence is recorded by journal entry `0024`, and operator
approval plus terminal park is recorded by journal entry `0025`. T3 parks the epistemic
substrate portion of P3.

## T4 review evidence

T4 product fixtures report that fresh attach starts with blank awareness state while
runtime receipts and substrate records remain blank until explicit actions run.
Awareness refresh on an unobserved target reports missing basis and `unknown` freshness
without rich findings. Awareness refresh after an empty substrate refresh produces a
thin immutable revision with explicit unknowns and limitations. Awareness refresh after
a non-empty substrate refresh produces compact findings with T3 handles and explicit
limitations. T3-owned resource, version, observation, evidence, claim, and relation
handles emitted by awareness round-trip through substrate API/CLI read or trace
entrances.

The fixtures prove that later awareness refreshes create new revisions without
overwriting prior revisions, that `awareness current` reports `stale` after target
content changes without a matching refresh, and that awareness drill resolves through
T3 provenance rather than direct T3 table ownership. Additional adversarial fixtures
prove that a target mutation after T3 refresh but before T4 refresh cannot receive
`current`, and that a latest empty T3 refresh does not leak historical non-empty
resources or claims into current awareness orientation. Separation fixtures prove
awareness does not create T2 operational artifacts or App Journal entries.

Authoritative repaired T4 gate evidence is recorded by journal entry `0031`: run
`20260827T121444Z-3713df86` passed 13/13, including a behavioral basis/freshness witness.
Entry `0032` records subsequent Acceptance Auditor and Reviewer evidence recommending a
bounded return for observed awareness limitations, emitted `relation:` handle
round-tripping, and the noncanonical `awareness-item:` handle form. Entry `0034` records
the repaired acceptance candidate: run `20260828T111925Z-d9548015` passed 14/14 with a
handle/limitations witness. Entry `0035` records operator approval and parks T4. P4 is
credited. T5 is now parked by entry `0039`, and Product STOP remains incomplete because
P6-P8 are not yet credited.

## T5 review evidence

T5 product fixtures report that fresh attach starts with blank mutation state; previewing
a write records the reviewed change without applying it or creating a receipt; approval
binds to the exact preview digest and basis and can link to an existing App Journal
entry; missing approval, preview mismatch, stale target state, and stale awareness basis
refuse before child launch; successful apply routes through the existing governed host,
records a completed receipt/artifact, independently measures changed paths, records
honest unavailable verification, refreshes substrate then awareness, and links the
resulting records without collapsing their owners.

Additional fixtures prove the first T5 precondition: the storage migration branch stamps
the intermediate target version accurately. A child-process fixture proves the governed
host does not inherit ambient `SIDECAR_IDENTITY_*` or `OPERATOR_TOKEN` environment values
while still providing the runtime import path needed by mechanical tools. A non-software
target fixture proves the narrow mutation loop does not assume a software project and
does not create automatic App Journal entries.

Authoritative T5 review evidence is recorded by journal entry `0038`: run
`20260829T095546Z-e30c36d7` passed 13/13 from clean commit
`62e321e2abbe68da8693ca3562bbacafcf3ea5a1` with SHA-256
`2F1B92BA6337AC84C43FDC6FD1F4F0653BC2C4BEDBDD61A6D917F98DB03D7437`.
Cumulative T4/T3/T2/T1/T0 gates also passed after the authoritative T5 receipt was
preserved.
External Reviewer evidence at
`.builder/evidence/reviews/T5/20260829T104344Z-external-review.md` recommends APPROVE
CANDIDATE, PARKED status, and P5 credit. Entry `0039` records operator approval and
parks T5. P5 is credited; Product STOP remains incomplete because P6-P8 are unscored,
and T6 is now awaiting operator approval.

## T6 review evidence

T6 introduces `product/core/mcp.py` as a removable stdio JSON-RPC entrance and
`product/core/host.py` as the shared host-status owner consumed by CLI and MCP. MCP
tool discovery is projected from the existing registry and owner APIs. MCP calls to
manifest tools route through the existing `ControlPlane`; MCP read/list calls for status,
receipts, App Journal, substrate, awareness, and mutation state call the owning product
modules rather than direct tables or private backends.

The CLI imports MCP lazily only when the `mcp` subcommand is invoked. Focused fixtures
prove fresh attach works before MCP is used, MCP initialization and tool discovery
derive from the same host catalog, an MCP `read_file` call records a governed receipt
with client `mcp`, MCP and CLI observe the same durable state across re-entry, malformed
requests fail truthfully, and removing the MCP adapter leaves status, tool discovery, and
governed CLI tool calls usable.

The cumulative T3 and T5 gates were narrowed to preserve their original tranche
boundaries after T6: T3 still forbids substrate/storage MCP ownership, and T5 still
forbids mutation/control surfaces from growing MCP behavior, while allowing the later
T6 adapter and CLI entrance to exist. The external T6 review then returned the candidate
for bounded T6 repairs: the missing `0042` submission record, MCP authority/timeout
contract mismatch, removed-adapter CLI error, and notification lifecycle handling.

Authoritative T6 review evidence is recorded by journal entry `0042`: T6 gate run
`20260830T101453Z-956b023b` passed 11/11. Cumulative T5/T4/T3/T2/T1/T0 gates passed with
receipts `20260830T101603Z-967e76c8`, `20260830T101728Z-3e23e4f5`,
`20260830T101835Z-a4bbaa7a`, `20260830T101945Z-42392a2b`,
`20260830T102005Z-8c3388b0`, and `20260830T102107Z-bdc96082`. T6 is awaiting approval;
P6 remains uncredited.
