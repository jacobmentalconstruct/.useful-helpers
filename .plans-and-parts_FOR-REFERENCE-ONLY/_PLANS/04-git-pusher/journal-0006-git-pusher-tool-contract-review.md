# Journal Entry 0006: Git Pusher Tool Contract Review

Date: 2026-08-03

## Tranche Declaration

Review the remaining reference app in the parts bin, isolate the functions we
want to incorporate as Useful Helpers tools, populate the related placeholder
Python adapter, and write a semantic overview with searchable locators.

Selected reference app:

`_PARTS-FOR-PLANS/_GitPUSHER/`

## Scope

- Review `_GitPUSHER` as the fourth and final core reference app.
- Identify functions and classes that define repository inspection, git command
  execution, branch management, quick commit/push, pull behavior, repository
  initialization, settings, GUI flow, and packaging evidence.
- Populate `src/useful_helpers/tools/git_pusher/adapter.py` with a semantic tool
  contract and granular capability map.
- Add a documentation overview for the Git Pusher terminal done state and safety gates.
- Record temporary parts-bin locator retirement rules.
- Add repeatable contract tests for the adapter.

## Non-Goals

- No executable git backend implementation in this tranche.
- No GUI git command wiring beyond registry status alignment.
- No actual git add, commit, pull, push, checkout, branch creation, init, or remote command execution.
- No Project Mapper, Tokenizing Patcher, or Line Numberizer backend implementation.
- No deletion of parts-bin references while they are still needed as review anchors.

## Reference Findings

Primary implementation anchors captured from `src/app.py`:

- `class SettingsManager` line 12 and `remote_base_url` line 17 for settings.
- `class GitOpsEngine` line 39 and `def _run` line 43 for subprocess git execution.
- `is_valid_repo` line 50 for repository detection.
- `get_current_branch` line 53, `get_all_branches` line 57, and `checkout_branch` line 63 for branch workflows.
- `get_status_short` line 68 for `git status --porcelain`.
- `def pull` line 72 for pull-before-push behavior.
- `full_init` line 76 for init, main branch, remote, add, commit, and push sequence.
- `class GitPusherUI` line 97 for the old standalone GUI surface.
- `_open_settings` line 239 for settings modal behavior.
- `refresh_state` line 276 for repo/branch/status refresh.
- `_open_branch_manager` line 294 for branch list/create/checkout flow.
- `_on_quick_push` line 349 for quick push workflow.
- `Continue pushing anyway` line 368 for pull-failure override.
- `self.engine._run(["add", "."])` line 374 for unsafe broad staging.
- `self.engine._run(["push"])` line 379 for push execution.
- `_on_full_init` line 390 for initialize-and-push workflow.

Other anchors:

- README `Features` line 5.
- README `CLI Arguments Reference` line 60.
- README `Safety Mechanisms` line 69.
- `settings.json` `remote_base_url` line 2.
- `_GitPUSHER.spec` `Analysis` line 4.

## Reference Frailties

- README advertises CLI mode, but `src/app.py` has no `argparse` or CLI entrypoint.
- README advertises a `.gitignore` stop-gap, but `src/app.py` does not implement a `.gitignore` check.
- Quick push stages every file with `git add .`, which is too broad for Useful Helpers without an explicit working-set gate.
- Pull failure can be overridden and push can continue; Useful Helpers must treat this as a high-risk confirmation path.
- `settings.json` contains a default remote-base value that differs from the source-code default.
- `_GitPUSHER.spec` contains old absolute local paths and is packaging provenance only.

## Changes

- Replaced `src/useful_helpers/tools/git_pusher/adapter.py` placeholder with a dataclass-backed semantic contract.
- Updated `src/useful_helpers/tools/registry.py` to show Git Pusher as contract-reviewed and implementation-pending.
- Added `tests/test_git_pusher_adapter_contract.py`.
- Added `_docs/GIT_PUSHER_TOOL_CONTRACT.md`.
- Updated `_docs/SOURCE_PROVENANCE.md` with Git Pusher review provenance.
- Updated `_docs/CURRENT_STATE.md` with all four core tool contracts.
- Updated `_docs/PROJECT_PLAN.md` with Root Tranche 5 and revised next tranche sequence.
- Updated `_docs/ARCHITECTURE.md` with Git Pusher safety boundaries.

## Decisions

- Treat Git Pusher as a high-risk tool family requiring stronger safety gates than the reference app.
- Do not inherit `git add .` as the only staging path; Useful Helpers must stage explicit explorer-selected paths by default.
- Implement backend inspection/safety behavior before GUI command wiring.
- Require confirmation and command result logging for every mutating operation.
- Treat CLI support as a desired Useful Helpers capability because the README promises it, even though the source app does not implement it.
- Treat old PyInstaller spec and personal remote defaults as provenance only, not runtime defaults.
- Keep parts-bin paths in runtime adapter only while implementation recovery still depends on them.

## Validation

- `python -m pytest -q -p no:cacheprovider`: `21 passed`.
- `python src\app.py --status`: root status smoke passed with `0.2.0-root-shell`.
- `rg -n "PARTS-BIN|_GitPUSHER|_LineNUMBERIZER|_TokenizingPATCHER|_ProjectMAPPER|from \.PARTS|import .*GitPUSHER|import .*LineNUMBERIZER|import .*Tokenizing|import .*ProjectMAPPER" _docs BCC.md src tests _journal --hidden --no-ignore`: intentional references only.
- `rg -n "placeholder" _docs src tests _journal --hidden --no-ignore`: no remaining placeholder status for the four core app adapters; historical journal mentions and UI placeholder-shell text remain intentional.
- Generated root `src/` and `tests/` cache debris was removed after verification. Preexisting parts-bin virtual-environment caches were left untouched.

## Review and Repair Notes

- Issue found: current-state verification lines were pending before checks. Repaired with actual verification results.
- Issue found: reference README claimed CLI and `.gitignore` safety behavior that source did not implement. Recorded as contract frailties rather than inheriting the claims.
- Issue found: reference quick-push uses `git add .`. Contract repaired this into a required explicit working-set staging rule for Useful Helpers.

## Risks and Backlog

- The Git Pusher backend is not implemented yet.
- Git operations are high-risk and need temporary-repo tests plus strong confirmation semantics.
- Explorer inclusion state must be hardened before explicit-path staging can be ergonomic.
- Temporary parts-bin locators in reviewed adapters must not be mistaken for runtime imports.

## Park State

Parked after verification and cleanup. All four core reference apps are now contract-reviewed; recommended next tranche is Project Mapper Backend Implementation.
