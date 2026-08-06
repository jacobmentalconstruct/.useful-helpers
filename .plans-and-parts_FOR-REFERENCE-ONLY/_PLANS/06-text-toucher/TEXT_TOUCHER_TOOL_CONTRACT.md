# TextTOUCHER Tool Contract

Status: contract reviewed; implementation pending

Date: 2026-08-03

## Reference Dependency Rule

Reference app reviewed:

`_PARTS-FOR-PLANS/_TextTOUCHER/`

Primary files reviewed:

- `_PARTS-FOR-PLANS/_TextTOUCHER/src/app.py`
- `_PARTS-FOR-PLANS/_TextTOUCHER/README.md`
- `_PARTS-FOR-PLANS/_TextTOUCHER/requirements.txt`
- `_PARTS-FOR-PLANS/_TextTOUCHER/run.bat`
- `_PARTS-FOR-PLANS/_TextTOUCHER/setup_env.bat`

The locators in this document and in
`src/useful_helpers/tools/text_toucher/adapter.py` are temporary review anchors.
They may guide implementation, but the Useful Helpers runtime must not import
from, read from, or require the parts-bin app.

When a TextTOUCHER capability is fully re-homed, remove the corresponding
parts-bin locator from runtime tool code. Historical provenance may remain in
this document or `_docs/SOURCE_PROVENANCE.md`.

## Reference Frailties Found

- README is empty, so source code and scripts are the only behavior evidence.
- CLI parser only supports verbose GUI launch; it does not create files headlessly.
- Reference save path joins folder and raw filename without explicit containment or path traversal validation.
- Tk Text reads through `tk.END`, which can include a trailing newline unless Useful Helpers normalizes content intentionally.
- Reference writes directly to the final path and does not use an atomic-write or rollback strategy.

## Tool Done State

TextTOUCHER is done when Useful Helpers can create one or more UTF-8 text files
from the explorer-selected folder or an explicitly chosen output folder; compose
safe filenames with user-selected extensions or no extension; optionally append
timestamp suffixes; preview the exact target paths and overwrite decisions;
prevent path traversal or writes outside the approved project/output root; write
text with predictable newline handling; surface success/failure per file; reset
or preserve form state according to user choice; and run entirely from local
Useful Helpers modules with no runtime dependency on the parts-bin reference app.

File-write safety stop state:

No TextTOUCHER write is complete until the target path is resolved, proven
inside the approved output root, checked for existing files, previewed to the
user when overwrite risk exists, and written through a local adapter that
reports path, encoding, newline policy, and error state.

## Capability Map

### Choose Output Folder

Target outcome:

Use the explorer-selected folder as the default output root, with an explicit
folder picker when the user wants a different destination.

Expected inputs:

- browse selection
- optional folder-picker result

Expected outputs:

- approved output root
- visible output path state
- disabled/enabled write state

Reference anchors:

- `selected_folder_path` at line 46
- `state="disabled"` at line 147
- `def select_folder` at line 156
- `filedialog.askdirectory` at line 157

Done when:

The tool cannot write until an output root is explicit and visible.

### Compose Safe Filename

Target outcome:

Build a filename from user input, selected extension, typed extension override,
optional no-extension mode, and optional timestamp suffix.

Expected inputs:

- raw filename
- selected extension
- timestamp toggle
- current clock

Expected outputs:

- display filename
- final extension
- timestamped filename
- validation findings

Reference anchors:

- `DEFAULT_EXT` at line 27
- `extensions =` at line 103
- `raw_name` at line 170
- `default_ext == " (None)"` at line 181
- `os.path.splitext` at line 184
- `datetime.now` at line 189

Search locator:

```bat
rg -n "DEFAULT_EXT|extensions =|raw_name|default_ext == \" \\(None\\)\"|os.path.splitext|datetime.now" "_PARTS-FOR-PLANS\_TextTOUCHER\src\app.py"
```

Done when:

Filename composition is deterministic, test-covered, and rejects empty names,
reserved names, path separators, and unsafe absolute paths.

### Validate Write Target

Target outcome:

Resolve the composed target path and prove it remains inside the approved output
root before any file operation occurs.

Expected inputs:

- approved output root
- composed filename

Expected outputs:

- resolved target path
- inside-root decision
- blocked-path reason

Reference anchors:

- `os.path.join` at line 194

Done when:

No TextTOUCHER write is complete until the target path is resolved, proven inside
the approved output root, checked for existing files, previewed to the user when
overwrite risk exists, and written through a local adapter that reports path,
encoding, newline policy, and error state.

### Preview Overwrite Decision

Target outcome:

Detect existing target files and require an explicit overwrite decision before
replacing content.

Expected inputs:

- resolved target path
- overwrite preference
- user confirmation

Expected outputs:

- exists flag
- overwrite allowed/blocked decision
- visible warning

Reference anchors:

- `os.path.exists` at line 197
- `messagebox.askyesno` at line 198

Done when:

Existing files are never overwritten silently and the final plan shows every
replace action.

### Write UTF-8 Text File

Target outcome:

Write the requested text content to the approved target path with explicit
encoding and newline policy.

Expected inputs:

- resolved target path
- text content
- encoding
- newline policy
- overwrite decision

Expected outputs:

- write result
- bytes/chars written
- path
- error state

Reference anchors:

- `open(full_path` at line 207
- `messagebox.showinfo` at line 210

Done when:

A write reports exact success/failure details and never depends on the old
standalone app.

### Normalize Text Content

Target outcome:

Preserve or normalize text content intentionally, including the trailing newline
that Tk text widgets can add when reading through `tk.END`.

Expected inputs:

- editor text
- trailing-newline policy
- newline policy

Expected outputs:

- normalized text
- content warnings

Reference anchors:

- `def save_file` at line 169

Done when:

Content written by Useful Helpers matches the previewed content byte-for-byte
after chosen newline policy.

### Reset Or Preserve Form State

Target outcome:

After a write, clear or preserve filename/content fields according to a visible
user setting.

Expected inputs:

- write result
- reset preference
- current form state

Expected outputs:

- next form state
- focus target
- status message

Reference anchors:

- `delete(0, tk.END` at line 213

Done when:

Successful writes leave the form in a predictable state for repeated file
creation.

### TextTOUCHER GUI Workflow

Target outcome:

Expose folder selection, filename, extension, no-extension mode, timestamp
toggle, text editor, preview, save, overwrite prompt, and result state inside
Useful Helpers.

Expected inputs:

- selected project/folder
- filename
- extension option
- timestamp toggle
- text content

Expected outputs:

- tool form state
- target preview
- write result
- error or success message

Reference anchors:

- `CONFIG =` at line 23
- `APP_TITLE` at line 26
- `class TextFileGenerator` at line 33
- `def save_file` at line 169
- `def main` at line 221
- `tk.Tk` at line 230

Done when:

TextTOUCHER is available from the Tools menu without replacing the
explorer-first workbench shell.

### Headless Create File

Target outcome:

Provide a backend/API path for tests and possible CLI use to create text files
without launching Tk.

Expected inputs:

- output root
- filename
- extension option
- content
- timestamp option
- overwrite policy

Expected outputs:

- operation plan
- write result
- exit/error state

Reference anchors:

- `argparse.ArgumentParser` at line 222
- `--verbose` at line 223

Done when:

The behavior promised by the GUI can be tested headlessly, while the reference
CLI launcher is treated only as evidence.

### Packaging Scripts Reference Only

Target outcome:

Treat old run/setup batch scripts as launch provenance, not Useful Helpers
runtime behavior.

Reference anchors:

- requirements `Standard Library` at line 1
- requirements `tkinter` at line 5
- `python -m src.app` at line 23
- `pip install -r requirements.txt` at line 14

Done when:

Useful Helpers packaging does not depend on the reference `.venv`, `run.bat`, or
`setup_env.bat` scripts.

## Implementation Notes

- Use Useful Helpers explorer selection as the natural default output folder.
- Add backend tests before any GUI save button calls the writer.
- Reject path traversal, absolute names, reserved names, and folder separators in
  filenames.
- Preview final paths before writing, especially for timestamp and overwrite cases.
- Decide and document newline behavior explicitly.
- Consider atomic write support during implementation because this tool mutates
  user-visible files.
- The typo in the parts-bin folder name is preserved in locators because it is
  the actual folder path.
