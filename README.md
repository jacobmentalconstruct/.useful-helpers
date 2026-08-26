# Sidecar Workbench

Sidecar Workbench is the provisional name for a self-contained local instrument
attached to one directory. Its governing product definition is
[`docs/PRODUCT_CHARTER.md`](docs/PRODUCT_CHARTER.md).

The Charter also owns the product/method boundary, lower-layer separability, and runtime
state terminology. Repository construction documents and projections consume those facts
rather than defining alternate versions.

## Construction status

T0 project bootstrap is **AWAITING_APPROVAL after a bounded vision-alignment reopen**.
The source preserved at Git baseline
`60174bc93ef4a187a0cc7ff848a03b3d8772b804` predates construction governance and is
**provisional T1 input**. Its behavior and passing tests confer no tranche or product
acceptance credit until T1 audits them.

The previously approved T0 receipt is
`.builder/evidence/T0/20260825T152930Z-8ecc1428/bootstrap-gate.json`. T1 has not begun.

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
