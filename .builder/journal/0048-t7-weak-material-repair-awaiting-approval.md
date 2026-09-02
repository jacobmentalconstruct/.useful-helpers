# 0048 - T7 Weak-Material Repair Awaiting Approval

Entry type: verification repair and review submission
Tranche: T7 Domain Truth
Status: AWAITING_APPROVAL
Date: 2026-09-02

## Operator Return

The operator returned T7 to VERIFYING for one bounded repair after Reviewer evidence at
`.builder/evidence/reviews/T7/20260901T135332Z-external-review.md` found that the
candidate claimed large/weak material was metadata-only or avoided content-heavy
inspection while the common resource path still read and hashed every file before
domain classification.

This entry preserves `0047` as historical review evidence and supersedes it only as the
current T7 review submission. It does not park T7, grant P7 credit, begin T8, or reopen
T0-T6.

## Repair

`product/core/substrate.py` now establishes the per-resource domain basis from path,
kind, size, and metadata before deciding whether a content hash is allowed. Files whose
domain basis is `metadata_only` retain `content_hash = null`; content hashing is only
performed after the substrate knows the resource is not weak metadata-only material.

Weak files are now recorded as `file_metadata` observations rather than `file_hash`
observations. This keeps the durable substrate record aligned with the actual inspection
basis.

## Mutation Witness

`tests/test_t7_domain_truth.py` adds
`test_large_weak_material_is_not_fully_read_or_hashed`. The fixture patches
`Path.read_bytes` so a read of the large weak resource raises
`AssertionError("large weak material was fully read")`; the repaired
`_describe_resource` path succeeds without reading the file, records
`content_basis = metadata_only`, and leaves `content_hash` unset.

The same fixture then exercises an installed sidecar refresh and verifies the durable
resource version for `path:large.dat` has no content hash, emits a `file_metadata`
observation, and does not emit a `file_hash` observation for that resource.

`.builder/gates/t7_domain_truth.py` adds the
`weak_material_metadata_only_boundary` check and a discrimination mutation that rejects
a source shape where content hashing is computed before weak-material basis is known.

## Evidence

Repair evidence:

- Initial repaired T7 gate run `20260902T112338Z-8b212d12` passed the behavioral checks
  but failed repository hygiene after generated caches remained; this receipt is
  preserved as failure evidence.
- Authoritative repaired T7 gate run `20260902T112455Z-7fce770c` passed 12/12 with
  SHA-256 `26B939412089377A77346DFF81EFA0A52BAB48B28A495670E86ED7135D6F8160`.
- Focused T7 pytest passed 8/8.
- Canonical pytest passed.
- Ruff passed.
- `git diff --check` passed with line-ending warnings only.

Cumulative gate evidence from the repaired candidate:

- T6 `20260902T112836Z-96df00b1`: 11/11 PASS,
  SHA-256 `4AAD0DD14090CC5D6A2E7A04248DD3EECEB3FCAF7EAEB3A2F5F84F984B3C07D4`.
- T5 `20260902T112941Z-0a944a21`: 13/13 PASS,
  SHA-256 `04B5F2AF3DA07B3609EB1AA9C7503ECBB62FECAE2F9F1DEBA8EBE794C7D61C2D`.
- T4 `20260902T113058Z-7562ba83`: 14/14 PASS,
  SHA-256 `8894467F1D857EBBC1B8D1CEEB0922EC8DA52BF12058538F1F198A9CB0479717`.
- T3 `20260902T113200Z-dd3b8979`: 12/12 PASS,
  SHA-256 `EE33778BCFAFB2A9201CF67ECFA6722D094375E257E1D9C9E7122F4C710F8135`.
- T2 `20260902T113316Z-36406ca5`: 13/13 PASS,
  SHA-256 `12C8E8F9B4201E05F21CAC162AE52E77816CCE046FCDFB065F7BD44493C4C341`.
- T1 `20260902T113440Z-966fd63b`: 9/9 PASS,
  SHA-256 `0A2F15D9910F2447901E363177634C02DF0373B5A78A36DF77018D137EA10A62`.
- T0 `20260902T113414Z-e73f3c86`: 13/13 PASS,
  SHA-256 `5DA2636A0C96BAA4AFFBDA5B7EEC4CF135903B643FB8556BC3E85D582F5D11C7`.

Earlier hygiene-only failed cumulative receipts from the parallel run remain preserved as
truthful non-authoritative evidence and are not cited as closure evidence.

## Current Review Position

T7 is submitted at AWAITING_APPROVAL for operator review after the bounded
weak-material repair. P7 remains UNSCORED until operator approval grants T7 PARKED
status and P7 credit. T8 has not begun.
