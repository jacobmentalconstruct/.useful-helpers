# Journal 0009: ChatWindowKERNAL Tool Contract Review

Date: 2026-08-03

## BCC Anchors

- `BCC-SPINE`
- `BCC-WORKFLOW-REQUIRED-TRANCHE-LOOP`
- `BCC-REFERENCE-SOURCE-RULE`
- `BCC-DOCS-REPORTING`
- `BCC-JOURNAL-LOGGING`

## User Request

Scaffold `_ChatWindowKERNAL` in the same way as the previous reviewed reference
apps, while noting that it needs more work before its layout is final and
currently functions in a very perfunctory, non-chat way.

## Current State Before Work

- Four core reference app contracts were reviewed.
- UiMAPPER and TextTOUCHER were reviewed as additional non-core/reference-app
  tool contracts.
- `_ChatWindowKERNAL` existed in the parts bin but had not yet been reviewed or
  added to the Useful Helpers tool registry.

## Reference Review

Reviewed `_ChatWindowKERNAL` files:

- `README.md`
- `app.py`
- `config/`
- `src/shell/`
- `src/ui/`
- `src/runtime/`
- `tool_packages/`

State databases, logs, runtime snapshots, and crash reports were observed but
treated as provenance only.

## Decisions

- Add ChatWindowKERNAL as a reviewed tool contract, not an implemented backend.
- Preserve useful host-kernel patterns: service graph, panel mounting, task
  queue, activity stream, data hooks, snapshots, crash reports, and optional
  adapter seam.
- Explicitly mark the reference chat layout as not final.
- Require a later design tranche before any ChatWindowKERNAL UI is accepted as
  product shape.
- Preserve the source spelling `KERNAL` in locators/tool key because it is the
  actual reference name.
- Keep vendored Mindshard and numpy dependency behind a deferred optional adapter
  seam.

## Changes Made

- Added `src/useful_helpers/tools/chat_window_kernal/adapter.py`.
- Added `src/useful_helpers/tools/chat_window_kernal/__init__.py`.
- Added `tests/test_chat_window_kernal_adapter_contract.py`.
- Added `_docs/CHAT_WINDOW_KERNAL_TOOL_CONTRACT.md`.
- Added ChatWindowKERNAL to `src/useful_helpers/tools/registry.py`.
- Updated `_docs/SOURCE_PROVENANCE.md`.
- Updated `_docs/ARCHITECTURE.md`.
- Updated `_docs/PROJECT_PLAN.md`.
- Updated `_docs/CURRENT_STATE.md`.

## Capability Groups Captured

- `chat_layout_rework_required`
- `bootstrap_host_kernel`
- `compose_chat_and_workspace_shell`
- `render_conversational_messages`
- `capture_chat_input_and_controls`
- `manage_sessions_models_and_loops`
- `host_agent_turns_and_hitl`
- `discover_and_run_tool_packages`
- `show_activity_events_hooks_and_inspector`
- `queue_background_tasks`
- `persist_state_and_runtime_snapshots`
- `structured_logging_and_crash_reports`
- `optional_mindshard_adapter_seam`

## Known Risks

- Layout is not final and currently feels perfunctory/non-chat.
- Transcript rendering is plain role/text appending.
- Checked-in runtime artifacts must not become migration inputs.
- Vendored Mindshard and numpy dependency are too broad for implicit runtime use.
- Debug crash controls must be gated before any user-facing integration.

## Parked State

ChatWindowKERNAL is scaffolded as a reviewed semantic contract with searchable
locators. Implementation remains pending, and layout redesign is required before
product acceptance.
