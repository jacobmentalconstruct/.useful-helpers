# 0023 - MonacoVIEWER Tool Contract Review

Date: 2026-08-04

## Tranche

Root Tranche 14F: MonacoVIEWER Tool Contract Review.

Goal: review the first of the three previously-unreviewed parts-bin apps and
produce a semantic contract for the shared human/agent editing surface.

This tranche was prioritized ahead of Root Tranche 15 because MonacoVIEWER is
the first tool that genuinely requires symmetric human/agent access, so it
constrains the Tool Command Surface Framework rather than consuming it.

Expected completion point:

- reference folder inspected in full,
- target intent recorded separately from reference implementation shape,
- host model decided and recorded,
- contract doc written,
- adapter scaffolded,
- registry exposes the tool as pending,
- tests pin capabilities, decisions, safety gates, and frailties.

Non-goals held:

- no runtime implementation,
- no process launch,
- no IPC transport selection,
- no Monaco vendoring,
- no dependency install (PySide6, pywebview, qtpy),
- no changes to the existing Tk explorer shell,
- no runtime dependency on the parts bin.

## Current State Before Work

`_MonacoVIEWER` was one of three parts-bin apps never reviewed, scaffolded, or
mentioned in any project document. See journal 0022 and the Parts-Bin Coverage
section of `_docs/CURRENT_STATE.md` for how that gap was found and corrected.

The app is small: `src/app.py` is 341 lines, `assets/index.js` is 442, and
`assets/index.html` is 68. It was read in full rather than sampled.

## Key Findings

**The reference is not a Tk integration.** `src/app.py:9` imports `tkinter` with
the comment "Kept for contract compliance, though primary GUI is pywebview" and
never uses it. The real stack is PySide6/Qt driving pywebview, forced at
`src/app.py:13`, with `webview.start()` blocking the main thread at
`src/app.py:255`. Qt and Tk each expect to own the process native event loop, so
this cannot be embedded into the Tk workbench process. The stated project
expectation of "fusing Monaco with Tkinter" does not describe what this code
does; it replaces Tk rather than extending it.

**The reusable half is real.** `js_api=api` (`src/app.py:239`) plus
`window.evaluate_js(...)` gives genuine Python control over a Monaco window, and
the range-edit primitive at `assets/index.js:126`-`:165` is correct: it clamps a
`{start_line, end_line, start_column, end_column, replacement_code}` range
against the model and applies it through `pushEditOperations` as an undoable
operation.

**The agent path contains no agent.** "Agent Surgical Replace"
(`assets/index.js:100`) is a modal textarea a human pastes JSON into, with a
"Copy Schema" button. There is no socket, RPC, or endpoint. The human is the
transport. Nothing can drive it programmatically.

**Nothing propagates into a running session.** CLI edit arguments
(`src/app.py:324`) launch a new window per invocation. There is no event stream;
`set_active_tab` (`assets/index.js:326`) reports state to the host only to
update the window title.

**Headless mode can destroy work.** `src/app.py:283`/`:294` runs `re.subn` and
rewrites the file in place with no dry run, preview, diff, backup, or
confirmation. If the GUI holds that file open with unsaved edits, the write is
silently clobbered. This is a data-loss path in exactly the shared human/agent
scenario the tool is meant to support, and it contradicts the dry-run-first
doctrine already established by the Tokenizing Patcher backend.

**Saves are unsafe.** `_save_logic` (`src/app.py:159`) uses a plain truncating
`open(path, 'w')` with no atomic write, no backup, and no staleness check
against on-disk content. This contradicts the atomic-ish write policy already
accepted in the TextTOUCHER contract.

Full frailty list, including the CDN dependency, the permissive CSP, the
process-wide log filter that rewrites "ERROR" to "WARNING (safe to ignore)", the
leaked untitled temp files, and the duplicated language-inference logic, is
recorded in the contract doc and pinned in tests.

## Decisions

Three decisions were put to the user and accepted 2026-08-04.

1. **Host model: separate process plus session service.** Monaco runs in its own
   Qt/pywebview process exposing an editor session over local IPC. The Tk
   workbench and the agent are equal clients. A GUI button press and an agent
   call travel the same command path and produce the same event record.
   Rejected: embedding a webview in Tk (no supported native Tk webview widget on
   Windows; risks the hardened explorer shell), and migrating the workbench to
   Qt (discards Tranches 14, 14A, 14B, 14C).

2. **Agent surface scope: all four surfaces**, including save to disk. Observe,
   ranged edits, tab management, and gated save. Because save is included, the
   save gate is the most safety-critical part of the contract and is pinned by
   its own test.

3. **Monaco assets: vendor locally.** Pin the version, work offline, and remove
   remote script from the CSP. Provenance to be recorded when vendoring happens.

## Implementation

Added:

- `_docs/MONACO_VIEWER_TOOL_CONTRACT.md`,
- `src/useful_helpers/tools/monaco_viewer/__init__.py`,
- `src/useful_helpers/tools/monaco_viewer/adapter.py`,
- `tests/test_monaco_viewer_adapter_contract.py`.

Updated `src/useful_helpers/tools/registry.py` so the tool appears as
`MonacoVIEWER` with status `contract reviewed; implementation pending;
separate-process session service required`.

The adapter defines nine capabilities: `session_process_lifecycle`,
`session_state_inspection`, `session_event_stream`, `ranged_edit_application`,
`tab_management`, `gated_buffer_save`, `vendored_monaco_assets`,
`headless_text_operations`, and `shared_session_provenance`. It carries 27
reference locators across `src/app.py`, `assets/index.js`, and
`assets/index.html`.

Three rules are stated as named constants and tested directly, so a future agent
cannot quietly weaken them: `HOST_MODEL_RULE`, `SHARED_SESSION_RULE`, and
`SAVE_GATE_RULE`.

## Review Findings And Repairs

No repairs were required. The tranche is additive; the only edit to existing
runtime code was the single registry tuple entry.

Deliberately not done in this tranche: the reference's `--regex-find` headless
path and the Tk workbench's own file-write helpers were not reconciled. They
have overlapping responsibilities and will need one owner, but that is
implementation work, not contract review.

## Verification

Cross-platform partial run (Linux sandbox; no `tkinter`, so the three
Tk-importing modules were excluded):

```bash
python -m pytest -q -p no:cacheprovider \
  --ignore=tests/test_project_mapper_adapter_contract.py \
  --ignore=tests/test_project_mapper_backend.py \
  --ignore=tests/test_ui_theme_contract.py
```

Result: `2 failed, 84 passed`. The two failures are the known Windows-only
assertions recorded in journal 0022, unchanged by this tranche.

Focused run:

```bash
python -m pytest -q -p no:cacheprovider tests/test_monaco_viewer_adapter_contract.py
```

Result: `9 passed`.

Test function count is now 94 (85 before this tranche, plus 9). Debris check
after the run: `_state/` contained only `evidence.sqlite3`.

Authoritative Windows verification: PENDING. Expected `94 passed`. Must be
confirmed with `python -m pytest -q` on the target platform.

## Residual Risks

- The host model is decided but unproven. No IPC transport has been selected and
  no session process has been launched; the separate-process design is sound on
  paper and untested in practice.
- Save is in scope for the agent, which is the highest-risk surface. The save
  gate is specified but not implemented.
- MonacoVIEWER adds heavier runtime dependencies than any existing tool
  (PySide6, pywebview, qtpy). BCC 9 requires these be justified by real need at
  implementation time; the shared editing surface is the justification, but the
  weight should be re-examined before install.
- Vendoring Monaco will add several MB to the repository.
- Two parts-bin apps remain unreviewed: `_TheDISMANTLER` and `_manifold-mcp`.
  Both contain prior art for the Root Tranche 15 command surface.

## Park Point

Root Tranche 14F is complete pending the Windows verification run.

Next recommended action: review `_manifold-mcp` and `_TheDISMANTLER` before
opening Root Tranche 15. `_manifold-mcp` ships an agent-facing MCP tool manifest
and a written contract; `_TheDISMANTLER` ships a tool registration and dispatch
model. Together with this contract's session-service decision, they are the
three inputs that should shape the Tool Command Surface Framework. Designing
that framework without reading them risks inventing a fourth pattern that
conflicts with all three.
