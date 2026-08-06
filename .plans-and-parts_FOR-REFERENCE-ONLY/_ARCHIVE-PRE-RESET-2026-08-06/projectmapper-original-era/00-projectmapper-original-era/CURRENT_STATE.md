# Current State

Date: 2026-08-03

Status: parked and pickup-ready for Tranche 2 explorer shell

## Summary

ProjectMapper Workbench has a configured local BCC, an export-ready standalone
BCC seed, governing docs, audited reference source, and tested core foundation.
It does not yet have the explorer UI, right-pane inspection, snapshot storage,
exports, patching, line numbering, or git workflow.

## Pickup Order

1. Read `_docs/BCC.md` anchor `BCC-SPINE`.
2. Read `_docs/BCC.md` anchor `BCC-BOOTSTRAP-SIDECAR` to understand local and
   portable BCC roles.
3. Read `_docs/BCC.md` anchor `BCC-WORKFLOW-REQUIRED-TRANCHE-LOOP`.
4. Read this file and `_docs/PROJECT_PLAN.md` section `7. Current Park Point`.
5. Start Tranche 2 only after recording scope, non-goals, checks, and risks in
   the app journal.

## Completed

- Tranche 0: project root, scaffold, BCC, plan, architecture, and journal
  baseline.
- Tranche 1: reference ProjectMapper audit and architecture/migration map.
- Core foundation repair: core models, file info, exclusions, selection,
  scanner, provenance updates, and tests.
- BCC anchor and pointer repair: BCC spine, regex-searchable anchors,
  workflow pointer reduction, and documentation references aligned back to BCC.
- BCC portability/bootstrap hardening: side-car bootstrap rule, parsable
  `BCC-CONFIG` lines, export seed placeholders, and local contract values.
- Handoff alignment cleanup: active docs now point to the current BCC model and
  next tranche state; the older artifact plan is marked superseded.

## Implemented Runtime Surface

- `src/app.py`: placeholder launch/status surface.
- `src/core/models.py`: core data contracts.
- `src/core/file_info.py`: file/path helpers and safe text classification.
- `src/core/exclusions.py`: default, dynamic, and `.gitignore`-informed
  exclusion policy.
- `src/core/selection.py`: core-owned operation inclusion model.
- `src/core/scanner.py`: typed project tree scanner.

## BCC State

- Active local contract: `_docs/BCC.md`.
- Local side-car root configured in BCC: `.project-mapper`.
- Portable export seed: `../artifacts/BCC.md`.
- Export seed placeholders are intentional and must be filled only in a new
  local copy after asking the user where to install that project's side-car.
- `_docs/TRANCHE_WORKFLOW.md` is pointer-only and not authoritative.

## Verification

Latest verification:

```bat
python -m pytest -q -p no:cacheprovider
```

Result: `8 passed`.

```bat
python src\app.py
```

Result: placeholder launched with `0.1.0-core-foundation` status.

Contract checks:

- Active local BCC has 25 required anchors, 0 missing, 0 duplicates.
- Export seed BCC has 25 required anchors, 0 missing, 0 duplicates.
- Active local BCC has 4 filled `BCC-CONFIG` lines and 0 `{{BCC_...}}`
  placeholders.
- Export seed BCC has 4 `BCC-CONFIG` lines and intentionally retains
  `{{BCC_...}}` placeholders for first-copy bootstrap.

## Remaining Risks

- Explorer UI is absent.
- Right-pane folder/file inspection is absent.
- Snapshot storage and Markdown exports are not re-homed.
- Exclusion policy is not a full Git-compatible parser.
- App launch is still a placeholder, not the final desktop shell.

## Active Workflow

Use `_docs/BCC.md` anchor `BCC-WORKFLOW-REQUIRED-TRANCHE-LOOP` for every
meaningful tranche. Validate side-car behavior against anchor
`BCC-BOOTSTRAP-SIDECAR`. Do not duplicate required workflow text outside the
BCC.

## Next Tranche

Begin Tranche 2: explorer shell.

The shell must use the owned core contracts and must preserve the separation
between browse selection and operation inclusion state.
