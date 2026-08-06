# Tokenizing Patcher Tool Contract

Status: backend implemented; GUI/CLI wiring pending

Date: 2026-08-04

## Reference Dependency Rule

Reference app reviewed:

`_PARTS-FOR-PLANS/_TokenizingPATCHER/src/app.py`

Backup copy observed:

`_PARTS-FOR-PLANS/_TokenizingPATCHER/src/app_ORIGINAL.py`

`app.py` and `app_ORIGINAL.py` have the same SHA256 hash at review time, so
`src/app.py` is the active locator surface.

The locators in this document and in
`src/useful_helpers/tools/tokenizing_patcher/adapter.py` are temporary review
anchors. They may guide implementation, but the Useful Helpers runtime must not
import from, read from, or require the parts-bin app.

When a Tokenizing Patcher capability is fully re-homed, remove the corresponding
parts-bin locator from runtime tool code. Historical provenance may remain in
this document or `_docs/SOURCE_PROVENANCE.md`.

## Current Implementation State

Root Tranche 11 implemented the headless Tokenizing Patcher backend in
`src/useful_helpers/tools/tokenizing_patcher/backend.py`.

Implemented locally:

- structured JSON hunk schema validation,
- line tokenization with indentation, trailing whitespace, newline style, and
  final-newline state preservation,
- strict hunk matching with content-only floating fallback,
- missing, ambiguous, and overlapping hunk detection,
- relative indentation by default and literal patch indentation when requested,
- unified diff preview generation,
- single-file dry-run helper,
- dry-run-first multi-file batch helper,
- conservative write gate that blocks all writes when any selected file fails
  preflight by default,
- overwrite and versioned output write modes.

Still pending:

- Useful Helpers GUI workflow for patch input, validation state, diff preview,
  apply/version controls, and per-file operation log,
- CLI wrapper command surface,
- output path collision handling for shared versioned output directories,
- retirement of temporary Tokenizing Patcher parts-bin locators after GUI/CLI
  behavior no longer needs reference recovery.
## Tool Done State

The Tokenizing Patcher tool family is done when Useful Helpers can build,
validate, preview, and apply structured JSON hunk patches against one or many
explorer-selected text files; preserve newline style and indentation intent;
detect missing, ambiguous, and overlapping hunks before writes; show per-file
diffs and errors; optionally write versioned outputs; and do all of that from
local Useful Helpers modules with no runtime dependency on the parts-bin
reference app.

## Capability Map

### Parse Patch Schema

Target outcome:

Accept a JSON patch object containing one or more hunks with search and replace
blocks plus per-hunk indentation mode.

Expected inputs:

- patch JSON text or file

Expected outputs:

- validated patch object
- schema errors with location/context

Reference anchors:

- README `Patch Schema Definition` at line 39
- `get_schema_template` at line 642
- `validate_patch` at line 691
- `run_cli` at line 790

Search locator:

```bat
rg -n "Patch Schema Definition|get_schema_template|validate_patch|run_cli" "_PARTS-FOR-PLANS\_TokenizingPATCHER\README.md" "_PARTS-FOR-PLANS\_TokenizingPATCHER\src\app.py"
```

Done when:

Useful Helpers can parse patch JSON, reject malformed schemas before file
matching, and surface actionable errors in both GUI and backend tests.

### Tokenize Source Lines

Target outcome:

Split source text into line tokens that preserve leading indentation, logical
content, trailing whitespace, and newline style.

Expected inputs:

- source text

Expected outputs:

- structured line sequence
- detected newline style

Reference anchors:

- `class StructuredLine` at line 133
- `tokenize_text` at line 149

Done when:

Patch matching and reconstruction can round-trip unchanged text and preserve
newline style in repeatable tests.

### Locate Patch Hunks

Target outcome:

Find each hunk search block in a target file by exact match first, then
content-only floating match when indentation changed.

Expected inputs:

- tokenized target file
- tokenized search block

Expected outputs:

- single match range per hunk
- missing or ambiguous match errors

Reference anchors:

- `class PatchError` at line 130
- `locate_hunk` at line 162

Done when:

Missing hunks, ambiguous matches, and match fallback behavior are reported before
any write occurs.

### Apply Single-File Patch

Target outcome:

Apply validated hunks to one text file buffer, using relative indentation by
default or strict patch indentation when requested.

Expected inputs:

- original source text
- validated patch object
- global force-indent toggle

Expected outputs:

- patched source text
- patch result metadata
- patch errors

Reference anchors:

- `apply_patch_text` at line 188
- `patch_base_indent` at line 255
- `class PatchError` at line 130

Search locator:

```bat
rg -n "class PatchError|apply_patch_text|patch_base_indent" "_PARTS-FOR-PLANS\_TokenizingPATCHER\src\app.py"
```

Done when:

A backend API can dry-run and apply a patch to one text buffer while detecting
overlapping hunks and preserving intended indentation.

### Preview Patch Diff

Target outcome:

Generate a unified diff preview for a valid patch before the user chooses to
write results.

Expected inputs:

- original source text
- patched preview text
- file label

Expected outputs:

- unified diff text

Reference anchors:

- `_show_diff_view` at line 661
- `validate_patch` at line 691

Done when:

Useful Helpers can show per-file diff previews for validated patches without
mutating the source file.

### Apply Multi-File Patch Batch

Target outcome:

Expand the one-file reference behavior into a Useful Helpers batch operation
over explorer-checked files, with per-file dry run, diff, errors, and write
decisions.

Expected inputs:

- explorer operation inclusion set
- one shared patch or per-file patch plan
- force-indent toggle
- dry-run/apply mode
- output/versioning policy

Expected outputs:

- per-file patch result records
- aggregate success/failure summary
- per-file diffs
- written files or versioned outputs when apply is approved

Reference anchors:

- `apply_patch_text` at line 188
- `validate_patch` at line 691
- `apply_patch` at line 738
- `run_cli` at line 790

Done when:

The Tools menu can validate and apply patch batches against multiple selected
text files without writing any file whose dry run failed.

### Write Patched Outputs

Target outcome:

Write patched results to original files or version-suffixed output paths
according to the user's selected safety policy.

Expected inputs:

- patched text
- target file path
- version/output policy

Expected outputs:

- written output path
- write error records

Reference anchors:

- `save_file` at line 617
- `run_cli` at line 790

Done when:

Write behavior is explicit, tested, and never overwrites multiple files without
prior validation and user-visible result state.

### Patcher GUI Workflow

Target outcome:

Present patch input, validation status, diff preview, indentation mode, and
apply/version options inside the Useful Helpers right pane or a tool dialog.

Expected inputs:

- selected file or file batch
- patch JSON
- user options

Expected outputs:

- validation state
- diff preview
- apply controls
- operation log

Reference anchors:

- `class ButtonConfig` at line 23
- `class LinkConfig` at line 31
- `class LocalUnifiedButtonGroup` at line 37
- `validation_preview_text` at line 316
- `validate_patch` at line 691
- `apply_patch` at line 738

Done when:

The GUI lets users validate first, inspect diffs, then apply patches with clear
per-file state and no hidden writes.

### CLI Compatibility

Target outcome:

Preserve a headless execution path for tests, automation, and future tooling
scripts even if the primary surface is the Useful Helpers GUI.

Expected inputs:

- target path
- patch JSON path
- output path
- force-indent
- dry-run

Expected outputs:

- exit code
- stdout/stderr message
- optional written output

Reference anchors:

- `run_cli` at line 790
- `main` at line 847

Done when:

The patch engine can be exercised without Tk and supports dry-run and
output-path behavior through local Useful Helpers code.

## Implementation Notes

- The old reference app is a one-file patcher. Useful Helpers must expand this
  into a batch-aware tool over the explorer inclusion set.
- Backend behavior should be implemented and tested without Tk first.
- GUI wiring should not write files until all selected files in the batch have
  passed dry-run validation or the chosen policy explicitly allows partial apply.
- The linked validate/apply control is a useful idea, but the Useful Helpers UI
  should adapt it to the workbench style rather than copying the old layout.
- The typo in the parts-bin folder name is preserved in locators because it is
  the actual folder path.
