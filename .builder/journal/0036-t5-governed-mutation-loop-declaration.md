# 0036 - T5 Governed Mutation Loop Declaration

- Date: 2026-08-28
- Tranche: T5 Governed Mutation Loop
- Entry class: tranche declaration
- Transition: PROVISIONAL -> DECLARED
- Preconditions: T0 PARKED; T1 PARKED; T2 PARKED; T3 PARKED; T4 PARKED in `0035-t4-park.md`
- Implementation authorized by this entry: no
- T5 outcome PARKED: no
- T6 started: no

## Process walk

ORIENT measured the live repository rather than relying on memory. T4 is PARKED by
operator approval, P4 is credited, P5-P8 remain UNSCORED, Product STOP is incomplete,
and T5 has not begun. The controlling authorities read for this declaration were
`.builder/BCC.md`, `.builder/TRANCHE_PROTOCOL.md`, `.builder/TRANCHE_PLAN.md`,
`.builder/CURRENT_STATE.md`, `docs/PRODUCT_CHARTER.md`, `docs/ARCHITECTURE.md`, and the
parked T4 journal/evidence chain through `0035`.

The operator provided a product-orientation clarification before this declaration. This
entry treats that clarification as planning input for T5: Sidecar Workbench is a
directory-bound general-purpose workbench that should remain useful for arbitrary
filesystem-backed targets, not just software repositories; human, CLI, MCP, GUI, and
future projections are entrances to one shared workbench; and construction process
concepts must not be reproduced in runtime behavior unless independently required by the
product.

No concrete contradiction with parked T0-T4 outcomes was identified. T0-T4 remain
PARKED and their Product STOP credit remains unchanged.

DECLARE is this entry. EXECUTE must wait for explicit operator approval.

## Declared outcome

T5 will close the prototype's fundamental governed work loop:

```text
current awareness
  -> reviewed preview
  -> approval bound to that preview and basis
  -> stale-state refusal
  -> bounded mutation through the existing governed host
  -> independent changed-path measurement
  -> honest verification
  -> substrate refresh
  -> awareness refresh
  -> linked durable records
```

The user-visible result is that a human or command-capable agent can make one exact,
reviewed change to an attached target and then see durable evidence of what was
approved, what changed, how verification was judged, and how the workbench re-oriented
to the resulting target reality.

One bounded `write_file` path is sufficient for T5 if it discriminates the required
preview, approval, staleness, measurement, verification, refresh, and record-linking
semantics. T5 proves governed mutation; it does not need a broad editing platform.

## Product intent applied to T5

T5 advances the directory-bound Swiss Army knife intent only where mutation trust needs
runtime machinery:

- **Current awareness** advances shared orientation before work; it must come from the
  parked T4 awareness owner, not from construction state or a parallel entrance.
- **Reviewed preview** advances transformation safety by showing the proposed target
  effect before apply.
- **Approval binding** advances trust by tying permission to the exact preview and
  observed basis that was reviewed.
- **Stale-state refusal** advances honesty by rejecting apply when the target or basis no
  longer matches the reviewed preview.
- **Bounded mutation through the existing governed host** advances the product's shared
  control plane rather than creating a second mutation backend.
- **Independent changed-path measurement** advances Charter invariant 12: measured
  reality outranks a mutating tool's self-report.
- **Honest verification** advances consumer trust by recording passed, failed, or
  unavailable verification without pretending.
- **Substrate refresh and awareness refresh** advance the full work loop by feeding the
  changed reality back into T3 evidence and T4 orientation.
- **Linked durable records** advance P5 by retaining distinct receipts, evidence, and
  App Journal decisions without collapsing their ownership.

No T5 runtime concept is proposed merely because the construction process has tranches,
roles, PARKED status, gates, or Product credit. Runtime governance remains product
governance for mutation only.

## Preconditions and first repair

Before any T5 schema bump or mutation-state storage is implemented, T5 must repair the
known migration-version-stamp defect in `product/core/storage.py`.

Measured current risk: `DATABASE_SCHEMA_VERSION` is 4, and the v3 migration branch
stamps `PRAGMA user_version` to the global current schema version after creating only
the T3 tables, then continues to the v4 awareness branch. Today this is latent; the
moment T5 raises the schema version to 5, the v3 branch could stamp a database as v5
before v4/T5 structures are guaranteed. T5 must stamp each migration branch to the
version actually materialized and prove forward migration from older synthetic
databases.

This repair is included in T5 because governed mutation requires trustworthy schema
evolution for any mutation preview, approval, verification, or linking state that T5
adds.

## Ownership model

Expected T5 ownership is small:

- **Mutation governance owner:** a product/core module, expected as
  `product/core/mutation.py` unless implementation evidence proves a better local name.
  It owns preview records, approval binding, stale-state checks, mutation attempt
  orchestration, changed-path measurement interpretation, verification status, refresh
  linkage, and record summaries.
- **Existing governed host:** `product/core/control.py` continues to own trusted instance
  loading, authority comparison, containment, context transport, child process launch,
  result validation, and operation receipts. T5 may route approved apply through this
  owner but must not duplicate it.
- **Mechanical tool:** `product/tools/write_file/` remains a manifest-described
  deterministic capability. T5 may use it as the smallest sufficient mutation surface.
- **Runtime records:** `product/core/runtime_records.py` continues to own operation
  receipts and operational artifacts.
- **App Journal:** `product/core/app_journal.py` continues to own deliberate work-memory
  entries and links. T5 may create or require an explicit decision entry only through the
  App Journal owner.
- **Substrate:** `product/core/substrate.py` continues to own resources, versions,
  observations, evidence, claims, and relations. T5 may call substrate refresh after a
  mutation but must not create substrate facts directly.
- **Awareness:** `product/core/awareness.py` continues to own awareness revisions/items.
  T5 may call awareness refresh after substrate refresh but must not create awareness
  records directly.

T5 may add mutation-governance records, but those records are not T2 receipts, T3
evidence, T4 awareness revisions, or App Journal entries. Links may connect the record
classes without merging their meaning.

## Dependency and entrance model

The intended runtime flow is:

```text
CLI mutation command
  -> mutation governance owner
  -> awareness current/read + substrate basis/freshness checks
  -> deterministic preview for one write_file operation
  -> explicit approval token or approval record bound to the preview and basis
  -> stale-state refusal before apply
  -> existing control plane invokes write_file with apply authority
  -> independent target measurement of changed paths
  -> honest verification result
  -> substrate refresh
  -> awareness refresh
  -> linked receipts/evidence/App Journal/mutation records
```

CLI is the only required T5 entrance. MCP remains absent and removable. A future MCP
adapter may later expose the same host and mutation state in T6, but T5 must not create
a parallel MCP backend.

## Scope

T5 is in scope to:

- repair migration branch version stamping before any schema-version increase;
- add a forward-migration fixture proving older synthetic databases cannot be stamped as
  a later version without owning the tables for that version;
- add minimal mutation-governance storage if needed for preview, approval, stale refusal,
  verification, measurement, refresh, and linkage;
- add a deterministic preview for one bounded `write_file` operation that includes the
  proposed path, before/after or created-file semantics, content digest or comparable
  reviewed payload identity, expected changed paths, and the awareness/substrate basis
  being reviewed;
- bind approval to that exact preview identity, target identity, awareness revision or
  basis, and current target signature;
- reject apply if the target content or relevant basis has changed since preview;
- apply only after explicit approval through the existing governed host and the existing
  `write_file` tool authority path;
- independently measure actual changed paths after apply rather than relying only on the
  tool envelope;
- record verification honestly as passed, failed, or unavailable with evidence of how
  that judgment was reached;
- refresh T3 substrate after successful mutation and then refresh T4 awareness from the
  resulting substrate basis;
- link mutation records, operation receipts/artifacts, substrate evidence/claims,
  awareness revision handles, and App Journal decisions without merging their owners;
- add minimal child-process environment containment needed to preserve explicit
  context/authority boundaries during governed mutation;
- expose minimal CLI commands for preview, approve, apply, inspect status/history, and
  read linked records where required by the loop;
- prove the loop remains target-domain-agnostic and does not assume a software project;
  and
- add a T5 gate under `.builder/gates/` with discriminating behavioral evidence.

## Non-goals

T5 does not implement a general workflow engine, generic transaction framework,
autonomous repair system, rollback platform, patch language, multi-step planner, merge
resolver, conflict-resolution UI, elaborate approval hierarchy, background daemon,
watcher, scheduler, or broad verification framework.

T5 does not add MCP, GUI, local AI, embeddings, vector retrieval, domain cartridges,
release packaging, compatible update proof, removal proof, public quickstart, Linux
certification, or broad cross-target truthfulness certification. Those belong to later
tranches unless a measured T5 blocker proves otherwise.

T5 does not create runtime equivalents of Builder, Reviewer, tranche, gate, PARKED, or
Product credit concepts. It records product mutation governance only: preview,
approval, stale refusal, measurement, verification, refresh, and linked records.

T5 does not make App Journal decisions automatic construction journal entries. The
runtime App Journal remains a deliberate work-memory owner for the attached target.

T5 does not make awareness or substrate depend upward on mutation governance. T5 may
call their public owners; lower layers must remain usable without T5-specific projection
imports.

## Expected changed surfaces

- `product/core/storage.py`: repair migration stamping and add T5 schema only if
  mutation-governance storage is needed.
- `product/core/constants.py`: advance `DATABASE_SCHEMA_VERSION` only after migration
  stamping is repaired and tested.
- `product/core/mutation.py` or equivalent: own governed mutation preview, approval
  binding, stale refusal, measurement interpretation, verification, refresh orchestration,
  and linking.
- `product/core/control.py`: add only minimal environment allowlist/containment and any
  narrow host hook required to route an already-approved mutation through the existing
  control plane.
- `product/core/cli.py`: expose minimal mutation loop commands through the CLI entrance.
- `product/core/runtime_records.py`: only if a narrow linking or receipt read helper is
  required by T5 while preserving T2 ownership.
- `product/core/app_journal.py`: only if an explicit App Journal decision/link helper is
  required by T5 while preserving App Journal ownership.
- `product/core/substrate.py`: only for public owner calls or narrow helpers needed to
  refresh/read linked T3 state; T5 must not move substrate ownership.
- `product/core/awareness.py`: only for public owner calls or narrow helpers needed to
  refresh/read linked T4 state; T5 must not move awareness ownership.
- `tests/test_t5_governed_mutation.py`: focused product fixtures for the loop.
- `.builder/gates/t5_governed_mutation.py`: sole T5 closure gate.
- Existing cumulative gates only if vocabulary/status updates are needed for their own
  continuing assertions.
- `docs/ARCHITECTURE.md`, `.builder/TRANCHE_PLAN.md`, `.builder/CURRENT_STATE.md`,
  `README.md`, and later journal entries: review synchronization only.

T5 should not modify MCP, GUI, release, factory packaging, domain-cartridge, or broad
consumer-documentation surfaces unless implementation evidence proves they block the
declared P5 outcome.

## Completion evidence declared before implementation

The eventual T5 gate must prove the following through product tests, CLI exercises,
structural checks, and discrimination witnesses:

1. A fresh attach has no mutation previews, approvals, mutation records, verification
   records, or mutation-linked App Journal decisions until explicit mutation-loop
   actions run.
2. Migration stamping is version-accurate: synthetic older databases cannot be stamped
   as a later schema version unless all tables/columns for the stamped version exist.
3. The migration fixture covers at least a synthetic v2 database through the repaired
   v3/v4 path and the T5 schema version, including an interruption-style or staged
   assertion that each branch stamps only its own materialized version.
4. Preview can be created for one bounded `write_file` change without applying the
   change, and the preview records proposed path, reviewed payload identity, expected
   changed paths, current awareness/basis handle, target identity, and current target
   signature.
5. Approval binds to the exact preview identity and reviewed basis/signature; an approval
   for one preview cannot authorize a different path, content, target, basis, or later
   preview.
6. Apply without approval is refused before child-process launch and before target
   mutation.
7. Apply after target or basis change is refused as stale before child-process launch and
   before target mutation.
8. Approved non-stale apply uses the existing governed host and `write_file` authority
   path rather than a private mutation backend.
9. Child-process environment containment preserves the explicit-context/authority
   boundary for governed mutation; undeclared identity or operator-token environment
   inheritance is rejected or absent from child execution evidence.
10. Actual changed paths are independently measured after apply and compared with the
    preview expectation and/or allowed mutation boundary.
11. A mutating tool's self-report alone is insufficient to close the mutation record.
12. Verification is recorded honestly as passed, failed, or unavailable, with supporting
    evidence and without converting unavailable verification into PASS.
13. Successful mutation triggers explicit substrate refresh and awareness refresh, and
    the new awareness is based on the post-mutation substrate basis.
14. Prior substrate evidence and prior awareness revisions remain inspectable after the
    mutation and refresh.
15. Linked records connect the mutation preview, approval, apply receipt/artifact,
    measurement, verification result, substrate evidence/claim handles, awareness
    revision, and any explicit App Journal decision without collapsing their owners.
16. The T5 loop works on a generic directory target and does not require software-project
    files, language metadata, build tools, or domain-specific intelligence.
17. T5 does not introduce MCP, GUI, local AI, embeddings/vector index, domain cartridge,
    release/update/removal, rollback platform, workflow engine, or construction-role
    runtime concepts.
18. Lower layers do not depend upward on mutation governance: mechanical tools,
    `core.tool_runtime`, registry, runtime records, App Journal, substrate, and awareness
    do not import a T5 projection/entrance owner unless a declared owner boundary
    explicitly requires a narrow lower-layer helper.
19. Canonical pytest, Ruff, the T5 gate, and cumulative T4/T3/T2/T1/T0 checks pass from
    the committed review candidate.

The gate must include discrimination against plausible wrong implementations, including:

- applying during preview;
- approval tokens that are not bound to the preview payload, target, basis, and target
  signature;
- applying after target mutation or substrate/awareness basis drift;
- trusting a mutating tool's self-reported changed paths without independent
  measurement;
- marking verification PASS when verification is unavailable or failed;
- writing substrate, awareness, receipt, or App Journal records directly from the wrong
  owner;
- leaving child-process environment inheritance broad enough to bypass explicit
  context/authority boundaries;
- stamping an older database as a later schema version before all migration branches for
  that version have materialized;
- adding MCP, GUI, local AI, embeddings, domain cartridges, release/update/removal,
  workflow-engine, rollback, planner, or construction-tranche runtime surfaces; and
- assuming the target is a software repository.

## Ordered implementation plan

1. Add focused failing migration tests for version-accurate migration stamping from
   synthetic older databases, including the current v3 branch defect and the eventual T5
   schema version.
2. Repair `storage.py` so each migration branch stamps only the version it has
   materialized; only then advance `DATABASE_SCHEMA_VERSION` if T5 storage is required.
3. Add focused failing T5 tests for blank mutation state, preview-without-apply,
   approval binding, stale target refusal, stale basis refusal, approved apply through
   the existing governed host, independent changed-path measurement, honest verification,
   substrate refresh, awareness refresh, and linked records.
4. Define the minimal T5 mutation-governance storage/API needed to persist preview,
   approval, mutation attempt/result, measurement, verification, refresh, and links.
5. Add minimal child-process environment allowlist/containment in the existing control
   plane, with evidence that governed mutation children receive only declared execution
   environment needed for the installed tool.
6. Implement deterministic preview for one bounded `write_file` operation using
   awareness/substrate basis information and target signature as reviewed reality.
7. Implement approval binding for that preview and stale-state refusal before apply.
8. Route approved non-stale apply through the existing `ControlPlane` and `write_file`
   tool rather than bypassing host authority.
9. Independently measure actual changed paths after apply and compare them with the
   previewed mutation boundary.
10. Record honest verification status and supporting evidence, including the
    unavailable-verification path if no target-native verifier is declared.
11. Refresh substrate and then awareness after successful mutation; link the resulting
    handles to mutation records without changing their owners.
12. Add minimal CLI commands for the governed mutation loop and readback of linked
    records.
13. Implement the T5 gate with behavioral and adversarial discrimination witnesses.
14. Consolidate for ownership separation, stale assumptions, containment, generated
    debris, target-domain neutrality, construction/runtime boundary, naming, and
    unnecessary abstraction.
15. Run focused T5 tests, canonical pytest, Ruff, `git diff --check`, T5 gate, cumulative
    T4/T3/T2/T1/T0 gates, and one discovery search for out-of-scope runtime concepts or
    construction-process leakage.
16. Synchronize review documentation and submit T5 AWAITING_APPROVAL without parking T5,
    claiming P5 credit, or beginning T6.

## Scope removed or deferred by the simplicity test

- A generic workflow engine is deferred because one reviewed `write_file` loop is enough
  to prove governed mutation.
- A general transaction/rollback platform is deferred because T5 needs stale refusal,
  measurement, verification, and refresh, not universal undo.
- A patch language or multi-file planner is deferred because the minimum P5 witness can
  be one exact bounded write.
- Multi-actor approval hierarchy is deferred because explicit operator approval bound to
  one preview proves the needed trust boundary.
- Autonomous repair, background watching, scheduling, and broad verifier discovery are
  deferred because they do not advance the smallest useful governed loop.
- MCP exposure is deferred to T6 so it remains a removable entrance to the same host and
  state.
- Domain-specific intelligence and broad target-class certification are deferred to T7.
- Release/update/removal and public consumer packaging are deferred to T8.
- Runtime tranche, Builder, Reviewer, gate, PARKED, or Product-credit concepts are
  rejected unless a future independent product requirement is declared.

## Risks and decisions held for implementation evidence

- The smallest durable representation for preview, approval, verification, measurement,
  and linkage may be one table or a small set of tables; implementation should choose the
  smallest form that preserves owner separation and queryability.
- Approval identity may be content-addressed or opaque, but it must bind the reviewed
  payload, target, basis, and target signature.
- Verification may be unavailable for a generic directory. Honest `unavailable` is
  acceptable if it is explicit, durable, and not scored as PASS.
- Changed-path measurement must be independent of the mutating tool report but can be a
  bounded before/after target signature for the single-write path.
- Environment allowlisting must preserve installed tool execution without carrying
  unrelated operator secrets into child processes.
- The current product still has a trusted installed-tool-code assumption; T5 may record
  that assumption in Architecture during review synchronization, but it should not become
  a sandboxing platform.
- If implementation discovers a specific contradiction between parked T0-T4 runtime
  behavior and the operator's clarified product intent, stop and report it instead of
  silently reopening or repairing parked work.

## Review position

This declaration is submitted for operator review. T5 is DECLARED, not IMPLEMENTING. No
product source, product tests, manifests, runtime schema, T5 gate, or runtime authority
document has been changed by this entry. Implementation must wait for explicit operator
approval of this declaration.
