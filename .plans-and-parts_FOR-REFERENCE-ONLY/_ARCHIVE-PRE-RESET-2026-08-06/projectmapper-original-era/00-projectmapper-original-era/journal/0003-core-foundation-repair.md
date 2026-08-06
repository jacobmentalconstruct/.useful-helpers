# 0003 - Core Foundation Repair

Date: 2026-08-03

Status: parked / closed

## Scope

Repair, fortify, and lightly enhance the project based on the Tranche 1 review
before beginning explorer UI work.

This tranche exists because Tranche 1 identified a BCC risk: building the UI
first would likely recreate the old ProjectMapper pattern where selection,
scan state, and operation inputs were owned by the Tkinter app. The repair goal
was to establish small, testable core contracts before any explorer UI work.

## Non-Goals

- No explorer UI implementation.
- No right-pane implementation.
- No top menu implementation.
- No snapshot writer migration.
- No Markdown export migration.
- No patcher, line-numberizer, or git workflow integration.
- No runtime dependency on parts-bin reference sources.
- No broad cleanup of sibling/reference folders.

## Completed

- Added core data contracts for project items, skipped paths, file previews,
  entry types, and inclusion states.
- Added core-owned file/path helpers.
- Added core-owned exclusion policy.
- Added core-owned selection model.
- Added core-owned scanner that returns typed project items and skipped-path
  records.
- Made scanner folder-size behavior safer by avoiding recursive folder-size
  totals by default.
- Added focused tests for file helpers, exclusions, selection, and scanner.
- Updated the placeholder app status to reflect the tested core foundation.
- Updated README, architecture, testing, project plan, and source provenance.
- Removed generated `.pytest_cache` and `__pycache__` cleanup debris after
  verification.

## Decisions

- Core item identity is based on project-relative paths for operation state.
- UI browse selection and operation inclusion state remain separate concepts.
- The selection model is core-owned and UI-agnostic.
- The scanner does not import or call any UI code.
- Folder recursive size totals are not part of the default scan path.
- Reference behavior was re-homed only in small, bounded units; the reference
  monolith was not copied.
- Full `.gitignore` compatibility is not claimed. The current policy supports
  the subset needed for the first explorer/scanner path and is documented as a
  later hardening area.

## Files Changed

Runtime/core:

- `.project-mapper/src/app.py`
- `.project-mapper/src/core/__init__.py`
- `.project-mapper/src/core/models.py`
- `.project-mapper/src/core/file_info.py`
- `.project-mapper/src/core/exclusions.py`
- `.project-mapper/src/core/selection.py`
- `.project-mapper/src/core/scanner.py`

Tests:

- `.project-mapper/tests/test_core_file_info.py`
- `.project-mapper/tests/test_core_exclusions.py`
- `.project-mapper/tests/test_core_selection.py`
- `.project-mapper/tests/test_core_scanner.py`

Documentation:

- `.project-mapper/README.md`
- `.project-mapper/_docs/ARCHITECTURE.md`
- `.project-mapper/_docs/PROJECT_PLAN.md`
- `.project-mapper/_docs/SOURCE_PROVENANCE.md`
- `.project-mapper/_docs/TESTING.md`
- `.project-mapper/_docs/_AppJOURNAL/0003-core-foundation-repair.md`

## Verification

Evidence:

- `evd_4cf820bac2`: Core foundation repair verification.

Checks run:

- `python -m pytest -q -p no:cacheprovider`
  - Result: `8 passed`.
- `python -m compileall -q src tests`
  - Result: passed.
- `python src\app.py`
  - Result: launched placeholder app and reported
    `ProjectMapper Workbench 0.1.0-core-foundation`.
- Checked for generated cache debris after verification.
  - Result: no `__pycache__` or `.pytest_cache` folders remained.

## BCC Alignment Review

Aligned:

- Core behavior now has owned modules instead of being planned as UI state.
- The selection model is explicitly separate from UI browse selection.
- Scanner behavior is project-root local and has no UI or shell dependency.
- The folder-size frailty is reduced by making recursive folder totals absent
  from the default scanner path.
- Tests now exist for the first owned behavior.
- Reference sources remain reference-only; no parts-bin runtime import exists.
- No heavy runtime mechanics were introduced.

Remaining frailties:

- The explorer UI is still absent.
- Snapshot storage and exports are still not re-homed.
- File/folder right-pane inspection is still absent.
- Exclusion policy is compatible with the reference behavior but remains a
  first-pass implementation; edge-case `.gitignore` semantics may need
  hardening later.
- The app still has only a placeholder `src/app.py` launch surface.

## Issue Disposition

Resolved in this tranche:

- UI-owned operation selection risk: repaired by `src/core/selection.py`.
- No test coverage: repaired with 8 core foundation tests.
- Scanner/UI coupling risk: repaired by `src/core/scanner.py` using core models.
- Recursive folder-size scan cost: reduced by making folder sizes absent by
  default.
- Unrecorded provenance for re-homed behavior: repaired in
  `_docs/SOURCE_PROVENANCE.md`.

Deferred deliberately:

- Explorer shell: Tranche 2.
- Right context pane: Tranche 2.
- Snapshot storage/schema migration: Tranche 4 unless Tranche 2/3 require an
  earlier compatibility stub.
- Markdown exports: Tranche 4.
- Full `.gitignore` semantics: hardening backlog after the first scanner/UI
  path is exercised.

## Current State

The project now has a tested core foundation but no user-facing explorer UI.
The correct next implementation move is to build the Tranche 2 shell against
these modules:

- `src/core/models.py`
- `src/core/file_info.py`
- `src/core/exclusions.py`
- `src/core/selection.py`
- `src/core/scanner.py`

The app can be launched, but it intentionally prints status only.

## Park Point

Parked cleanly after core foundation repair.

Next recommended action:

1. Start Tranche 2 with a new journal entry.
2. Re-read `_docs/BCC.md`, `_docs/PROJECT_PLAN.md`, `_docs/ARCHITECTURE.md`,
   and this journal entry.
3. Build the explorer shell without copying the old `ProjectMapperApp`.
4. Keep UI browse selection separate from operation inclusion state.
5. Add UI smoke checks once the shell can open and scan a project folder.