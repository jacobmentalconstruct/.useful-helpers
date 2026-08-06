# Architecture

Status: Pickup-ready for Tranche 2 explorer shell

ProjectMapper Workbench is an explorer-driven desktop application. The app is
not a tool launcher with a tree attached; the explorer is the stable front door
and tools operate on the current project context and inclusion set.

## Contract Authority

The governing contract is `_docs/BCC.md`; its local `BCC-CONFIG` identifies
`.project-mapper` as this project side-car root. `../artifacts/BCC.md` is the
portable export seed, not the active local contract. When a convenience choice
conflicts with the active BCC, the contract wins unless the user explicitly
authorizes a deviation.

## Core Flow

```text
project scan -> tree model -> browse selection -> inclusion set -> operation runner -> output artifact
```

## Interaction Doctrine

- Click selects the item to inspect in the right pane.
- Check/toggle includes the item in the operation working set.
- Folder inspection shows an immediate child listing with metadata.
- Text file inspection shows a readable preview.
- Binary, large, unreadable, or unsupported files show metadata and status.
- Tools live under a normal top menu structure and operate on the current
  project context.

## Initial Ownership

- `src/app.py`: composition root only.
- `src/ui/`: Tkinter windows, panes, menus, widgets, and UI adapters.
- `src/core/`: project scanning, inclusion state, filtering, and operation
  orchestration.
- `src/storage/`: SQLite snapshot schema, writers, readers, and verification
  helpers.
- `tests/`: repeatable tests for core behavior as tranches add logic.
- `_docs/`: contract, architecture, plan, provenance, testing notes, and app
  journal for this side-car project. In a bootstrapped target project, the BCC
  side-car root owns builder-control docs unless the user chooses otherwise.

## Runtime Doctrine

Heavy runtime mechanics are not justified for the first completion target.
The default architecture is ordinary typed data flow, explicit services,
bounded managers where needed, and clear composition from `src/app.py`.

## Reference Source Boundary

The parts-bin apps are reference sources only. They must not become runtime
dependencies. Any meaningful borrowed behavior must be re-homed into this
project root and recorded in provenance or the app journal.

## Tranche 1 Reference Findings

The current ProjectMapper reference app is a single-file Tkinter application:

- reference path:
  `../_PARTS-FOR-PLANS/_ProjectMAPPER/src/app.py`
- size: about 80 KB / 2017 lines
- primary class: `ProjectMapperApp`
- major pure/functional areas: helpers, vendor export, exclusion policy,
  filesystem scanning, SQLite schema/writers, environment hints, Markdown
  projections, snapshot compile
- major UI areas: layout, tree behavior, exclusion UI, actions, threading,
  logging

The reference app uses section markers that help migration, but those sections
do not create real ownership boundaries. The new project should not import the
reference module at runtime.

## Target Component Map

Initial migration ownership:

| Reference responsibility | Reference anchors | Target owner |
| --- | --- | --- |
| App metadata/constants | `APP_NAME`, `APP_VERSION`, exclusions, suffixes | `src/core/config.py` or `config/` once behavior needs it |
| Pure path/file helpers | `format_display_size`, `rel_posix`, `is_binary`, `safe_read_text`, `safe_stat_size` | `src/core/file_info.py` |
| Exclusion policy | `ExclusionPolicy` | `src/core/exclusions.py` |
| Project scan rows | `scan_project_tree` | `src/core/scanner.py` |
| Inclusion state | `folder_item_states`, `S_CHECKED`, `S_UNCHECKED` | `src/core/selection.py` |
| Folder/file inspect data | not cleanly separated in reference | `src/core/inspection.py` |
| SQLite schema | `create_snapshot_schema` | `src/storage/schema.py` |
| SQLite inserts/readback | `insert_*`, `load_snapshot_output` | `src/storage/snapshot_store.py` |
| Snapshot compilation | `compile_snapshot` | `src/core/operations/snapshot.py` coordinating storage |
| Markdown projections | `build_project_tree_markdown`, `build_filedump_markdown` | `src/core/exports/markdown.py` |
| Environment hints | `detect_environment_hints` | `src/core/environment.py` |
| Operation threading/progress | `run_threaded_action`, `ProgressPopup` | `src/ui/progress.py` plus a small UI-side operation runner |
| Main window shell | `ProjectMapperApp._setup_ui` | `src/ui/main_window.py` |
| Explorer tree view | `populate_tree`, `refresh_tree_visuals`, `on_tree_item_click` | `src/ui/explorer_tree.py` |
| Right context pane | absent from reference | `src/ui/context_pane.py` |
| Top menu commands | absent from reference | `src/ui/menu.py` |
| Vendor export | `create_vendor_export`, `tools/export_vendor_app.py` | defer until packaging tranche; likely `scripts/export_vendor_app.py` |

## Migration Order

The safest order is:

1. Define typed scan and selection data in `src/core`.
2. Build the Tranche 2 explorer shell against those core contracts.
3. Move exclusion/scanner behavior behind tests.
4. Move SQLite schema and writer behavior behind tests.
5. Rebuild snapshot operations against the owned core/storage APIs.
6. Add packaging/vendor export only after the app has useful behavior.

## Known Frailties To Repair

- The reference UI does not match the target workbench layout: operations are
  inline buttons, not top-menu commands, and there is no right context pane.
- Selection state is currently a UI-owned absolute-path dictionary instead of
  a core-owned working-set model.
- `compile_snapshot` is the highest-risk hotspot and mixes scan state,
  selection, storage, file capture, projection generation, manifest creation,
  and metadata.
- The reference tree includes generated `vendor_exports`, including copied
  source and zip files. These are reference artifacts, not content to migrate
  into the new project.
- Folder size computation recursively walks folders during scan. That may be
  expensive for large projects and should be optional or lazy in the new app.
- Opening output folders uses platform shell calls. Keep this UI-owned and
  explicit, and do not let it become a core dependency.

## Quick Wins Identified

- Preserve the reference section markers as a migration checklist.
- Test pure helpers before UI work begins.
- Use the existing SQLite schema as the first compatibility target, but move it
  to `src/storage` before expanding it.
- Treat the existing snapshot compiler as behavioral reference, not code shape
  to copy wholesale.
## Implemented Core Foundation

The repair pass after Tranche 1 introduced the first owned runtime modules:

- `src/core/models.py`: project item, skipped path, preview, entry type, and
  inclusion state contracts.
- `src/core/file_info.py`: path, size, binary/text classification, and safe text
  read helpers.
- `src/core/exclusions.py`: default, dynamic, and `.gitignore`-informed
  exclusion policy.
- `src/core/selection.py`: core-owned inclusion model separated from UI browse
  selection.
- `src/core/scanner.py`: project tree scanner returning owned contracts and
  skipped-path records.

These modules are the required foundation for the Tranche 2 explorer shell.
They intentionally do not implement snapshot writing, menus, right-pane UI, or
project operations yet.
