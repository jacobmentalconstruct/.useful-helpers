# Source Provenance

Status: Tranche 1 reference audit

This project may inspect the following reference sources:

- `../_PARTS-FOR-PLANS/_ProjectMAPPER/`
- `../_PARTS-FOR-PLANS/_TokenizingPATCHER/`
- `../_PARTS-FOR-PLANS/_LineNUMBERIZER/`
- `../_PARTS-FOR-PLANS/_GitPUSHER/`

These are not runtime dependencies.

## Provenance Rule

When behavior is borrowed, ported, or substantially adapted from a reference
source, record:

- source path,
- borrowed behavior,
- reason for reuse,
- owning destination component,
- cleanup or decoupling performed,
- tests or checks that preserve behavior.

## Tranche 1 ProjectMapper Reference Audit

Audited source:

- `../_PARTS-FOR-PLANS/_ProjectMAPPER/README.md`
- `../_PARTS-FOR-PLANS/_ProjectMAPPER/src/app.py`
- `../_PARTS-FOR-PLANS/_ProjectMAPPER/tools/export_vendor_app.py`
- `../_PARTS-FOR-PLANS/_ProjectMAPPER/assets/`

Reference behavior identified for possible re-homing:

| Behavior | Reference anchor | Migration status |
| --- | --- | --- |
| Project tree scan with exclusion skips | `scan_project_tree`, `ExclusionPolicy` | audit only; not copied |
| SQLite snapshot schema | `create_snapshot_schema` | audit only; schema likely compatibility target |
| Snapshot inserts and output readback | `insert_*`, `load_snapshot_output` | audit only; not copied |
| Text and binary classification | `safe_read_text`, `safe_read_blob`, binary extension constants | audit only; good early test target |
| Markdown tree/filedump projections | `build_project_tree_markdown`, `build_filedump_markdown` | audit only; not copied |
| UI tree behavior | `ProjectMapperApp.populate_tree`, `on_tree_item_click`, `toggle_tree_item` | audit only; target UI differs |
| Vendor export | `create_vendor_export`, `tools/export_vendor_app.py` | deferred until packaging tranche |

No reference code has been re-homed into `.project-mapper` during Tranche 1.

## Provenance Findings

- The reference source includes generated `vendor_exports` folders and zip
  files. These are historical artifacts, not implementation source to migrate.
- The reference `tools/export_vendor_app.py` imports from `src.app`; this is
  acceptable in the old app but should not be copied until packaging behavior
  has an owned project-local module to call.
- The reference app's section markers are useful as audit landmarks, but the
  new project should create real module boundaries instead of preserving the
  monolith shape.
## Core Foundation Re-Homed Behavior

The core foundation repair re-homed small, bounded behavior from the reference
ProjectMapper app. This was done to establish owned contracts before UI work,
not to copy the monolith.

| Behavior | Reference anchor | Destination | Cleanup / ownership | Verification |
| --- | --- | --- | --- | --- |
| File size formatting and safe text classification | `format_display_size`, `safe_read_text`, binary extension constants | `src/core/file_info.py` | Removed UI coupling; kept core-only helpers | `tests/test_core_file_info.py` |
| Default/dynamic/gitignore exclusion policy | `ExclusionPolicy` | `src/core/exclusions.py` | Owned by core; no widget state or snapshot writes | `tests/test_core_exclusions.py` |
| Inclusion state model | `folder_item_states`, `S_CHECKED`, `S_UNCHECKED` | `src/core/selection.py` | Converted from UI-owned absolute paths to core-owned relative-path selection | `tests/test_core_selection.py` |
| Project tree scan records | `scan_project_tree` | `src/core/scanner.py` | Returns typed project items/skipped paths; avoids recursive folder-size totals by default | `tests/test_core_scanner.py` |

Generated `vendor_exports` and the reference monolith were not copied.