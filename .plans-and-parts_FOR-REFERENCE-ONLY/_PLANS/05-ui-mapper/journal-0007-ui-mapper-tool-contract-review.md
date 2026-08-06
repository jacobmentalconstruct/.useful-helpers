# Journal 0007: UiMAPPER Tool Contract Review

Date: 2026-08-03

## BCC Anchors

- `BCC-SPINE`
- `BCC-WORKFLOW-REQUIRED-TRANCHE-LOOP`
- `BCC-REFERENCE-SOURCE-RULE`
- `BCC-DOCS-REPORTING`
- `BCC-JOURNAL-LOGGING`

## User Request

Scaffold `_UiMAPPER` in the same way as the previously reviewed reference apps.

## Current State Before Work

- Project Mapper, Tokenizing Patcher, Line Numberizer, and Git Pusher had
  reviewed semantic adapter contracts.
- `_UiMAPPER` existed in the parts bin but had not yet been contract-reviewed
  or added to the Useful Helpers tool registry.
- The next main implementation tranche remained Project Mapper backend work.

## Reference Review

Reviewed `_UiMAPPER` files:

- `README.md`
- `src/app.py`
- `src/ui.py`
- `src/backend.py`
- `src/microservices/`
- `tools/fix.py`
- `tools/check_ms_inits.py`

The reference app describes a local Tkinter-based UI mapper that scans Python
projects and produces a UI map, callback graph, and report artifacts.

## Decisions

- Add UiMAPPER as a reviewed tool contract, not an implemented backend.
- Keep UiMAPPER as a Tools menu workflow inside the Useful Helpers workbench
  rather than copying the old standalone UI shell.
- Treat Ollama/inference/HITL as optional. The base tool must work without a
  local model.
- Treat `_UiMAPPER/tools/` scripts as maintenance provenance only.
- Preserve parts-bin locators only as temporary implementation review anchors.

## Changes Made

- Added `src/useful_helpers/tools/ui_mapper/adapter.py`.
- Added `src/useful_helpers/tools/ui_mapper/__init__.py`.
- Added `tests/test_ui_mapper_adapter_contract.py`.
- Added `_docs/UI_MAPPER_TOOL_CONTRACT.md`.
- Added UiMAPPER to `src/useful_helpers/tools/registry.py`.
- Updated `_docs/SOURCE_PROVENANCE.md`.
- Updated `_docs/ARCHITECTURE.md`.
- Updated `_docs/PROJECT_PLAN.md`.

## Capability Groups Captured

- `scan_python_project`
- `detect_entrypoints`
- `parse_ast_cache`
- `map_tkinter_ui_surface`
- `build_callback_graph`
- `collect_unknown_cases`
- `optional_inference_hitl`
- `serialize_and_write_reports`
- `run_pipeline_with_progress`
- `ui_mapper_gui_workflow`
- `maintenance_tools_reference_only`

## Known Risks

- UiMAPPER is Python/Tkinter-focused and is not yet a general UI mapper.
- The optional inference path depends on local Ollama configuration.
- Reference GUI shell helpers overlap with Useful Helpers shell ownership and
  must not be copied wholesale.
- No UiMAPPER runtime behavior has been re-homed yet.

## Parked State

UiMAPPER is scaffolded as a reviewed semantic contract with searchable locators.
Implementation remains pending and must be completed in a later tranche.
