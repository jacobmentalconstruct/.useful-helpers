# Journal Entry 0003: Project Mapper Tool Contract Review

Date: 2026-08-03

## Tranche Declaration

Select one reference app from the parts bin, review it, isolate the functions we
want to incorporate as Useful Helpers tools, populate the related placeholder
Python adapter, and write a semantic overview with searchable locators.

Selected reference app:

`_PARTS-FOR-PLANS/_ProjectMAPPER/src/app.py`

## Scope

- Review `_ProjectMAPPER` as the first integration target.
- Identify Project Mapper functions and constants that define scan, snapshot,
  markdown export, exclusion, and task-runner behavior.
- Populate `src/useful_helpers/tools/project_mapper/adapter.py` with a semantic
  tool contract and granular capability map.
- Add a documentation overview for expected Project Mapper terminal done state.
- Record temporary parts-bin locator retirement rules.
- Add a repeatable contract test for the adapter.

## Non-Goals

- No executable snapshot/export implementation in this tranche.
- No GUI command wiring beyond registry status alignment.
- No Tokenizing Patcher, Line Numberizer, or Git Pusher review.
- No deletion of parts-bin references while they are still needed as review anchors.
- No vendor export adoption; it remains deferred unless explicitly accepted later.

## Reference Findings

Primary implementation anchors captured from the reference app:

- `APP_NAME` line 28 and `SNAPSHOT_DB_SUFFIX` line 47 for metadata/naming.
- `EXCLUDED_FOLDERS` line 53, `FORCE_BINARY_EXTENSIONS_FOR_DUMP` line 64,
  `class ExclusionPolicy` line 457, and `scan_project_tree` line 551 for scan behavior.
- `safe_read_text` line 226 and `safe_read_blob` line 244 for file capture behavior.
- `create_snapshot_schema` line 599 and snapshot writer helpers beginning at
  `insert_project_tree_row` line 740 for SQLite structure.
- `detect_environment_hints` line 853 for snapshot context metadata.
- `build_project_tree_markdown` line 929 and `build_filedump_markdown` line 961
  for markdown projections.
- `compile_snapshot` line 992 for end-to-end snapshot compilation.
- `export_snapshot_output` line 1841 plus export commands at lines 1854, 1857,
  1871, and 1883 for artifact export behavior.
- `toggle_tree_item` line 1662, `set_global_selection` line 1675,
  `manage_exclusions_popup` line 1713, and `run_threaded_action` line 1937 for
  UI behavior to preserve or adapt.

## Changes

- Replaced `src/useful_helpers/tools/project_mapper/adapter.py` placeholder with
  dataclass-backed semantic contract objects.
- Updated `src/useful_helpers/tools/registry.py` to show Project Mapper as
  contract-reviewed and implementation-pending.
- Added `tests/test_project_mapper_adapter_contract.py`.
- Added `_docs/PROJECT_MAPPER_TOOL_CONTRACT.md`.
- Updated `_docs/SOURCE_PROVENANCE.md` with Project Mapper review provenance.
- Updated `_docs/CURRENT_STATE.md` with current stop state and next tranche guidance.
- Updated `_docs/PROJECT_PLAN.md` with Root Tranche 2 and next tranche sequence.
- Updated `_docs/ARCHITECTURE.md` with Project Mapper adapter ownership notes.

## Decisions

- Treat Project Mapper as the first real tool family, not as the application identity.
- Make the adapter semantic before executable so backend implementation has a
  documented stop state and searchable extraction map.
- Keep parts-bin paths in runtime adapter only while implementation recovery
  still depends on them.
- Move or remove parts-bin locators from runtime code once behavior is fully
  re-homed; provenance docs may keep historical anchors.
- Defer vendor export until a later tranche explicitly accepts it as product scope.

## Validation

- `python -m pytest -q -p no:cacheprovider`: `11 passed`.
- `python src\app.py --status`: root status smoke passed with `0.2.0-root-shell`.
- `rg -n "PARTS-BIN" _docs BCC.md src tests _journal --hidden --no-ignore`: intentional references only.
- `rg -n "_ProjectMAPPER" _docs BCC.md src tests _journal --hidden --no-ignore`: intentional references only.
- Generated cache debris was removed after verification.

## Review and Repair Notes

- Issue found: current-state verification lines initially still said pending. Repaired with actual verification results.
- Issue found: Project plan still pointed directly from Root Tranche 1 to explorer hardening. Repaired by inserting this Project Mapper contract tranche and making backend implementation the recommended next tranche.
- Issue found: architecture did not name Project Mapper adapter ownership. Repaired with an explicit adapter role and backend ownership split.
- Deferred issue: non-ProjectMapper placeholder adapters still contain parts-bin source references. This is acceptable while they remain unreviewed placeholders; remove or replace when their tools are re-homed.

## Risks and Backlog

- The Project Mapper backend is not implemented yet.
- The GUI selection surface still needs hardening before tool execution feels complete.
- Temporary parts-bin locators in the adapter must not be mistaken for runtime imports.
- Tokenizing Patcher, Line Numberizer, and Git Pusher remain unreviewed placeholders.

## Park State

Parked after verification and cleanup. Recommended next tranche is Project Mapper Backend Implementation, unless explorer selection hardening is chosen first.
