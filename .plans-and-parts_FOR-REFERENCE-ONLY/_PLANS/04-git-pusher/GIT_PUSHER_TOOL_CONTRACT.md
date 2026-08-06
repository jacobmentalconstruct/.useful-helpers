# Git Pusher Tool Contract

Status: backend implemented; GUI/CLI wiring pending

Date: 2026-08-03

## Reference Dependency Rule

Reference app reviewed:

`_PARTS-FOR-PLANS/_GitPUSHER/src/app.py`

Reference settings observed:

`_PARTS-FOR-PLANS/_GitPUSHER/settings.json`

Packaging spec observed:

`_PARTS-FOR-PLANS/_GitPUSHER/_GitPUSHER.spec`

The locators in this document and in
`src/useful_helpers/tools/git_pusher/adapter.py` are temporary review anchors.
They may guide implementation, but the Useful Helpers runtime must not import
from, read from, or require the parts-bin app.

When a Git Pusher capability is fully re-homed, remove the corresponding
parts-bin locator from runtime tool code. Historical provenance may remain in
this document or `_docs/SOURCE_PROVENANCE.md`.

## Reference Frailties Found

- README advertises CLI mode, but `src/app.py` has no `argparse` or CLI entrypoint.
- README advertises a `.gitignore` stop-gap, but `src/app.py` does not implement a `.gitignore` check.
- Quick push stages every file with `git add .`, which is too broad for Useful Helpers without an explicit working-set gate.
- Pull failure can be overridden and push can continue; Useful Helpers must treat this as a high-risk confirmation path.
- `settings.json` contains a default remote-base value that differs from the source-code default.

## Tool Done State

The Git Pusher tool family is done when Useful Helpers can inspect a target
repository, show branch/status/remote state, validate safety gates, stage and
commit only an explicit user-approved working set, optionally pull and push with
clear confirmation, initialize a repository only through an explicit setup
workflow, manage branches with visible dirty-state checks, record
stdout/stderr/exit codes for every git command, and do all of that from local
Useful Helpers modules with no runtime dependency on the parts-bin reference app.

Safety stop state:

No mutating git operation is complete until it has a dry-run/previewable plan,
verifies the selected repository root, reports dirty status, checks for
`.gitignore` or equivalent exclusion risk, requires an explicit user
confirmation for commits, pushes, pulls, branch checkout/create, init, and
remote setup, and never runs `git add .` as the only available staging mode.

## Capability Map

### Inspect Repository State

Target outcome:

Given a selected project root, determine whether it is a git repo, show current
branch, concise working-tree status, and command errors.

Expected inputs:

- repository path

Expected outputs:

- repo validity
- current branch
- porcelain status
- git availability errors

Reference anchors:

- `class GitOpsEngine` at line 39
- `def _run` at line 43
- `is_valid_repo` at line 50
- `get_current_branch` at line 53
- `get_status_short` at line 68
- `refresh_state` at line 276

Search locator:

```bat
rg -n "class GitOpsEngine|def _run|is_valid_repo|get_current_branch|get_status_short|refresh_state" "_PARTS-FOR-PLANS\_GitPUSHER\src\app.py"
```

Done when:

Useful Helpers can inspect git state without mutating files or remote state, and
can show this state in the right pane/tool surface.

### Validate Git Safety Gates

Target outcome:

Block or warn before risky git operations when repo root, `.gitignore`,
working-set staging, branch state, pull state, or remote setup is unsafe.

Expected inputs:

- repository path
- operation plan
- explorer inclusion set
- user confirmation state

Expected outputs:

- safety findings
- blocked/warn/allowed decision
- required confirmations

Reference anchors:

- README `Safety Mechanisms` at line 69
- `get_status_short` at line 68
- `is_valid_repo` at line 50
- `self.engine._run(["add", "."])` at line 374
- `Continue pushing anyway` at line 368

Done when:

No mutating git operation runs until Useful Helpers has a dry-run/previewable
plan, verified repo root, dirty status, `.gitignore`/exclusion-risk check,
explicit confirmation, and a staging mode more precise than only `git add .`.

### Stage Explicit Working Set

Target outcome:

Stage only checked files/folders or a reviewed file list from the Useful Helpers
explorer instead of blindly staging the whole repo.

Expected inputs:

- repository path
- explorer operation inclusion set
- status records

Expected outputs:

- staged paths
- skipped paths
- git command records

Reference anchors:

- `self.engine._run(["add", "."])` at line 374
- `get_status_short` at line 68
- `_on_quick_push` at line 349

Done when:

The user can see exactly what will be staged, and backend tests prove the adapter
can build path-specific `git add` commands.

### Commit Changes

Target outcome:

Create a git commit with an explicit message after staging has passed safety
checks and the user confirms the final plan.

Expected inputs:

- repository path
- commit message
- staged path summary
- confirmation token

Expected outputs:

- commit command record
- commit stdout/stderr
- commit success/failure

Reference anchors:

- `_on_quick_push` at line 349
- `get_status_short` at line 68

Done when:

Useful Helpers refuses empty commit messages, reports nothing-to-commit states
clearly, and records the commit command result.

### Pull Before Push

Target outcome:

Optionally pull from the current branch's upstream before push, with
conflict/failure handling that defaults to stop.

Expected inputs:

- repository path
- current branch
- user pull option
- confirmation state

Expected outputs:

- pull command record
- pull stdout/stderr
- blocked push decision on failure

Reference anchors:

- `def pull` at line 72
- `get_current_branch` at line 53
- `Continue pushing anyway` at line 368
- `_on_quick_push` at line 349

Done when:

Pull failure does not proceed to push unless a high-risk confirmation path is
explicit, visible, and logged.

### Push Commits

Target outcome:

Push committed changes to the configured upstream/default remote after
inspection, optional pull, and confirmation.

Expected inputs:

- repository path
- remote/upstream state
- confirmation token

Expected outputs:

- push command record
- push stdout/stderr
- push success/failure

Reference anchors:

- `self.engine._run(["push"])` at line 379
- `_on_quick_push` at line 349

Done when:

Push is never hidden behind staging/commit side effects and always shows command
output and failure state.

### Manage Branches

Target outcome:

List, checkout, and create branches with dirty-state checks and explicit
confirmation before changing branch state.

Expected inputs:

- repository path
- branch action
- target branch
- confirmation state

Expected outputs:

- branch list
- checkout/create command result
- dirty-state warnings

Reference anchors:

- `get_all_branches` at line 57
- `checkout_branch` at line 63
- `_open_branch_manager` at line 294
- `get_status_short` at line 68

Done when:

Branch changes are blocked or confirmed when the working tree is dirty, and the
UI refreshes branch/status after success.

### Initialize Repository And Remote

Target outcome:

Initialize a repository, set main branch, add remote, create initial commit, and
push only through a deliberate setup workflow.

Expected inputs:

- target folder
- remote URL
- initial commit message
- confirmation token

Expected outputs:

- step-by-step command records
- initialized repo result
- push result

Reference anchors:

- `full_init` at line 76
- `_on_full_init` at line 390
- source `remote_base_url` at line 17
- settings file `remote_base_url` at line 2

Search locator:

```bat
rg -n "remote_base_url|full_init|_on_full_init|self.engine._run\(\[\"add\", \"\.\"\]\)|self.engine._run\(\[\"push\"\]\)" "_PARTS-FOR-PLANS\_GitPUSHER\src\app.py" "_PARTS-FOR-PLANS\_GitPUSHER\settings.json"
```

Done when:

Full initialization has a previewable step plan, validates URL/message, checks
`.gitignore` risk, and records each command result.

### Manage Git Pusher Settings

Target outcome:

Store non-secret user preferences such as default remote base URL in Useful
Helpers configuration without embedding personal defaults in runtime code.

Expected inputs:

- settings file
- remote base URL
- user update

Expected outputs:

- persisted settings
- settings validation messages

Reference anchors:

- `class SettingsManager` at line 12
- `_open_settings` at line 239
- source `remote_base_url` at line 17
- settings file `remote_base_url` at line 2

Done when:

Settings are local, inspectable, non-secret, and do not leak old personal paths
or defaults into a vendorable Useful Helpers runtime.

### Git Pusher GUI Workflow

Target outcome:

Present repository selection, status, branches, commit message, pull option,
push/init controls, confirmations, and logs inside Useful Helpers.

Expected inputs:

- selected project root
- git operation options
- confirmation decisions

Expected outputs:

- operation form state
- command logs
- success/error messages

Reference anchors:

- `class GitPusherUI` at line 97
- `refresh_state` at line 276
- `_open_branch_manager` at line 294
- `_on_quick_push` at line 349
- `_on_full_init` at line 390

Done when:

The GUI exposes the expected git controls but routes through local
safety-checked adapters, not the reference app or raw hidden commands.

### CLI Compatibility

Target outcome:

Provide the CLI behavior promised by the reference README, even though the
inspected source app does not currently implement it.

Expected inputs:

- repo path
- message
- push-only
- force-without-gitignore
- dry-run/confirm policy

Expected outputs:

- exit code
- stdout/stderr message
- optional git operation results

Reference anchors:

- README `CLI Arguments Reference` at line 60
- README `Safety Mechanisms` at line 69
- `def _run` at line 43

Done when:

A headless path can inspect, dry-run, commit, and push through local Useful
Helpers code with the same safety gates as the GUI.

### Packaging Reference Only

Target outcome:

Treat the old PyInstaller spec as historical packaging evidence, not as a Useful
Helpers runtime or build dependency.

Reference anchors:

- `_GitPUSHER.spec` `Analysis` at line 4

Done when:

Useful Helpers packaging is designed separately and contains no old absolute
local paths from the reference spec.


## Current Implementation State

Root Tranche 13 implemented the first executable Git Pusher backend at
`src/useful_helpers/tools/git_pusher/backend.py`.

Implemented now:

- repository inspection and porcelain-status parsing,
- remotes and branch list inspection,
- command records with command tuple, cwd, stdout, stderr, exit code, and ok flag,
- safety reports with blockers, warnings, required confirmations, preview commands, and normalized selected paths,
- selected-path-only staging and stage/commit behavior,
- pull and push command execution behind confirmation and remote/branch validation,
- branch checkout/create behind confirmation and dirty-state gates,
- repository init with explicit branch naming, optional selected-path commit, optional remote setup, and optional push,
- non-secret settings load/save helpers,
- CLI-compatible dry-run/execute wrapper for later command wiring.

Still pending:

- Useful Helpers GUI command surfaces,
- actual CLI argument parser/wrapper,
- progress/cancel/log rendering in the right pane or tool dialog,
- retirement of runtime adapter reference locators after the project no longer needs them for implementation recovery.
## Implementation Notes

- The inspected source is GUI-only despite README CLI claims; CLI compatibility
  must be implemented from the contract, not assumed present.
- The README `.gitignore` stop-gap is not present in `src/app.py`; Useful
  Helpers must implement its own safety gate.
- `git add .` in the reference app is not acceptable as the only staging mode.
  Useful Helpers should stage explicit explorer-selected paths by default.
- Mutating operations require confirmation and logged command records.
- Old remote defaults must not be copied as runtime defaults.
- The PyInstaller spec contains old absolute local paths and is provenance only.
- The typo in the parts-bin folder name is preserved in locators because it is
  the actual folder path.
