# T4 Awareness Declaration

- Date: 2026-08-27
- Tranche: T4 Awareness
- Entry class: tranche declaration
- Transition: PROVISIONAL -> DECLARED
- Preconditions: T0 PARKED; T1 PARKED; T2 PARKED; T3 PARKED in `0025-t3-park.md`
- Implementation authorized by this entry: no
- T4 outcome PARKED: no
- T5 started: no

## Process walk

ORIENT measured the live repository rather than relying on memory. The working tree was
clean at commit `081ae5ea8d6451639fd8e1ac7deabbda3c5f8838`, T3 was PARKED, P3 was
credited, P4-P8 were UNSCORED, and T4 had not begun. The controlling authorities read
for this declaration were `.builder/BCC.md`, `.builder/TRANCHE_PROTOCOL.md`,
`.builder/TRANCHE_PLAN.md`, `.builder/CURRENT_STATE.md`, `docs/PRODUCT_CHARTER.md`,
`docs/ARCHITECTURE.md`, and the parked T3 declaration/park entries.

DECLARE is this entry. EXECUTE must wait for explicit operator approval.

## Declared outcome

T4 will establish compact immutable awareness revisions over the parked T3 epistemic
substrate. Awareness is a projection and orientation layer: it references resources,
resource versions, observations, epistemic evidence, derived claims, and provenance
relations through stable handles, but it does not own or rewrite those source records.

The user-visible result is that a returning human or command-capable agent can ask:

- what the sidecar currently thinks it is attached to;
- which substrate revision or refresh the orientation is based on;
- which compact findings and handles are useful starting points;
- which limitations and unknowns constrain the projection;
- whether awareness is fresh relative to the currently observed target signature; and
- how to drill from an awareness item back to substrate claims, observations, evidence,
  and resources.

## Remeasured parked T3 substrate

The repository is clean on branch `codex/t1-mechanical-host` at commit
`081ae5ea8d6451639fd8e1ac7deabbda3c5f8838`. T3 is operator-approved and parked. P3 is
credited through parked T2 runtime memory and parked T3 epistemic substrate. No T4
implementation exists.

Current runtime storage is `DATABASE_SCHEMA_VERSION = 3`. `product/core/storage.py`
creates these T3 epistemic tables:

- `resources`
- `resource_versions`
- `observations`
- `epistemic_evidence`
- `claims`
- `relations`

`product/core/substrate.py` owns explicit refresh, resource/version lookup,
deterministic observation records, content-addressed epistemic evidence, derived claims,
typed provenance relations, and trace traversal. It also records explicit limitations
and the principle that anything not observed by a refresh remains unknown.

Source measurements show no `awareness_revisions` table, no awareness module, no
awareness CLI command, no vector index, no MCP entrance, no GUI, and no domain cartridge
authority. Awareness language currently appears only in the Charter, Architecture,
Plan, parked tranche history, and explicit T3 no-awareness checks.

## Ownership model

T4 will add one awareness owner under `product/core/` unless implementation evidence
proves a split is necessary. The expected owner is `product/core/awareness.py`.
`product/core/storage.py` will own schema migration mechanics only. CLI may expose
awareness commands, but CLI must not compose private awareness projections.

Record ownership is:

- **Awareness revisions:** immutable projection envelopes. A revision records a stable
  revision identifier, creation time, basis signature, source substrate counts or
  handles, compact summary fields, findings, limitations, unknowns, and provenance
  references. A revision must not be overwritten after creation.
- **Awareness items/findings:** compact user/model-facing orientation items inside or
  linked to a revision. They carry type, title/statement, priority or confidence where
  useful, and handles back to T3 claims, observations, evidence, resources, or versions.
- **Freshness:** an assessment comparing the revision basis with a current cheap target
  signature and/or latest substrate refresh state. Freshness may be `current`, `stale`,
  or `unknown`, but must not silently pass when no basis exists.
- **Limitations and unknowns:** explicit projection facts. Empty or thin substrate
  evidence yields thin awareness; unobserved material remains unknown, not absent.
- **Handles:** initial awareness directly exposes and verifies T3-owned handles:
  `path:...`, `version:...`, `observation:...`, `evidence:...`, `claim:...`, and
  provenance relation references. T2 receipt or App Journal information is reachable
  only if explicitly mediated by an owning provenance layer rather than independently
  consumed by T4. T4 introduces one canonical `awareness:<digest-or-id>` handle form for
  its own records.

Awareness does not own resources, versions, observations, epistemic evidence, claims,
relations, operational receipts, operational artifacts, App Journal entries, mechanical
tool contracts, or construction history.

## Dependency and entrance model

T4 awareness sits above the T3 substrate and below CLI/MCP projections:

```text
CLI awareness command
  -> governed host / trusted state owner
  -> awareness owner
  -> T3 substrate queries and provenance handles
  -> immutable awareness revision / compact projection
```

Awareness may query T3 substrate records only through `product/core/substrate.py` APIs
and handles. It may use verified storage for awareness-owned tables. It must not scan
the target independently in a way that bypasses the substrate owner. It may compute a
cheap freshness signature from host-known target metadata if needed, but freshness must
remain a projection status, not a replacement substrate observation. A direct target
signature used by T4 is an ephemeral invalidation/freshness signal only. It must not
create awareness findings or substrate facts, and lack of a comparable basis yields
`unknown`.

The CLI remains an entrance. MCP remains absent and removable. Mechanical tools and App
Journal semantics must not import or depend on awareness.

## Scope

T4 is in scope to:

- advance SQLite to the next schema version with distinct awareness revision storage;
- add a small awareness owner that composes compact immutable projections from T3
  substrate records;
- expose minimal CLI commands such as `awareness refresh`, `awareness current`,
  `awareness revisions`, and `awareness drill` or equivalent;
- create immutable awareness revision identifiers that remain inspectable after later
  refreshes;
- include compact target orientation derived from substrate resources/claims and their
  handles;
- include explicit limitations and unknowns, especially for empty, stale, or thinly
  observed targets;
- include freshness state based on a declared basis, with honest `unknown` where
  freshness cannot be established;
- prove awareness references source handles and provenance rather than duplicating or
  mutating T3 records;
- prove empty targets produce compact truthful orientation without fake richness;
- prove stale awareness is detectable after target change before a new substrate/awareness
  refresh;
- preserve T1 mechanical dependency boundaries, T2 runtime-memory separation, and T3
  substrate ownership; and
- add a T4 gate under `.builder/gates/` with discriminating evidence.

## Non-goals

T4 does not implement preview-first mutation, approval binding, stale-preview refusal,
changed-path measurement, target-native verification workflow, apply/refresh work-loop
governance, or mutation-linked App Journal decisions. Those belong to T5.

T4 does not add MCP, GUI, autonomous agents, local AI, embeddings, vector retrieval,
domain cartridges, document/PDF semantic parsing, release packaging, update proof,
removal proof, standalone extraction, or a broad semantic ontology.

T4 does not make awareness the canonical store for substrate facts. Awareness revisions
are projections over T3 records. A claim remains a claim, an observation remains an
observation, evidence remains evidence, a receipt remains a receipt, and a journal entry
remains work memory.

T4 does not require rich awareness for all targets. Empty or nascent targets may produce
minimal awareness with limitations and unknowns, and that is success.

## Expected changed surfaces

- `product/core/constants.py`: advance `DATABASE_SCHEMA_VERSION`.
- `product/core/storage.py`: add minimal schema migration for awareness revision
  storage.
- `product/core/awareness.py` or similarly named owner: own awareness projection,
  revision identity, freshness, limitation/unknown projection, and drill mapping.
- `product/core/cli.py`: expose minimal awareness refresh/current/revision/drill
  commands.
- `tests/test_t4_awareness.py`: focused product fixtures.
- `.builder/gates/t4_awareness.py`: sole T4 closure gate.
- `.builder/gates/t0_bootstrap.py`, `.builder/gates/t2_runtime_receipts_work_memory.py`,
  or `.builder/gates/t3_epistemic_substrate.py`: only if cumulative gates need narrow
  lifecycle or T4-started vocabulary updates.
- `docs/ARCHITECTURE.md`, `.builder/TRANCHE_PLAN.md`, `.builder/CURRENT_STATE.md`,
  `README.md`, and later T4 journal entries: review synchronization only.

T4 should not modify `product/tools/*`, `product/core/tool_runtime.py`,
`product/core/app_journal.py`, or `product/core/runtime_records.py` unless a measured
defect blocks awareness while preserving the approved lower-layer boundaries.

## Completion evidence declared before implementation

The eventual T4 gate must prove the following through product tests, CLI exercises,
structural checks, and discrimination witnesses:

1. A fresh attach starts with no awareness revisions while T2 runtime memory and T3
   substrate state remain blank until their explicit actions run.
2. Awareness cannot fabricate a rich orientation without substrate support. On a fresh
   unobserved target, awareness reports missing or unknown basis rather than pretending
   absence was observed.
3. After substrate refresh on an empty target, awareness creates a compact immutable
   revision that reports observed empty/thin orientation, explicit limitations, and
   unknowns.
4. After substrate refresh on a non-empty target, awareness creates a compact revision
   with stable handles that resolve through T3 substrate CLI/API back to resources,
   versions, observations, evidence, claims, and relations where applicable.
5. A later awareness refresh creates a new revision without overwriting the prior
   revision; the prior revision remains inspectable with its original basis and handles.
6. Freshness detects a target change or substrate-basis mismatch as `stale` or `unknown`
   before a new matching refresh, rather than silently reporting current.
7. Awareness drill resolves an awareness item or revision handle back to T3 provenance
   without copying T3 source records into awareness-owned authority.
8. Awareness storage remains distinct from T3 substrate tables, T2 operational artifacts,
   T2 receipts, and App Journal entries.
9. Awareness refresh does not automatically create App Journal entries and does not
   collapse into operation receipts. Receipts may record the CLI command as a runtime
   event, but the receipt is not the awareness revision.
10. Lower layers do not depend upward on awareness: mechanical tools, `core.tool_runtime`,
    App Journal, runtime records, and substrate do not import `core.awareness`.
11. T4 introduces no MCP, GUI, vector/embedding index, domain cartridge, mutation
    preview/apply loop, or target-native verification workflow.
12. Canonical pytest, Ruff, the T4 gate, and relevant cumulative T0/T1/T2/T3 checks pass
    from the committed review candidate.

The gate must include discrimination against plausible wrong implementations, including:

- overwriting an awareness revision in place;
- storing awareness findings as T3 claims or T2 operational artifacts;
- creating rich awareness when substrate basis is missing;
- reporting freshness as current after target content changes without a matching refresh;
- allowing awareness handles that do not resolve through their owning source layer;
- making substrate, App Journal, receipts, mechanical tools, or the shared tool runtime
  import awareness; and
- introducing MCP, GUI, vector, or mutation-governance surfaces in T4.

## Ordered implementation plan

1. Add focused failing product tests for blank awareness state, unobserved target
   unknown-basis behavior, empty-target awareness, non-empty awareness with resolvable
   handles, immutable revision history, stale/unknown freshness, drill traversal, and
   state-owner separation.
2. Add minimal schema migration for awareness revisions and any required child item
   storage.
3. Add the awareness owner with revision composition, compact projection, freshness,
   limitations/unknowns, handle validation, revision lookup, and drill behavior.
4. Add minimal CLI awareness commands through the existing CLI entrance.
5. Ensure awareness consumes T3 substrate APIs/handles and does not mutate or become the
   source owner for substrate records.
6. Implement the T4 gate and discrimination witness.
7. Consolidate for ownership separation, immutable revision behavior, stale freshness,
   blank-state behavior, generated debris, naming, path/context safety, and dependency
   direction.
8. Run focused T4 tests, canonical pytest, Ruff, T4 gate, relevant cumulative T0/T1/T2/T3
   checks, and one discovery search for terminology or storage collapse across
   awareness, substrate, receipts, App Journal, tools, MCP, GUI, and mutation workflow.
9. Synchronize review documentation and submit T4 AWAITING_APPROVAL without parking T4,
   claiming P4 credit, or beginning T5.

## Risks and decisions held for implementation evidence

- Revision identity may be content-addressed or deterministic over the projection body.
  T4 should choose the smallest stable form that preserves immutable historical meaning.
- Freshness should be useful without becoming a full file-watcher or incremental
  invalidation system. A cheap target signature plus substrate-basis comparison may be
  enough for prototype P4.
- Awareness must stay compact. If a target is large, T4 should expose useful handles and
  limitations rather than dumping the substrate graph.
- Empty-target awareness must be truthful. It should orient around what was observed and
  what remains unknown, not manufacture a project story.
- Handle validation can begin with path/resource/version/observation/evidence/claim
  handles already owned by T3. T4 should not invent broad natural-language resolution.
- The first awareness projection may use deterministic rules only. Local AI and semantic
  synthesis remain out of scope.

## Review position

This declaration is submitted for operator review. T4 is DECLARED, not IMPLEMENTING. No
product source, product tests, manifests, runtime schema, or T4 gate has been changed by
this entry. Implementation must wait for explicit operator approval of this declaration.
