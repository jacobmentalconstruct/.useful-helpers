# Project Mapper Tool Contract

Status: backend implemented; GUI wiring pending

Date: 2026-08-04

## Reference Dependency Rule

Reference app reviewed:

`_PARTS-FOR-PLANS/_ProjectMAPPER/src/app.py`

The locators in this document and in
`src/useful_helpers/tools/project_mapper/adapter.py` are temporary review
anchors. They may guide implementation, but the Useful Helpers runtime must not
import from, read from, or require the parts-bin app.

When a Project Mapper capability is fully re-homed, remove the corresponding
parts-bin locator from runtime tool code. Historical provenance may remain in
this document or `_docs/SOURCE_PROVENANCE.md`.

## Current Implementation State

Root Tranche 10 implemented the headless Project Mapper backend in
`src/useful_helpers/tools/project_mapper/backend.py`.

Implemented locally:

- SQLite snapshot schema and writer helpers,
- selected text file capture,
- optional small binary blob preservation,
- tree, filedump, combined, and manifest markdown projection builders,
- standalone markdown export writing,
- backend tests for schema, selected capture, skipped paths, outputs, metadata,
  and optional blob capture.

Still pending:

- GUI Tools-menu wiring,
- explorer check/toggle UX integration,
- progress/cancel/error presentation for long Project Mapper operations,
- retirement of temporary Project Mapper parts-bin locators after GUI behavior no
  longer needs reference recovery.
## Tool Done State

The Project Mapper tool family is done when Useful Helpers can use the
explorer-selected working set to compile a SQLite project snapshot; export
project tree, filedump, combined tree plus filedump, and manifest markdown;
preserve exclusion, skipped-path, environment, mapper-state, warning, and error
metadata; surface operation progress and failures in the GUI; and do all of that
from local Useful Helpers modules with no runtime dependency on the parts-bin
reference app.

## Capability Map

### Scan Project Tree

Target outcome:

Produce a typed visible tree and skipped-path records from a chosen project root
using built-in, dynamic, and gitignore-informed exclusions.

Expected inputs:

- project root path
- respect exclusions toggle
- default/dynamic/gitignore exclusion policy
- optional cancellation signal

Expected outputs:

- visible tree rows for folders and files
- skipped path records with reason, detail, entry type, size, and source
- initial checked state for selectable explorer items

Reference anchors:

- `EXCLUDED_FOLDERS` at line 53
- `FORCE_BINARY_EXTENSIONS_FOR_DUMP` at line 64
- `class ExclusionPolicy` at line 457
- `scan_project_tree` at line 551

Search locator:

```bat
rg -n "EXCLUDED_FOLDERS|FORCE_BINARY_EXTENSIONS_FOR_DUMP|class ExclusionPolicy|scan_project_tree" "_PARTS-FOR-PLANS\_ProjectMAPPER\src\app.py"
```

Done when:

The main explorer can rescan a folder, preserve checked state for stable paths,
expose skipped reasons, and avoid scanning excluded or unsafe paths.

### Compile SQLite Snapshot

Target outcome:

Create an authoritative SQLite snapshot from the current checked working set,
including selected text files, optional binary blobs, tree state, metadata,
outputs, and nonfatal errors.

Expected inputs:

- project root path
- output directory
- visible tree rows
- checked/unchecked mapper state
- scan skipped-path records
- exclusion policy
- include binary blobs toggle
- optional cancellation signal

Expected outputs:

- root-named `*_snapshot.sqlite3` database
- `snapshot_metadata`
- `snapshot_manifest`
- `project_tree`
- `project_files`
- optional `project_blobs` rows with sha256
- `snapshot_exclusion_rules`
- `snapshot_skipped_paths`
- `snapshot_mapper_state`
- `snapshot_environment`
- `snapshot_outputs`
- `snapshot_errors`

Reference anchors:

- `APP_NAME` at line 28
- `SNAPSHOT_DB_SUFFIX` at line 47
- `safe_read_text` at line 226
- `safe_read_blob` at line 244
- `create_snapshot_schema` at line 599
- `insert_project_tree_row` at line 740
- `detect_environment_hints` at line 853
- `compile_snapshot` at line 992

Search locator:

```bat
rg -n "APP_NAME|SNAPSHOT_DB_SUFFIX|safe_read_text|safe_read_blob|create_snapshot_schema|insert_project_tree_row|detect_environment_hints|compile_snapshot" "_PARTS-FOR-PLANS\_ProjectMAPPER\src\app.py"
```

Done when:

A user can select paths in Useful Helpers and compile a complete or partial
SQLite snapshot whose tables can be validated with repeatable tests.

### Export Project Tree Markdown

Target outcome:

Export the DB-embedded project tree projection as standalone markdown for a
lightweight project map.

Expected inputs:

- latest snapshot database
- project root path
- output directory

Expected outputs:

- root-named `*_project_tree.md` file

Reference anchors:

- `build_project_tree_markdown` at line 929
- `export_snapshot_output` at line 1841
- `export_tree_markdown` at line 1854

Done when:

The Tools menu can write the selected tree projection from the latest snapshot
and report success or actionable failure.

### Export Filedump Markdown

Target outcome:

Export selected text file contents as fenced markdown, optionally prefixed with
the project tree.

Expected inputs:

- latest snapshot database
- include tree in filedump toggle
- project root path
- output directory

Expected outputs:

- root-named `*_project_filedump.md` file

Reference anchors:

- `build_filedump_markdown` at line 961
- `export_snapshot_output` at line 1841
- `export_filedump_markdown` at line 1857

Done when:

The Tools menu can write a filedump projection that includes only checked,
text-readable files and keeps skipped content out.

### Export Tree Plus Filedump Markdown

Target outcome:

Export one markdown artifact containing both tree map and selected filedump
content.

Expected inputs:

- latest snapshot database
- project root path
- output directory

Expected outputs:

- root-named `*_project_tree_and_filedump.md` file

Reference anchors:

- `build_project_tree_markdown` at line 929
- `build_filedump_markdown` at line 961
- `export_snapshot_output` at line 1841
- `export_combined_markdown` at line 1871

Done when:

The Tools menu can write a combined tree/filedump markdown artifact from the
latest SQLite snapshot without recomputing scan state.

### Export Snapshot Manifest Markdown

Target outcome:

Export the snapshot manifest as a standalone onboarding document for users or
agents inspecting the database.

Expected inputs:

- latest snapshot database
- project root path
- output directory

Expected outputs:

- root-named `*_snapshot_manifest.md` file

Reference anchors:

- `compile_snapshot` at line 992
- `export_snapshot_output` at line 1841
- `export_manifest_markdown` at line 1883

Done when:

The Tools menu can write the DB-embedded manifest markdown and the manifest
accurately describes schema, counts, quick-start queries, and completion state.

### Manage Project Mapper Exclusions

Target outcome:

Let the user view and adjust dynamic exclusions that influence scanning,
snapshots, and exports.

Expected inputs:

- current exclusion policy
- user-entered pattern

Expected outputs:

- updated dynamic exclusion list
- rescan or snapshot behavior reflecting the updated policy

Reference anchors:

- `class ExclusionPolicy` at line 457
- `manage_exclusions_popup` at line 1713

Done when:

The UI can add, remove, and list dynamic exclusions, and snapshot output records
the active exclusion rules.

### Run Long Project Mapper Tasks With Progress

Target outcome:

Run scans, snapshot compiles, and exports without freezing the UI, with visible
progress, cancellation, and logged completion state.

Expected inputs:

- tool command
- progress sink
- optional cancellation signal

Expected outputs:

- task status updates
- success, failure, or cancelled result

Reference anchors:

- `run_threaded_action` at line 1937

Done when:

Long Project Mapper operations can be cancelled or completed while the explorer
remains responsive and errors are visible.

### Deferred Vendor Export Candidate

Target outcome:

Export a standalone copy of Useful Helpers or a selected tool package only if a
later product tranche confirms this is still wanted.

Reference anchor:

- `create_vendor_export` at line 337

Done when:

Not part of the first Project Mapper integration stop state unless a later
tranche explicitly accepts vendor export as product scope.

## Implementation Notes

- Existing root core modules already cover part of scan, exclusion, file info,
  and selection behavior.
- The next implementation tranche should re-home snapshot schema and projection
  logic into local modules before wiring GUI commands.
- GUI command wiring should call local adapters only after the backend can be
  tested without Tk.
- The typo in the parts-bin folder name is preserved in locators because it is
  the actual folder path.
