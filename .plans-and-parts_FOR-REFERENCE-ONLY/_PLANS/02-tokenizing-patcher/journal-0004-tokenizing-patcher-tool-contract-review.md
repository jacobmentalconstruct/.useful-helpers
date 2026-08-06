# Journal Entry 0004: Tokenizing Patcher Tool Contract Review

Date: 2026-08-03

## Tranche Declaration

Select another reference app from the parts bin, review it, isolate the functions
we want to incorporate as Useful Helpers tools, populate the related placeholder
Python adapter, and write a semantic overview with searchable locators.

Selected reference app:

`_PARTS-FOR-PLANS/_TokenizingPATCHER/src/app.py`

## Scope

- Review `_TokenizingPATCHER` as the second integration target.
- Identify functions and classes that define JSON patch schema handling,
  line tokenization, hunk matching, indentation behavior, validation, diff
  preview, file writes, GUI flow, and CLI behavior.
- Populate `src/useful_helpers/tools/tokenizing_patcher/adapter.py` with a
  semantic tool contract and granular capability map.
- Add a documentation overview for the Tokenizing Patcher terminal done state.
- Record temporary parts-bin locator retirement rules.
- Add repeatable contract tests for the adapter.
- Extract shared tool contract dataclasses to avoid duplicating adapter scaffolding.

## Non-Goals

- No executable patch engine implementation in this tranche.
- No GUI patch command wiring beyond registry status alignment.
- No Project Mapper backend implementation.
- No Line Numberizer or Git Pusher review.
- No deletion of parts-bin references while they are still needed as review anchors.

## Reference Findings

Primary implementation anchors captured from the reference app:

- README `Patch Schema Definition` line 39 for the hunk schema.
- `class ButtonConfig` line 23, `class LinkConfig` line 31, and
  `class LocalUnifiedButtonGroup` line 37 for the validate/apply UI pattern.
- `class PatchError` line 130 for expected patch-domain failures.
- `class StructuredLine` line 133 and `tokenize_text` line 149 for whitespace
  and newline-aware tokenization.
- `locate_hunk` line 162 for strict and content-only hunk matching.
- `apply_patch_text` line 188 for schema validation, hunk matching, overlap
  detection, indentation adjustment, and patched text reconstruction.
- `patch_base_indent` line 255 for relative indentation behavior.
- `validation_preview_text` line 316 for GUI dry-run state.
- `save_file` line 617 for versioned output behavior.
- `get_schema_template` line 642 for user-facing schema template.
- `_show_diff_view` line 661 for unified diff preview.
- `validate_patch` line 691 and `apply_patch` line 738 for GUI dry-run/apply flow.
- `run_cli` line 790 and `main` line 847 for headless and hybrid execution.

`src/app.py` and `src/app_ORIGINAL.py` had the same SHA256 hash at review time,
so `src/app.py` was treated as the active locator surface.

## Changes

- Added `src/useful_helpers/tools/contracts.py` for shared semantic contract dataclasses.
- Updated `src/useful_helpers/tools/project_mapper/adapter.py` to use the shared contract types.
- Replaced `src/useful_helpers/tools/tokenizing_patcher/adapter.py` placeholder with a dataclass-backed semantic contract.
- Updated `src/useful_helpers/tools/registry.py` to show Tokenizing Patcher as contract-reviewed and implementation-pending.
- Added `tests/test_tokenizing_patcher_adapter_contract.py`.
- Added `_docs/TOKENIZING_PATCHER_TOOL_CONTRACT.md`.
- Updated `_docs/SOURCE_PROVENANCE.md` with Tokenizing Patcher review provenance.
- Updated `_docs/CURRENT_STATE.md` with both reviewed tool contracts.
- Updated `_docs/PROJECT_PLAN.md` with Root Tranche 3 and revised next tranche sequence.
- Updated `_docs/ARCHITECTURE.md` with Tokenizing Patcher ownership notes and shared contract types.

## Decisions

- Treat Tokenizing Patcher as a tool/domain label, not as the application identity.
- Preserve the reference app's core one-file patch semantics but define the Useful
  Helpers target as multi-file batch patching over the explorer inclusion set.
- Implement backend patch behavior before GUI command wiring.
- Require dry-run validation and per-file result records before any multi-file write.
- Keep parts-bin paths in runtime adapter only while implementation recovery still depends on them.
- Use a shared contract type module rather than duplicating dataclass definitions in each reviewed adapter.

## Validation

- `python -m pytest -q -p no:cacheprovider`: `14 passed`.
- `python src\app.py --status`: root status smoke passed with `0.2.0-root-shell`.
- `rg -n "PARTS-BIN|_TokenizingPATCHER|_ProjectMAPPER|from \.PARTS|import .*Tokenizing|import .*ProjectMAPPER" _docs BCC.md src tests _journal --hidden --no-ignore`: intentional references only.
- `rg -n "from \.PARTS|import .*Tokenizing|import .*ProjectMAPPER" src tests --hidden --no-ignore`: no runtime imports found.
- Generated cache debris was removed after verification.

## Review and Repair Notes

- Issue found: adding a second semantic adapter would duplicate dataclass contract scaffolding. Repaired by adding `src/useful_helpers/tools/contracts.py` and updating Project Mapper to use it.
- Issue found: current-state verification lines were pending before checks. Repaired with actual verification results.
- Deferred issue: Line Numberizer and Git Pusher placeholder adapters still contain parts-bin source references. This is acceptable while they remain unreviewed placeholders; remove or replace when their tools are re-homed.

## Risks and Backlog

- The Tokenizing Patcher backend is not implemented yet.
- The reference app patches one file; Useful Helpers must design and test batch behavior separately.
- The GUI selection surface still needs hardening before multi-file tool execution feels complete.
- Temporary parts-bin locators in reviewed adapters must not be mistaken for runtime imports.
- Line Numberizer and Git Pusher remain unreviewed placeholders.

## Park State

Parked after verification and cleanup. Recommended next tranche remains Project Mapper Backend Implementation unless multi-file patching becomes the priority.
