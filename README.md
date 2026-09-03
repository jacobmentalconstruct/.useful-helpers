# Sidecar Workbench

Sidecar Workbench is the provisional name for a self-contained local instrument
attached to one directory. Its governing product definition is
[`docs/PRODUCT_CHARTER.md`](docs/PRODUCT_CHARTER.md).

The Charter also owns the product/method boundary, lower-layer separability, and runtime
state terminology. Repository construction documents and projections consume those facts
rather than defining alternate versions.

## Construction status

T0 project bootstrap and its subsequent vision alignment are **PARKED by operator approval**.
The source preserved at Git baseline
`60174bc93ef4a187a0cc7ff848a03b3d8772b804` predates construction governance and is
**provisional T1 input**. Its behavior and passing tests confer no tranche or product
acceptance credit until T1 audits them.

The approved T0 alignment receipt is
`.builder/evidence/T0/20260826T054142Z-b5ec742a/bootstrap-gate.json`. T1 Mechanical
Hands + Governed Host is **PARKED by operator approval** in
`.builder/journal/0015-t1-park.md`, supported by authoritative gate run
`20260826T133048Z-8782844f`. T2 Runtime Receipts + Work Memory is **PARKED by operator
approval** in `.builder/journal/0021-t2-park.md`, supported by repaired T2 gate run
`20260827T084412Z-8f66c495`. P1/P2 are credited for the declared T1 boundary, and T2
partially advanced P3 for runtime receipts/artifacts and App Journal memory before T3
completed the epistemic substrate portion.

T3 Epistemic Substrate is **PARKED by operator approval** in
`.builder/journal/0025-t3-park.md`, supported by authoritative T3 gate run
`20260827T103210Z-7c9533eb`. P3 is credited for the combined parked T2 runtime-memory and
T3 epistemic-substrate outcomes.

T4 Awareness is **PARKED by operator approval** in `.builder/journal/0035-t4-park.md`,
supported by authoritative repaired T4 gate run `20260828T111925Z-d9548015`. P4 is
credited. T5 Governed Mutation Loop is **PARKED by operator approval** in
`.builder/journal/0039-t5-park.md`, supported by gate run
`20260829T095546Z-e30c36d7` and external review
`.builder/evidence/reviews/T5/20260829T104344Z-external-review.md`. P5 is credited.
Product STOP is satisfied; project closure remains pending a separate final closure
entry.

T6 Removable MCP Entrance is **PARKED by operator approval** in
`.builder/journal/0043-t6-park.md`, supported by T6 gate run
`20260830T101453Z-956b023b`, cumulative receipts listed in
`.builder/journal/0042-t6-awaiting-approval.md`, and External Reviewer evidence
`.builder/evidence/reviews/T6/20260830T125528Z-external-review.md`. P6 is credited.
T7 Domain Truth is **PARKED by operator approval** under
`.builder/journal/0044-t7-domain-truth-declaration.md`, amended by
`.builder/journal/0045-t7-declaration-weak-material-amendment.md` after Reviewer
declaration evidence
`.builder/evidence/reviews/T7/20260901T115016Z-external-review.md`, with execution start
recorded in `.builder/journal/0046-t7-execution-start.md`, initial implementation review
submitted in `.builder/journal/0047-t7-awaiting-approval.md`, bounded weak-material
repair resubmitted in
`.builder/journal/0048-t7-weak-material-repair-awaiting-approval.md`, and the bounded
classification/generated-subtree repair with operator rulings D1-D3 resubmitted in
`.builder/journal/0049-t7-classification-repair-awaiting-approval.md`, and the bounded
text-document ratio and gate self-consistency repair resubmitted in
`.builder/journal/0050-t7-text-document-ratio-repair-awaiting-approval.md`. Entry
`.builder/journal/0051-t7-park.md` records operator approval and parks P7 credit. Pre-T8
housekeeping is recorded in
`.builder/journal/0052-pre-t8-housekeeping.md`: line-ending policy and gate-exemption
ownership are resolved, while MCP parity/conformance and final release provenance are
carried into the T8 declaration surface.

T8 Release and STOP is **PARKED by operator approval** in
`.builder/journal/0060-t8-park-product-stop.md`, supported by repaired T8 gate run
`20260903T135132Z-5f6595f9` and External Reviewer evidence
`.builder/evidence/reviews/T8/20260903T182527Z-external-review.md`. P8 is credited and
Product STOP is satisfied. Project closure remains pending a separate final closure
entry. Public GitHub/default-branch topology and a concise consumer quickstart remain
post-STOP release-prep items before broad external testing.

Read construction authority in this order:

1. [`.builder/BCC.md`](.builder/BCC.md)
2. [`docs/PRODUCT_CHARTER.md`](docs/PRODUCT_CHARTER.md)
3. [`.builder/TRANCHE_PLAN.md`](.builder/TRANCHE_PLAN.md)
4. [`.builder/TRANCHE_PROTOCOL.md`](.builder/TRANCHE_PROTOCOL.md)
5. [`.builder/CURRENT_STATE.md`](.builder/CURRENT_STATE.md)

Incoming or replacement agents should start with
[`.builder/ROLE_ONBOARDING.md`](.builder/ROLE_ONBOARDING.md), then follow the authority
read order above and their role-specific manifest.

The canonical product-test entrance is:

```powershell
python -m pytest
```

Construction gates are owned only by `.builder/gates/`. Product tests and fixtures
belong only under `tests/`.

## Ownership boundary

- `product/` is installed runtime source.
- `factory/` manufactures, installs, packages, or releases product material. It is not
  runtime product logic.
- `.builder/` governs construction and never ships.
- `tests/` contains product tests and fixtures and never owns tranche gates.
- `docs/` contains product authority and approved implementation documentation.

The shipped runtime must never import from `factory/`.
