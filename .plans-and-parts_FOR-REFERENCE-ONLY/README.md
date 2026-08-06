# useful-helpers-plans-and-parts-2026-08-05

Self-contained backup of the conversion plans and the original apps
they were derived from.

Generated: 2026-08-05

## Layout

- `_PLANS/` - one folder per reference app, holding that app's plan.
- `_PARTS-FOR-PLANS/` - the original reference apps themselves.

The two halves travel together on purpose. Each plan carries reference
locators naming a file and line in its source app; with both halves
present, every locator can be followed without access to the original
project.

## Path Rewriting

In the live project the apps sit under `.PARTS-BIN-FOR-REFERNCE-ONLY-TO-BE-REMOVED/`.
Inside this bundle they sit under `_PARTS-FOR-PLANS/`. Every reference in
the bundled plans has been rewritten accordingly: 120
references across 31 files.

This bundle is verified to contain no remaining references to the
original parts-bin path.

## `_PLANS/`

Each numbered folder holds one app's full pre-conversion plan:

- `*_TOOL_CONTRACT.md` - intent, required stop state, capability list,
  safety rules, reference frailties, explicit non-goals.
- `journal-*.md` - the contract review record: what was inspected, what
  was decided and why, residual risks, park point.
- `adapter-*.py` - the same contract in code, carrying capability
  records and reference locators (file and line) into the source app.
- `SOURCE_APP.txt` - which app this plan covers and where it sits in
  this bundle.

| Plan folder | Source app |
| --- | --- |
| `_PLANS/01-project-mapper/` | `_PARTS-FOR-PLANS/_ProjectMAPPER/` |
| `_PLANS/02-tokenizing-patcher/` | `_PARTS-FOR-PLANS/_TokenizingPATCHER/` |
| `_PLANS/03-line-numberizer/` | `_PARTS-FOR-PLANS/_LineNUMBERIZER/` |
| `_PLANS/04-git-pusher/` | `_PARTS-FOR-PLANS/_GitPUSHER/` |
| `_PLANS/05-ui-mapper/` | `_PARTS-FOR-PLANS/_UiMAPPER/` |
| `_PLANS/06-text-toucher/` | `_PARTS-FOR-PLANS/_TextTOUCHER/` |
| `_PLANS/07-chat-window-kernal/` | `_PARTS-FOR-PLANS/_ChatWindowKERNAL/` |
| `_PLANS/08-the-cell/` | `_PARTS-FOR-PLANS/_theCELL/` |
| `_PLANS/09-wasm-inference-wrapper/` | `_PARTS-FOR-PLANS/_WasmInferenceWRAPPER/` |
| `_PLANS/10-monaco-viewer/` | `_PARTS-FOR-PLANS/_MonacoVIEWER/` |
| `_PLANS/11-manifold-mcp/` | `_PARTS-FOR-PLANS/_manifold-mcp/` |
| `_PLANS/12-the-dismantler/` | `_PARTS-FOR-PLANS/_TheDISMANTLER/` |

### `_PLANS/00-projectmapper-original-era/`

The original ProjectMapper-era plan set, recovered from Git history.
This is the plan as it stood before the ProjectMapper scaffold was
superseded by the broader workbench. It was deleted from the working
tree in commit `907868d`, so it cannot be found by browsing the live
project.

Includes the original 473-line `PROJECT_PLAN.md` covering Tranches 0
through 8, the supporting document set, `BCC.superseded.md`, and eight
`_AppJOURNAL` entries.

## `_PARTS-FOR-PLANS/`

12 reference apps, 468 files.

These are working copies of the original applications. Regenerable
content was excluded: version control directories, virtual
environments, dependency directories, and bytecode caches. Everything
else is preserved as-is.

These apps are reference material. They are not runtime dependencies of
the workbench and were never intended to be.

## Status

A backup and reading snapshot. Not authoritative. The live documents
are in the project under `_docs/` and `_journal/`; the ProjectMapper-era
set is authoritative only as history.

## Provenance

Built by `scripts/export_plans_and_parts_backup.py`.
