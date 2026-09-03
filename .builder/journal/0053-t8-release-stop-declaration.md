# 0053 - T8 Release and STOP Declaration

Date: 2026-09-03

Status: DECLARED - AWAITING OPERATOR REVIEW. Same-turn operator instruction authorizes
implementation if no declaration contradiction or blocker is found.

## Reorientation

The live repository is clean at commit `40d1cb274bb552af7a47930949e413de52f93eb5`.
T0-T7 are PARKED by operator approval. P1-P7 are credited. P8 is UNSCORED. Product STOP
is incomplete. Entry `0052-pre-t8-housekeeping.md` resolved pre-T8 H1/H2/H3 and C1/C5,
and carried C2, C3, and C4 into this T8 declaration surface.

## Declared Outcome

T8 produces one positive-composed sealed release artifact that can be installed and used
from clean Windows and Linux environments, proves compatible update and clean removal
behavior, preserves lower-layer dependency direction, excludes construction history and
transient state, and completes the Product STOP evidence walk without beginning a new
product layer.

## Scope

T8 may add or change:

- `factory/` manufacture/release code, including a packaging-neutral archive builder.
- minimal product lifecycle surfaces needed by a sealed installed artifact, including
  compatible replacement/update behavior if existing attach-only mechanics are
  insufficient.
- T8-focused product tests and fixtures under `tests/`.
- the authoritative T8 gate under `.builder/gates/`.
- release output under `/release/` as generated evidence only.
- construction journal, Plan, Current State, Architecture, and README synchronization.

T8 must preserve:

- product runtime code never imports `factory/`, `.builder/`, or `tests/`;
- factory remains manufacture/install/package/release only;
- `.builder/`, tests, gates, review reports, certification exhaust, parent/reference
  lineage, sandbox paths, and transient fixture state do not ship;
- mechanical tools and `core.tool_runtime` do not depend upward on awareness, MCP,
  mutation, receipts, journal, substrate, factory, tests, or construction;
- App Journal semantics do not depend on awareness, MCP, construction history, or this
  repository;
- CLI and MCP expose one host/durable world rather than parallel capability owners.

## Required Carry-In Rulings

- C2 MCP governed mutation parity: T8 must prove the sealed installed artifact exposes
  the governed mutation lifecycle through MCP and CLI over the same durable records, or
  explicitly fail the gate.
- C3 MCP client conformance: T8 must include a realistic JSON-RPC/MCP smoke witness for
  initialization, tool listing, governed calls, mutation access, shutdown, and error
  behavior through the sealed install.
- C4 gate provenance consistency: T8 final evidence must include head commit,
  working-tree state, source digest, artifact identity/digest, platform, Python version,
  and generated release manifest identity. Historical receipts are not rewritten.

## Non-Goals

T8 does not add a GUI, autonomous agent, local AI, embeddings, vector authority, broad
domain cartridges, plugin marketplace, workflow engine, rollback system, native updater
daemon, cloud service, global registry, standalone Tool Pack release, standalone App
Journal distribution, or Coherent Development product. macOS remains UNSCORED.

T8 may implement the minimal compatible replacement path needed for Product STOP, but it
must not grow an updater subsystem or elaborate update UI.

## Completion Evidence

The T8 gate must prove, through fixtures and direct artifact inspection:

1. a sealed artifact is created from a positive product/factory boundary;
2. the artifact contains product runtime and necessary factory install/release surfaces,
   and excludes `.builder`, tests, gates, evidence, review material, runtime fixtures,
   caches, parent/projectmapper dumps, sandbox paths, and construction state;
3. the same artifact installs on a fresh target and begins with blank runtime state;
4. install/attach creates exactly one `.sidecar` footprint and no target-owned pointer,
   `.gitignore`, global registry, or external identity file;
5. relocation with `.sidecar` preserves structural identity;
6. observe/orient/handle drill work through the sealed CLI entrance on empty, software,
   and mixed/document targets;
7. governed mutation works through preview, approval, stale refusal, apply, measured
   changed paths, honest verification, substrate refresh, awareness refresh, and linked
   durable records;
8. MCP from the sealed install exposes the same host catalog and durable world as CLI,
   including the governed mutation surfaces required by C2/C3;
9. removing the MCP adapter leaves CLI, host, and mechanical tools usable;
10. compatible replacement/update from one sealed product payload to another preserves
    instance UUID and runtime state;
11. deleting `.sidecar` removes the instrument while approved target work products
    remain;
12. dependency-direction checks prove lower mechanical capabilities and App Journal
    semantics do not depend upward on projections or construction machinery;
13. release evidence records consistent provenance and digest identity for the source,
    artifact, and gate run.

Focused tests should discriminate wrong implementations with at least:

- artifact-denylist mutation or positive-boundary mutation;
- install/update state-preservation witness;
- sealed CLI/MCP parity witness;
- deletion/removal witness;
- dependency-direction mutation witness.

## Ordered Implementation Plan

1. Add a small release builder in `factory/` that writes a deterministic manifest and
   sealed archive from explicitly selected product/factory surfaces.
2. Add a minimal compatible update/replacement function if attach-only factory mechanics
   cannot preserve state while replacing installed runtime code.
3. Add focused T8 tests for artifact contents, clean install, blank state, update,
   removal, CLI/MCP parity, governed mutation walk, and dependency direction.
4. Add `.builder/gates/t8_release_stop.py` to run the T8 evidence walk and emit a
   provenance-rich receipt.
5. Consolidate source and documentation for stale status, ownership drift, generated
   debris, path leaks, and unnecessary release scope.
6. Run focused T8 tests, canonical pytest, Ruff, `git diff --check`, the T8 gate, and
   cumulative T7/T6/T5/T4/T3/T2/T1/T0 gates as risk warrants.
7. Record an AWAITING_APPROVAL journal entry. Do not park T8 or credit P8/Product STOP
   without explicit operator approval.

## Park Condition

If same-artifact Windows/Linux proof cannot be produced in this environment, T8 must
stop with that limitation explicit rather than claiming Product STOP. If release
assembly requires a new artifact format beyond a zip archive, stop for operator ruling
before expanding scope.
