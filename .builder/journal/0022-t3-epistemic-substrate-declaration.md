# T3 Epistemic Substrate Declaration

- Date: 2026-08-27
- Tranche: T3 Epistemic Substrate
- Entry class: tranche declaration
- Transition: PROVISIONAL -> DECLARED
- Preconditions: T0 PARKED; T1 PARKED; T2 PARKED in `0021-t2-park.md`
- Implementation authorized by this entry: no
- T3 outcome PARKED: no
- T4 started: no

## Declared outcome

T3 will establish the first durable epistemic substrate for a target: resources,
resource versions, deterministic observations, immutable epistemic evidence, derived
claims, and typed provenance relations persist as distinct record classes without
collapsing into operational receipts, operational artifacts, App Journal entries, or
awareness projections.

The user-visible result is that a returning human or command-capable agent can ask:

- what target resources were actually observed;
- which resource versions were seen and whether historical versions remain;
- what deterministic observations were produced;
- what immutable evidence supports those observations;
- which derived claims exist and why they are not facts; and
- how to traverse from a claim to observations, evidence, and target resources.

## Remeasured parked T2 substrate

The repository is clean on branch `codex/t1-mechanical-host` at commit `1e8c188` except
for ignored `_projectmapper/` file-dump output locked by an external process. T2 is
operator-approved and parked. No active tranche exists.

Current runtime storage is `DATABASE_SCHEMA_VERSION = 2`. `product/core/storage.py`
creates exactly these persistent tables:

- `instances`
- `operational_artifacts`
- `operation_receipts`
- `app_journal_entries`
- `app_journal_links`

Source and grep measurements show no persistent T3 tables in product storage:
`resources`, `resource_versions`, `observations`, `epistemic_evidence`, `claims`,
`relations`, and `awareness_revisions` are absent as storage tables. Existing resource
language appears only in transient inventory tool output and tests.

T2 runtime records remain owned by `product/core/runtime_records.py`; the App Journal
remains owned by `product/core/app_journal.py`. Operational artifacts are evidence of
runtime operations only. They are not the T3 epistemic evidence owner for observations or
claims.

## Ownership model

T3 will add one small substrate owner under `product/core/` unless implementation
evidence proves a split is necessary. The expected owner is `product/core/substrate.py`.
`product/core/storage.py` will own only schema migration mechanics, not substrate
semantics. CLI commands may expose substrate records, but CLI must not scan the target or
create private epistemic state.

Record ownership is:

- **Resources:** target things observed by the substrate, initially files,
  directories, and supported symlink records. Resource handles are target-relative, for
  example `path:docs/readme.txt` and `path:docs/`. T3 does not solve rename identity;
  path handles are the initial canonical resource identity.
- **Resource versions:** immutable observations of a resource at a point in time. File
  versions include content hash, size, mtime, kind, and evidence link. Directory and
  symlink versions include the available deterministic metadata. A changed file creates
  a new version; it must not overwrite the prior version.
- **Observations:** deterministic statements produced by named substrate contributors,
  such as `resource_inventory`, `file_hash`, `text_stats`, or `resource_missing`.
  Observations carry producer, observed_at, subject handle, observation type, structured
  data, and supporting evidence. Observations are facts only about what the producer
  actually measured.
- **Epistemic evidence:** immutable support for resource versions, observations, or
  claims. Evidence identifiers are content-addressed, for example `evidence:<sha256>`.
  T3 may store small JSON bodies in SQLite and/or immutable blobs beneath
  `.sidecar/state/objects/`; either way the digest is authoritative. This evidence owner
  is distinct from T2 `operational_artifacts`.
- **Derived claims:** interpretations computed from observations, not deterministic
  facts. Claims carry claim type, statement, derivation method, confidence, optional
  model metadata, structured data, and provenance relations to supporting observations.
  T3 may create only thin deterministic claims such as "target appears empty" or "target
  contains text-like files" when directly supported. It must not invent richness.
- **Provenance relations:** typed edges between canonical records. Required relation
  predicates include `concerns`, `version_of`, `supported_by`, `derived_from`, and
  `supersedes`. Relations are the initial graph layer over SQLite rows; T3 must not add a
  graph database.

## Dependency and entrance model

T3 substrate behavior belongs below awareness and above the target. It may use the
governed host, existing manifest-defined tools, and T2 receipts for runtime events, but
the substrate records remain their own semantic objects.

Expected product flow:

```text
CLI substrate command
  -> governed host / trusted state owner
  -> substrate owner
  -> existing mechanical tools or deterministic local inspection
  -> resources / versions / observations / evidence / claims / relations
```

The exact implementation may choose whether target inspection occurs by invoking the
existing `inventory` and `hash_file` tools through the host or by a small deterministic
host-owned contributor. In either case, target binding, containment, trusted state, and
excluded `.sidecar` subtree behavior remain host-owned. Product tools must not import
the substrate upward or become substrate-specific tools merely to persist observations.

T3 CLI commands should be minimal and consumer-visible. Expected commands are roughly:

- `observe` or `substrate refresh` to create a new substrate observation pass;
- `resources list/read`;
- `versions list/read`;
- `observations list/read`;
- `evidence read`;
- `claims list/read`; and
- `trace <handle>` for provenance traversal.

Naming may change during implementation if the simpler CLI grammar is clearer, but CLI
must remain an entrance, not a capability owner.

## Scope

T3 is in scope to:

- advance SQLite to the next schema version with distinct epistemic substrate tables;
- add immutable evidence storage for observation support, using content-addressed IDs;
- persist resources and immutable resource versions from explicit observation passes;
- record deterministic observations with direct evidence links;
- record thin derived claims only where observations support them;
- record typed provenance relations that allow claim -> observation -> evidence ->
  resource traversal;
- expose minimal CLI commands to refresh and inspect substrate records;
- preserve T2 receipts, operational artifacts, App Journal memory, and their owners;
- prove fresh installs start with blank epistemic substrate state;
- prove empty targets produce truthful thin substrate records without fake richness;
- prove non-empty targets persist resource/version/observation/evidence records and
  handles that round-trip through CLI;
- prove historical versions remain inspectable after a target file changes and a later
  refresh occurs;
- preserve T1 mechanical dependency boundaries; and
- add a T3 gate under `.builder/gates/` with discriminating evidence.

## Non-goals

T3 does not implement awareness revisions, model-facing summaries, "current orientation"
projections, freshness scoring, or awareness handles beyond substrate record handles.
Those belong to T4.

T3 does not implement preview-first mutation, approval binding, stale-preview refusal,
changed-path measurement, target-native verification workflow, or refresh-after-mutation
as a governed work loop. Those belong to T5.

T3 does not add MCP, GUI, autonomous agents, local AI, embeddings, vector retrieval,
graph database, domain cartridges, document/PDF semantic parsing, release packaging,
update proof, removal proof, or standalone extraction of a Tool Pack, App Journal, or
substrate library.

T3 does not make runtime operational artifacts the epistemic evidence store. It may link
to operation receipts where useful, but epistemic evidence has its own identity and
meaning. A `read_file` receipt is not an observation; an App Journal decision is not a
claim; a claim is not an awareness finding.

## Expected changed surfaces

- `product/core/constants.py`: advance `DATABASE_SCHEMA_VERSION`.
- `product/core/storage.py`: add minimal schema migration for T3 tables.
- `product/core/substrate.py` or similarly named owner: own resources, versions,
  observations, evidence, claims, relations, and trace semantics.
- `product/core/cli.py`: expose minimal substrate refresh and inspection commands.
- `product/core/control.py`: only if host-owned invocation or attribution needs a small
  composition point for substrate refresh.
- `tests/test_t3_epistemic_substrate.py`: focused product fixtures.
- `.builder/gates/t3_epistemic_substrate.py`: sole T3 closure gate.
- `docs/ARCHITECTURE.md`, `.builder/TRANCHE_PLAN.md`, `.builder/CURRENT_STATE.md`, and
  later T3 journal entries: review synchronization only.

T3 must not modify `product/tools/*` unless implementation evidence shows a manifest or
mechanical contract defect that blocks substrate observation. Cosmetic re-homing is not
in scope.

## Completion evidence declared before implementation

The eventual T3 gate must prove the following through product tests, structural checks,
consumer CLI exercises, and discrimination witnesses:

1. A fresh attach starts with blank epistemic substrate records while T2 runtime receipt
   and App Journal blank-start behavior remains intact.
2. An explicit observe/refresh action on an empty target succeeds and records only thin,
   truthful facts. Empty means observed empty; unobserved remains unknown.
3. An explicit observe/refresh action on a non-empty target records resources excluding
   `.sidecar`, creates immutable resource versions, and stores content-addressed
   evidence for deterministic observations.
4. A changed file followed by a later refresh creates a new resource version while the
   prior version and its evidence remain inspectable.
5. Observations cannot exist without supporting epistemic evidence and a concerned
   resource or observation subject where applicable.
6. Claims cannot exist without derived-from provenance to observations. Claims are
   identifiable as derived and do not silently become deterministic facts.
7. Provenance traversal can resolve claim -> observation -> evidence -> resource using
   canonical handles.
8. Epistemic evidence is distinct from T2 operational artifacts. T3 must not store
   observation support by writing to `operational_artifacts`, and T2 runtime artifacts
   must not appear as observation evidence unless explicitly linked as external support.
9. App Journal entries remain deliberate work memory and are not automatically generated
   by substrate observation.
10. Operational receipts may record the observation command as a runtime event, but
    substrate resources, observations, evidence, claims, and relations do not collapse
    into receipt rows.
11. The T1 mechanical dependency boundary remains intact: `product/tools/*` may import
    `core.tool_runtime` but no other `core.*`, and `core.tool_runtime` imports no higher
    Sidecar `core.*`.
12. T3 introduces no `awareness_revisions`, embeddings, vector store, MCP, GUI, or
    domain-cartridge authority.
13. Canonical pytest, Ruff, the T3 gate, and relevant cumulative T0/T1/T2 checks pass
    from the committed review candidate.

The gate must include discrimination against plausible wrong implementations, including:

- collapsing `resources` and `resource_versions` into one mutable row;
- storing epistemic evidence in `operational_artifacts`;
- accepting observations without evidence;
- accepting claims without `derived_from` observation provenance;
- creating App Journal entries automatically during observation;
- overwriting an old version when target content changes; and
- introducing awareness tables or awareness-like projection state in T3.

## Ordered implementation plan

1. Add focused failing product tests for blank substrate state, empty target refresh,
   non-empty target refresh, version history, evidence immutability, claim provenance,
   trace traversal, T2 separation, and no automatic App Journal projection.
2. Add minimal T3 schema migration and typed identifiers for resources, resource
   versions, observations, epistemic evidence, claims, and relations.
3. Add the small substrate owner with append/lookup/list/trace operations and
   content-addressed evidence persistence.
4. Add an explicit substrate refresh path that uses trusted host context and excludes
   `.sidecar`.
5. Add minimal CLI inspection commands for resources, versions, observations, evidence,
   claims, and trace.
6. Add thin deterministic claim generation only where direct observations support it.
7. Implement the T3 gate and its discrimination witness.
8. Consolidate for ownership separation, path containment, schema migration safety,
   immutable evidence/version behavior, blank-state behavior, generated debris, naming,
   and dependency direction.
9. Run focused T3 tests, canonical pytest, Ruff, T3 gate, relevant cumulative T0/T1/T2
   checks, and one discovery search for terminology collapse across receipts, App
   Journal, evidence, claims, and awareness.
10. Synchronize review documentation and submit T3 AWAITING_APPROVAL without parking T3
    or beginning T4.

## Risks and decisions held for implementation evidence

- The first resource identity strategy is path-based. Rename tracking is explicitly out
  of T3 unless tests show that path identity makes basic substrate behavior misleading.
- Evidence storage may begin as SQLite JSON rows plus digest or as digest-addressed
  object files under `.sidecar/state/objects/`. The implementation must choose the
  smallest durable form that proves immutability and retrieval without confusing it with
  T2 operational artifacts.
- Running existing tools through `ControlPlane.invoke()` may produce T2 receipts for an
  observation pass. That is acceptable if substrate records remain distinct and if the
  receipt is not treated as the observation itself.
- Claims should remain sparse. If a target provides too little evidence, T3 should record
  limitations or no claim instead of manufacturing a richer project story.
- Schema constraints may need to balance SQLite simplicity with discriminating tests for
  provenance. T3 should not build a large ontology or graph database to prove the first
  traversal.

## Review position

This declaration is submitted for operator review. T3 is DECLARED, not IMPLEMENTING. No
product source, product tests, manifests, runtime schema, or T3 gate has been changed by
this entry. Implementation must wait for explicit operator approval of this declaration.
