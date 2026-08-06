# Journal Entry 0005: Line Numberizer Tool Contract Review

Date: 2026-08-03

## Tranche Declaration

Select another reference app from the parts bin, review it, isolate the functions
we want to incorporate as Useful Helpers tools, populate the related placeholder
Python adapter, and write a semantic overview with searchable locators.

Selected reference app:

`_PARTS-FOR-PLANS/_LineNUMBERIZER/`

## Scope

- Review `_LineNUMBERIZER` as the third integration target.
- Identify functions and classes that define annotation, stripping, line maps,
  AST tree/flat/semantic export, output naming, CLI dispatch, and GUI flow.
- Populate `src/useful_helpers/tools/line_numberizer/adapter.py` with a semantic
  tool contract and granular capability map.
- Add a documentation overview for the Line Numberizer terminal done state.
- Record temporary parts-bin locator retirement rules.
- Add repeatable contract tests for the adapter.

## Non-Goals

- No executable line-numberizer backend implementation in this tranche.
- No GUI line-numberizer command wiring beyond registry status alignment.
- No Project Mapper or Tokenizing Patcher backend implementation.
- No Git Pusher review.
- No deletion of parts-bin references while they are still needed as review anchors.

## Reference Findings

Primary implementation anchors captured from the reference engine:

- README `Features` line 7 for annotate, strip, AST export, and line-map behavior.
- `class PrefixStyle` line 38, `class PipeStyle` line 44, `class ColonStyle`
  line 48, and `class BracketStyle` line 52 for supported line-number formats.
- `PIPE_RE` line 56 for conservative prefix recognition.
- `open_text_maybe` line 71 and `create_text_maybe` line 76 for text IO.
- `detect_total_lines` line 86 and `annotate_lines` line 93 for annotation.
- `strip_lines` line 99 for stripping only recognized prefixes.
- `line_hash` line 107, `build_map` line 111, and `strip_prefix_for_map` line
  315 for line-map generation.
- `AST_SAFE_FIELDS` line 122, `_ast_node_to_dict` line 136, and `build_py_ast`
  line 155 for tree/flat AST JSON.
- `class SemanticVisitor` line 177 and `build_semantic_model` line 260 for
  semantic block exports.
- `cmd_annotate` line 272, `cmd_strip` line 321, `cmd_map` line 344, and
  `cmd_ast` line 359 for CLI command behavior.
- `Python syntax error at line` line 408 for syntax failure reporting.
- `numbered_suffix` line 415, `suggest_out_path` line 418, `build_parser` line
  426, and `main` line 471 for CLI/output orchestration.

Primary GUI anchors captured from `src/app.py`:

- `default_output_for` line 35 for output naming cues.
- `run_cli_async` line 57 for background execution pattern.
- `class App` line 73 for operation, style, AST mode, output, run, and log controls.
- `on_run` line 269 for building CLI argv from GUI state.

## Changes

- Replaced `src/useful_helpers/tools/line_numberizer/adapter.py` placeholder with a dataclass-backed semantic contract.
- Updated `src/useful_helpers/tools/registry.py` to show Line Numberizer as contract-reviewed and implementation-pending.
- Added `tests/test_line_numberizer_adapter_contract.py`.
- Added `_docs/LINE_NUMBERIZER_TOOL_CONTRACT.md`.
- Updated `_docs/SOURCE_PROVENANCE.md` with Line Numberizer review provenance.
- Updated `_docs/CURRENT_STATE.md` with three reviewed tool contracts.
- Updated `_docs/PROJECT_PLAN.md` with Root Tranche 4 and revised next tranche sequence.
- Updated `_docs/ARCHITECTURE.md` with Line Numberizer ownership notes.

## Decisions

- Treat `linenumberizer.py` as the authoritative behavior source and `app.py` as GUI workflow evidence only.
- Treat Line Numberizer as a tool/domain label, not as the application identity.
- Preserve the reference app's line prefix, strip, map, and AST semantics but define the Useful Helpers target as batch-aware over the explorer inclusion set.
- Implement backend behavior before GUI command wiring.
- Keep parts-bin paths in runtime adapter only while implementation recovery still depends on them.
- Keep in-place writes explicit and conservative; prefer preview/output-file behavior for batch mode.

## Validation

- `python -m pytest -q -p no:cacheprovider`: `17 passed`.
- `python src\app.py --status`: root status smoke passed with `0.2.0-root-shell`.
- `rg -n "PARTS-BIN|_LineNUMBERIZER|_TokenizingPATCHER|_ProjectMAPPER|from \.PARTS|import .*LineNUMBERIZER|import .*Tokenizing|import .*ProjectMAPPER" _docs BCC.md src tests _journal --hidden --no-ignore`: intentional references only.
- `rg -n "pending after this tranche|next integration target|from \.PARTS|import .*LineNUMBERIZER|import .*Tokenizing|import .*ProjectMAPPER" _docs src tests _journal --hidden --no-ignore`: no stale pending text or runtime imports after verification results were recorded.
- Generated cache debris was removed after verification.

## Review and Repair Notes

- Issue found: current-state verification lines were pending before checks. Repaired with actual verification results.
- Deferred issue: Git Pusher placeholder adapter still contains a parts-bin source reference. This is acceptable while it remains an unreviewed placeholder; remove or replace when the tool is re-homed.

## Risks and Backlog

- The Line Numberizer backend is not implemented yet.
- The reference engine is CLI-first and mostly single-file; Useful Helpers must design and test batch behavior separately.
- AST export needs per-file syntax/unsupported-file handling in batch mode.
- The GUI selection surface still needs hardening before batch tool execution feels complete.
- Temporary parts-bin locators in reviewed adapters must not be mistaken for runtime imports.
- Git Pusher remains an unreviewed placeholder.

## Park State

Parked after verification and cleanup. Recommended next tranche remains Project Mapper Backend Implementation unless the user wants to review Git Pusher first.
