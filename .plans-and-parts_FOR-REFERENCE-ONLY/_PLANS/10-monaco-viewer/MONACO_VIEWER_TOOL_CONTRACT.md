# MonacoVIEWER Tool Contract

Status: contract reviewed; implementation pending; reference is Qt-hosted and
must be re-homed as a separate-process session service

Reference app:
`_PARTS-FOR-PLANS/_MonacoVIEWER/`

- `src/app.py` (341 lines): Qt/pywebview host, `Api` bridge class, CLI.
- `assets/index.js` (442 lines): Monaco boot, tab model, surgical replace.
- `assets/index.html` (68 lines): shell markup, CSP, modals.

Runtime contract surface:
`src/useful_helpers/tools/monaco_viewer/adapter.py`

## Intent

The intended tool is the shared editing surface of the workbench: a Monaco
editor that a human and an agent operate **together, on the same session**.

The accepted behavior is symmetric and bidirectional:

- when the human acts in the GUI, the agent observes the action and its result,
- when the agent calls a function, the change propagates into the human's live
  window as a visible, undoable edit,
- both sides read the same session state and the same event record.

Monaco is the right engine for this because it supplies editing behavior Tk does
not provide natively (syntax highlighting, multi-model tabs, range-precise
programmatic edits, undo stacks, find/replace), while remaining scriptable from
Python.

## Host Model Decision

ACCEPTED 2026-08-04: **separate process plus session service.**

The reference is not a Tk integration. `src/app.py:9` imports `tkinter` with the
comment "Kept for contract compliance, though primary GUI is pywebview" and then
never uses it. The real stack is PySide6/Qt driving pywebview, forced at
`src/app.py:13` by `os.environ['PYWEBVIEW_GUI'] = 'qt'`. `webview.start()` at
`src/app.py:255` blocks and owns the main thread.

Qt and Tk each expect to own the process native event loop, so the Monaco
surface cannot be embedded into the existing Tk workbench process.

Accepted shape:

- Monaco runs in its own Qt/pywebview process.
- That process exposes an **editor session service** over local IPC.
- The Tk workbench is a client of that service.
- The agent is a client of that service.
- Neither client is privileged. A GUI button press and an agent call travel the
  same command path and produce the same event record.

Rejected alternatives, recorded so they are not relitigated:

- Embedding a webview inside Tk. Tk has no supported native webview widget on
  Windows; this requires HWND reparenting or a third-party wrapper and risks the
  hardened explorer shell.
- Migrating the whole workbench to Qt. This discards the Tk explorer shell, the
  Project Mapper theme authority, and the theme contract tests delivered by Root
  Tranches 14, 14A, 14B, and 14C.

Consequence for Root Tranche 15: the Tool Command Surface Framework must define
the command/event record such that a GUI-initiated and an agent-initiated
invocation are indistinguishable to observers. MonacoVIEWER is the first tool
that genuinely requires this, so it constrains that framework rather than
consuming it.

## Required Stop State

The tool is complete when Useful Helpers can:

- launch and supervise a Monaco session process from the workbench without
  blocking or destabilizing the Tk event loop,
- expose a documented session API that both the Tk UI and an agent call
  identically,
- report session state (open tabs, active tab, cursor, selection, dirty flags,
  buffer text) to any client on demand,
- emit an event stream so every client observes every mutation, regardless of
  which client caused it,
- apply range-precise edits into a live buffer as undoable operations,
- open, close, and focus tabs on request,
- save a buffer to disk only behind explicit gating that cannot silently
  overwrite newer on-disk content or discard unsaved buffer state,
- load Monaco from vendored local assets with no runtime network dependency,
- survive session-process death without corrupting workbench state,
- do all of this from local Useful Helpers modules with no runtime dependency on
  the parts bin.

## Capabilities

- `session_process_lifecycle`
- `session_state_inspection`
- `session_event_stream`
- `ranged_edit_application`
- `tab_management`
- `gated_buffer_save`
- `vendored_monaco_assets`
- `headless_text_operations`
- `shared_session_provenance`

## Agent Surface Scope

ACCEPTED 2026-08-04: the first implementation grants the agent all four
surfaces below. Save is included, and therefore the save gate is the most
safety-critical part of this contract.

- **Observe (read-only).** Open tabs, active tab, cursor, selection, dirty
  state, live buffer text, plus events raised by human GUI actions. This is the
  half that makes the human's actions visible to the agent.
- **Ranged edits.** The `{start_line, end_line, start_column, end_column,
  replacement_code}` primitive applied into a live buffer as an undoable
  operation. This is the half that makes the agent's actions visible to the
  human.
- **Open / close / focus tabs.** Bring a file into the shared session or change
  which file both parties are looking at.
- **Save to disk.** Commit a buffer to disk. Gated per the rule below.

## Save Gate Rule

No save completes unless the target path is explicit and inside an approved
root, on-disk content is checked for modification since the buffer was loaded,
a conflicting on-disk change is surfaced rather than overwritten, the write is
atomic or equivalently non-truncating, the acting client is recorded, and the
resulting change is announced on the event stream to every other client.

This rule exists because the reference violates all of it. See frailties.

## Reference Frailties

Host and integration:

- `src/app.py:9` imports `tkinter` purely as a "contract compliance" gesture and
  never uses it; the app is Qt, not Tk. The comment is misleading about the
  integration story.
- `src/app.py:13` hard-forces the Qt pywebview backend at import time.
- `src/app.py:255` runs `webview.start()` inside
  `contextlib.redirect_stderr(os.devnull)`, discarding all launch diagnostics.

Agent path:

- The "Agent Surgical Replace" feature (`assets/index.js:100`, `:126`) is a
  modal textarea the human pastes JSON into, with a "Copy Schema" button. There
  is no socket, RPC, or endpoint. The human is the transport; no agent can drive
  it programmatically.
- There is no channel into a running instance. CLI edit arguments
  (`src/app.py:324`) launch a new window per invocation rather than propagating
  into an existing session.
- There is no event stream. `set_active_tab` (`assets/index.js:326`) pushes
  state to the Python host only for window-title purposes.

Data safety:

- Headless regex mode (`src/app.py:283`, `:294`) runs `re.subn` and rewrites the
  file in place with no dry run, no preview, no diff, no backup, and no
  confirmation. If the GUI holds that file open with unsaved edits, the write is
  silently clobbered or diverged. This contradicts the dry-run-first doctrine
  already established by the Tokenizing Patcher backend.
- `_save_logic` (`src/app.py:159`) writes with a plain truncating
  `open(path, 'w')`. There is no atomic write and no backup, so a failure
  mid-write can destroy the original. This contradicts the atomic-ish write
  policy already accepted in the TextTOUCHER contract.
- Save performs no staleness check against on-disk content.

Runtime dependencies:

- Monaco is loaded from `https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0`
  (`assets/index.js:203`). The editor silently fails with no network.
- The CSP (`assets/index.html:5`) permits `unsafe-eval`, `unsafe-inline`, and
  remote script from jsdelivr and unpkg.

Hygiene:

- `apply_log_filter` (`src/app.py:33`) replaces `sys.stdout` and `sys.stderr`
  process-wide and rewrites the substrings "ERROR" to "WARNING (safe to ignore)"
  and "failed" to "note: failed" in all output. This suppresses genuine
  diagnostics and conflicts with BCC 12.1 and 12.2.
- `NamedTemporaryFile(..., delete=False)` (`src/app.py:310`, `:337`) leaks a
  temp file on every untitled launch, never cleaned up. `_update_title`
  (`src/app.py:177`) then string-matches `Untitled-*.txt` to hide the leak.
- Language inference (`src/app.py:318`) uses a hardcoded extension map in the
  CLI while `assets/index.js:304` separately queries Monaco's own language
  registry. Two competing sources of truth.

## Asset Vendoring Decision

ACCEPTED 2026-08-04: **vendor Monaco locally.**

`monaco-editor` is to be shipped under the tool's own assets directory so the
workbench works offline, the version is pinned, and remote script execution is
removed from the CSP. The vendored copy, its version, license, and origin must
be recorded in `_docs/SOURCE_PROVENANCE.md`.

## Non-Goals For This Contract Review

- no runtime implementation,
- no process launch,
- no IPC transport selection,
- no Monaco vendoring yet,
- no dependency install (PySide6, pywebview, qtpy),
- no changes to the existing Tk explorer shell,
- no import/read dependency on the parts bin.
