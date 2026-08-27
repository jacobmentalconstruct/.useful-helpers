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
partially advances P3 for runtime receipts/artifacts and App Journal memory. Product STOP
remains incomplete because T3 still owns the epistemic substrate portion of P3 and P4-P8
remain UNSCORED.

T3 Epistemic Substrate is **PARKED by operator approval** in
`.builder/journal/0025-t3-park.md`, supported by authoritative T3 gate run
`20260827T103210Z-7c9533eb`. P3 is credited for the combined parked T2 runtime-memory and
T3 epistemic-substrate outcomes. Product STOP remains incomplete because P4-P8 remain
UNSCORED.

T4 Awareness is submitted for operator review in
`.builder/journal/0031-t4-basis-freshness-repair-awaiting-approval.md`, supported by
authoritative repaired T4 gate run `20260827T121444Z-3713df86`. T4 is not parked, P4 is
not credited, and T5 has not begun.

Read construction authority in this order:

1. [`.builder/BCC.md`](.builder/BCC.md)
2. [`docs/PRODUCT_CHARTER.md`](docs/PRODUCT_CHARTER.md)
3. [`.builder/TRANCHE_PLAN.md`](.builder/TRANCHE_PLAN.md)
4. [`.builder/TRANCHE_PROTOCOL.md`](.builder/TRANCHE_PROTOCOL.md)
5. [`.builder/CURRENT_STATE.md`](.builder/CURRENT_STATE.md)

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
