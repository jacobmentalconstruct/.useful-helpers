# Journal Entry 0007: BCC Portability and Bootstrap Hardening

Date: 2026-08-03

## Tranche Declaration

Harden the BCC so it can operate as a standalone export seed for bootstrapping
future project work while preserving a configured local contract for this
project.

## Scope

- Add a parsable side-car bootstrap configuration to the BCC.
- Require an agent to ask the user where to save the side-car before first
  local installation.
- Prefer a dot-prefixed side-car root over project-facing `_docs/`.
- Keep builder-control docs removable from the target project runtime.
- Align the active ProjectMapper docs with the local/export BCC split.

## Non-Goals

- No runtime code changes.
- No relocation of existing `.project-mapper` docs in this tranche.
- No rewrite of historical journal entries.
- No explorer UI work.

## Decisions

- `.project-mapper/_docs/BCC.md` is now the active local BCC copy configured
  with `SIDECAR_ROOT=".project-mapper"`.
- `artifacts/BCC.md` is now the standalone export seed and intentionally keeps
  `{{BCC_...}}` placeholders.
- A first-copy agent must ask the user where to install the side-car, suggest a
  dot-prefixed folder such as `.project-workbench/` or `.bcc/`, then fill the
  `BCC-CONFIG` values in the local copy.

## Changes

- Added `BCC-BOOTSTRAP-SIDECAR` to the BCC spine and anchor map.
- Added parsable `BCC-CONFIG` lines for target root, side-car root, contract
  path, and journal path.
- Reframed BCC documentation storage around the configured side-car root.
- Updated project docs to identify the local BCC and standalone export seed
  separately.

## Validation

- `python -m pytest -q -p no:cacheprovider`: `8 passed`.
- `python src\app.py`: placeholder launches with `0.1.0-core-foundation` status.
- Anchor audit: both BCC copies contain 25 required anchors, 0 missing, 0 duplicates.
- Local config audit: `.project-mapper/_docs/BCC.md` has 4 filled `BCC-CONFIG` lines and 0 `{{BCC_...}}` placeholders.
- Export seed audit: `artifacts/BCC.md` has 4 `BCC-CONFIG` lines and intentionally retains `{{BCC_...}}` placeholders for first-copy bootstrap.
- Formatting audit: no literal `` `r`n`` debris remains in active docs checked.
- Cache cleanup: generated Python cache folders removed after verification.

## Park State

Parked. `artifacts/BCC.md` is now suitable as the standalone export seed for bootstrapping a new project, subject to a first-copy agent asking the user where to install the side-car and filling the placeholders in the local copy.
