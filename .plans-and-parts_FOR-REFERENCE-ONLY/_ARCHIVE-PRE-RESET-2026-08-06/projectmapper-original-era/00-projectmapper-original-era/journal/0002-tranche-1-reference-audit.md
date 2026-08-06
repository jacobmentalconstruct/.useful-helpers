# 0002 - Tranche 1 Reference Audit and Architecture Map

Date: 2026-08-03

Status: closed

## Scope

Audit the reference ProjectMapper application and translate its current
single-file behavior into an owned migration map for `.project-mapper`.

## Non-Goals

- No explorer UI implementation.
- No snapshot writer implementation.
- No patcher, line-numberizer, or git workflow integration.
- No runtime dependency on the parts-bin reference source.
- No broad cleanup of sibling/reference folders.

## Tools Used

- `file_tree`: captured reference and project scaffold shape.
- `report`: inspected Python structure.
- `tkinter_widget_tree`: extracted current Tkinter UI structure.
- `ui_callback_graph`: mapped UI callbacks and coupling.
- `complexity_score`: identified risky functions.
- `module_decomp_plan`: confirmed monolith decomposition need.
- `blocking_call_scan`: checked blocking-call risk surface.
- `repo_search` and `rg`: located responsibility clusters and line anchors.
- `evidence`: attached scan summary evidence.

Evidence:

- `evd_2a6138f8e6`: Tranche 1 ProjectMapper reference audit summary.

## Completed

- Audited the reference ProjectMapper structure.
- Audited `src/app.py` responsibility clusters and line anchors.
- Audited Tkinter widget and callback shape.
- Audited complexity/decomposition hotspots.
- Updated `_docs/ARCHITECTURE.md` with target component map and migration
  order.
- Updated `_docs/SOURCE_PROVENANCE.md` with reference-source findings.
- Updated `_docs/TESTING.md` with early test candidates.

## Key Findings

- The reference ProjectMapper is a single-file Tkinter app of about 80 KB / 2017
  lines.
- `ProjectMapperApp` owns UI layout, tree behavior, actions, threading, and
  logging.
- Pure/core behavior is present but mixed into the same file: file helpers,
  exclusion policy, scanner, environment hints, Markdown projections, SQLite
  schema/writers, snapshot compilation, and vendor export.
- The highest-risk function is `compile_snapshot`, which spans lines 992-1265
  and mixes selection, storage, file capture, projections, manifest, metadata,
  and error accounting.
- The current UI is vertical tree/actions/log, not the target explorer plus
  right context pane with top-menu tooling.
- The reference selection state is a UI-owned absolute-path dictionary called
  `folder_item_states`, not a core-owned selected working-set model.

## BCC Alignment Review

Aligned:

- `.project-mapper` remains the only app write target.
- Reference sources remain reference-only.
- No feature work was implemented in this audit tranche.
- Heavy runtime mechanics remain unjustified and unused.

Frailties / issues to repair before or during implementation:

- The reference monolith violates the BCC ownership rules if copied as-is.
- `compile_snapshot` is too broad to become an owned component without
  decomposition.
- Selection needs a core owner before operations are built around it.
- Generated vendor exports in the reference tree must not be migrated.
- The old inline button UI does not satisfy the target menu/right-pane design.
- Recursive folder-size calculation may be expensive on large projects and
  should be lazy, optional, or capped.

## Quick Wins Accounted For

- Use reference section markers as the migration checklist.
- Start tests with pure helpers and exclusion behavior before UI work gets deep.
- Preserve SQLite schema compatibility first, then improve shape only when a
  later tranche justifies it.
- Defer vendor export until packaging; do not pull it into early runtime code.

## Files Changed

- `.project-mapper/_docs/ARCHITECTURE.md`
- `.project-mapper/_docs/SOURCE_PROVENANCE.md`
- `.project-mapper/_docs/TESTING.md`
- `.project-mapper/_docs/_AppJOURNAL/0002-tranche-1-reference-audit.md`

## Verification

- Ran local analysis tools successfully after setting `PYTHONPATH` to the
  workspace root.
- Ran `python src\app.py` after documentation updates.
- Ran `python -m pytest -q`; no tests were discovered, which remains expected
  because Tranche 1 did not add executable behavior.

## Repair Plan

1. Before Tranche 2 UI work, create minimal core data contracts for scan rows,
   item identity, item metadata, and inclusion state.
2. Build tests for `file_info`, `exclusions`, and `selection` as soon as those
   modules are introduced.
3. In Tranche 2, build the explorer shell against the new core contracts rather
   than copying `ProjectMapperApp` wholesale.
4. Keep output-opening and progress UI in `src/ui`; keep scanner/storage free of
   shell and widget dependencies.
5. Defer recursive folder-size totals or make them lazy/capped so scanning large
   projects stays responsive.
6. In Tranche 4, split snapshot compilation into operation orchestration,
   storage writes, capture policy, and projection generation before adding new
   output behavior.

## Park Point

Tranche 1 is complete. The next implementation tranche should begin with the
repair plan above, especially core contracts and testable selection/scanning
boundaries, before building the Tranche 2 explorer shell.