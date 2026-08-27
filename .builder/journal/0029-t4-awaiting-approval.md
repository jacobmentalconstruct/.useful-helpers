# 0029 - T4 awaiting approval

Date: 2026-08-27

Status transition: T4 Awareness IMPLEMENTING -> VERIFYING -> AWAITING_APPROVAL.

## Declared outcome

T4 must establish compact immutable awareness revisions over the parked T3 epistemic
substrate. Awareness is a projection and orientation layer: it references T3-owned
resources, versions, observations, epistemic evidence, claims, and provenance through
stable handles, exposes freshness, limitations, and unknowns, and never becomes the
owner of substrate facts, T2 runtime receipts/artifacts, or App Journal memory.

## Amendment honored

Entry `0027` hardened the declaration before implementation. The implementation follows
that amendment:

- awareness consumes T3 semantics through `product/core/substrate.py` APIs and handles;
- verified storage is used only for awareness-owned tables;
- direct target signatures are ephemeral freshness signals only;
- insufficient or missing basis yields `unknown`;
- initial awareness source handles are T3-owned handles, plus awareness-owned
  `awareness:` identifiers; and
- T2 receipt/App Journal information is not independently consumed by T4.

## What changed

- Advanced the runtime SQLite schema to version 4.
- Added `product/core/awareness.py` as the owner for awareness revisions, items,
  freshness, limitations, unknowns, handle references, and drill mapping.
- Added CLI awareness commands for status, refresh, current, revision list/read, and
  drill.
- Added focused product fixtures for blank awareness state, unobserved target unknown
  basis, empty-target awareness, non-empty awareness with resolvable T3 handles,
  immutable revisions, stale freshness, drill traversal, and T2/T3 separation.
- Added the authoritative T4 gate and discrimination witnesses.
- Updated cumulative T0/T2/T3 gates narrowly so parked earlier tranches remain valid
  once T4 owns awareness tables and lifecycle vocabulary.
- Synchronized Architecture, Tranche Plan, Current State, and README for T4 review.

## Evidence

The red baseline was captured before implementation: focused T4 product fixtures failed
6/6 because the `awareness` CLI command did not exist.

Focused and canonical verification after implementation:

- `python -B -m pytest tests\test_t4_awareness.py -q` passed 6/6.
- `python -B -m pytest -q` passed 37/37.
- `python -m ruff check . --no-cache` passed.

Gate evidence:

- Initial T4 gate run `20260827T112409Z-3d124322` failed 10/12 because generated cache
  debris remained and the new gate did not yet recognize the legitimate relative import
  `from . import substrate`; SHA-256
  `68D97C5796846D7357B029B8B68E68668DA708E5EBE5C97AD205BFE989829629`.
- Repaired dirty-tree T4 run `20260827T112506Z-256911a6` passed 12/12; SHA-256
  `B9D10F2F336DA979752AD81D657D135338A7C6252F14B907B3386DD1E3BE78D7`.
- Parallel cumulative discovery found fixture-runtime interference and a T3 cumulative
  schema-era assumption. These were recorded in T0 run `20260827T112651Z-fb135294`, T1
  run `20260827T112635Z-1ed72003`, T2 run `20260827T112700Z-7067271b`, and T3 runs
  `20260827T112657Z-6e849fff` and `20260827T112810Z-d2a265bf`.
- T3 cumulative compatibility repair run `20260827T112856Z-c0c0df5c` passed 12/12.
  SHA-256 `4DC9F1889BDDB37338A43F533790734673C4DF36883B83A01F1F014A1FE4C0A4`.
- Authoritative T4 review receipt from clean implementation candidate `21787fb`: run
  `20260827T112959Z-3b4dd2a9` passed 12/12; SHA-256
  `26FC5F45FDEBE3C8A380CE48F131088BCB9DE2CFE0561C2D4307E5C762B922A6`.
- Cumulative T3 run `20260827T113036Z-c4d644f9` passed 12/12; SHA-256
  `9F676093E6C83AD7E34A5A370FFAC635FB29C830E52D3D54576F5F91F90C2C83`.
- Cumulative T2 run `20260827T113118Z-6146afff` passed 13/13; SHA-256
  `E67CF644EFD7F7B1DE8F3BE21C66D10B8E82A8FFD72D92F07AE4ABC6968B024A`.
- Cumulative T1 run `20260827T113134Z-b41771ee` passed 9/9; SHA-256
  `77261302DC555C28A4809439C35ED555ABA96309FA3567455BD7F6AE8098C76C`.
- Cumulative T0 run `20260827T113402Z-765d004d` passed 13/13; SHA-256
  `0A459B0C258E4971EEAC9D1FEBF643807FBEE1F5CA34853C4EE6CD03ABE17AC6`.

## Discrimination

The T4 gate rejects plausible wrong implementations:

- overwriting awareness revisions in place;
- querying T3-owned tables directly instead of using the substrate owner;
- using generic `revision:` handles instead of canonical `awareness:` handles;
- fabricating rich orientation when substrate basis is missing; and
- reporting stale target state as current.

Focused fixtures also discriminate against unobserved/empty collapse, missing handle
round-trips, awareness-owned copies of substrate facts, receipt/journal side effects
during awareness refresh, and loss of prior revisions after refresh.

## Remaining risks

The projection is intentionally compact and deterministic. It does not use local AI,
embeddings, semantic retrieval, domain cartridges, model summaries, GUI, MCP, mutation
preview/apply, stale approval binding, changed-path measurement, target-native
verification workflow, release packaging, update proof, or removal proof. Those remain
owned by later tranches.

## Review position

This entry supersedes `0028` only as the current lifecycle position. T4 is submitted for
operator review and remains AWAITING_APPROVAL. The builder does not park T4, does not
claim P4 credit, and does not begin T5.
