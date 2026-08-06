"""Git Pusher tool contract and reference implementation map.

This module is intentionally semantic, not operational. It defines the Git
Pusher behavior Useful Helpers may re-home from the reference app before runtime
adapters start inspecting repositories or running git operations.

Temporary reference rule:
The parts-bin locators below are implementation review anchors only. When the
Git Pusher tool no longer depends on the reference app for design recovery,
runtime modules must not import from, read from, or require the parts bin.
"""

from __future__ import annotations

from useful_helpers.tools.contracts import ReferenceLocator, ToolCapability, ToolContract


TOOL_KEY = "git_pusher"
TOOL_LABEL = "Git Pusher"
STATUS = "backend implemented; GUI/CLI wiring pending"

SOURCE_REFERENCE = "_PARTS-FOR-PLANS/_GitPUSHER/"
REFERENCE_APP_PATH = f"{SOURCE_REFERENCE}src/app.py"
REFERENCE_SETTINGS_PATH = f"{SOURCE_REFERENCE}settings.json"
REFERENCE_SPEC_PATH = f"{SOURCE_REFERENCE}_GitPUSHER.spec"

REFERENCE_RETIREMENT_RULE = (
    "Parts-bin references are temporary review anchors. Once each git workflow "
    "capability is re-homed into Useful Helpers runtime modules, remove "
    "parts-bin references from runtime tool code and keep historical provenance "
    "in docs only."
)

DONE_STATE = (
    "Git Pusher integration is complete when Useful Helpers can inspect a target "
    "repository, show branch/status/remote state, validate safety gates, stage "
    "and commit only an explicit user-approved working set, optionally pull and "
    "push with clear confirmation, initialize a repository only through an "
    "explicit setup workflow, manage branches with visible dirty-state checks, "
    "record stdout/stderr/exit codes for every git command, and do all of that "
    "from local Useful Helpers modules with no runtime dependency on the parts-bin "
    "reference app."
)

SAFETY_DONE_STATE = (
    "No mutating git operation is complete until it has a dry-run/previewable "
    "plan, verifies the selected repository root, reports dirty status, checks "
    "for .gitignore or equivalent exclusion risk, requires an explicit user "
    "confirmation for commits, pushes, pulls, branch checkout/create, init, and "
    "remote setup, and never runs git add . as the only available staging mode."
)

REFERENCE_FRAILTIES = (
    "README advertises CLI mode, but src/app.py has no argparse or CLI entrypoint.",
    "README advertises a .gitignore stop-gap, but src/app.py does not implement a .gitignore check.",
    "Quick push stages every file with git add ., which is too broad for Useful Helpers without an explicit working-set gate.",
    "Pull failure can be overridden and push can continue; Useful Helpers must treat this as a high-risk confirmation path.",
    "Settings contain a default remote-base value that differs from the source-code default.",
)


def app_locator(label: str, symbol: str, line: int, purpose: str) -> ReferenceLocator:
    return ReferenceLocator(label, symbol, line, purpose, REFERENCE_APP_PATH)


LOC_README_FEATURES = ReferenceLocator(
    "README feature list",
    "Features",
    5,
    "Describes hybrid interface, add/commit/push automation, safety claims, and recursion detection claims.",
    f"{SOURCE_REFERENCE}README.md",
)
LOC_README_CLI = ReferenceLocator(
    "README CLI reference",
    "CLI Arguments Reference",
    60,
    "Documents desired repo/message/push-only/force-without-gitignore arguments not found in source app.py.",
    f"{SOURCE_REFERENCE}README.md",
)
LOC_README_SAFETY = ReferenceLocator(
    "README safety mechanisms",
    "Safety Mechanisms",
    69,
    "Documents .gitignore and porcelain-status safety expectations.",
    f"{SOURCE_REFERENCE}README.md",
)
LOC_SETTINGS_MANAGER = app_locator(
    "settings manager",
    "class SettingsManager",
    12,
    "Loads and saves local JSON settings for default remote base URL.",
)
LOC_SETTINGS_DEFAULT = app_locator(
    "settings default remote",
    "remote_base_url",
    17,
    "Defines source-code default remote base URL.",
)
LOC_SETTINGS_FILE = ReferenceLocator(
    "settings file remote",
    "remote_base_url",
    2,
    "Defines checked-in settings remote base URL, which differs from source default.",
    REFERENCE_SETTINGS_PATH,
)
LOC_GIT_ENGINE = app_locator(
    "git operations engine",
    "class GitOpsEngine",
    39,
    "Wraps subprocess git operations against a selected repository path.",
)
LOC_RUN = app_locator(
    "git command runner",
    "def _run",
    43,
    "Runs git subprocess commands and returns exit code, stdout, and stderr.",
)
LOC_VALID_REPO = app_locator(
    "repository validation",
    "is_valid_repo",
    50,
    "Checks whether the selected path contains a .git directory.",
)
LOC_CURRENT_BRANCH = app_locator(
    "current branch",
    "get_current_branch",
    53,
    "Reads the current branch with git branch --show-current.",
)
LOC_ALL_BRANCHES = app_locator(
    "all branches",
    "get_all_branches",
    57,
    "Lists local branches from git branch output.",
)
LOC_CHECKOUT_BRANCH = app_locator(
    "checkout branch",
    "checkout_branch",
    63,
    "Checks out existing branches or creates and checks out a new branch.",
)
LOC_STATUS = app_locator(
    "porcelain status",
    "get_status_short",
    68,
    "Reads git status --porcelain for concise working-tree state.",
)
LOC_PULL = app_locator(
    "pull current branch",
    "def pull",
    72,
    "Runs git pull origin <current-branch>.",
)
LOC_FULL_INIT = app_locator(
    "full repository init",
    "full_init",
    76,
    "Runs git init, branch rename, remote add, add ., commit, and push -u.",
)
LOC_UI = app_locator(
    "Git Pusher UI",
    "class GitPusherUI",
    97,
    "Defines Tk workbench for repo path, quick push, initialize, branches, settings, status, and logs.",
)
LOC_SETTINGS_MODAL = app_locator(
    "settings modal",
    "_open_settings",
    239,
    "Updates and persists default remote base URL.",
)
LOC_REFRESH = app_locator(
    "refresh repository state",
    "refresh_state",
    276,
    "Refreshes repo validity, branch label, and porcelain status display.",
)
LOC_BRANCH_MANAGER = app_locator(
    "branch manager",
    "_open_branch_manager",
    294,
    "Shows branches and supports checkout/create branch actions.",
)
LOC_QUICK_PUSH = app_locator(
    "quick push workflow",
    "_on_quick_push",
    349,
    "Validates repo and commit message, optionally pulls, runs git add ., commit, then push.",
)
LOC_PULL_OVERRIDE = app_locator(
    "pull failure override",
    "Continue pushing anyway",
    368,
    "Shows the reference app's high-risk path for pushing after pull failure.",
)
LOC_ADD_ALL = app_locator(
    "stage all files",
    'self.engine._run(["add", "."])',
    374,
    "Stages every file in the repo; Useful Helpers should replace with explicit working-set staging.",
)
LOC_PUSH = app_locator(
    "push command",
    'self.engine._run(["push"])',
    379,
    "Pushes committed changes to the configured upstream/default remote.",
)
LOC_FULL_INIT_UI = app_locator(
    "full init UI workflow",
    "_on_full_init",
    390,
    "Reads remote URL and message, then runs full repository initialization and push.",
)
LOC_SPEC = ReferenceLocator(
    "PyInstaller spec",
    "Analysis",
    4,
    "Packages the old standalone app from local absolute paths; not a runtime contract for Useful Helpers.",
    REFERENCE_SPEC_PATH,
)


CAPABILITIES = (
    ToolCapability(
        key="inspect_repository_state",
        label="Inspect Repository State",
        target_outcome=(
            "Given a selected project root, determine whether it is a git repo, "
            "show current branch, concise working-tree status, and command errors."
        ),
        expected_inputs=("repository path",),
        expected_outputs=("repo validity", "current branch", "porcelain status", "git availability errors"),
        reference_locators=(LOC_GIT_ENGINE, LOC_RUN, LOC_VALID_REPO, LOC_CURRENT_BRANCH, LOC_STATUS, LOC_REFRESH),
        done_when=(
            "Useful Helpers can inspect git state without mutating files or remote "
            "state, and can show this state in the right pane/tool surface."
        ),
        implementation_owner="useful_helpers.tools.git_pusher inspect module",
    ),
    ToolCapability(
        key="validate_git_safety_gates",
        label="Validate Git Safety Gates",
        target_outcome=(
            "Block or warn before risky git operations when repo root, .gitignore, "
            "working-set staging, branch state, pull state, or remote setup is unsafe."
        ),
        expected_inputs=("repository path", "operation plan", "explorer inclusion set", "user confirmation state"),
        expected_outputs=("safety findings", "blocked/warn/allowed decision", "required confirmations"),
        reference_locators=(LOC_README_SAFETY, LOC_STATUS, LOC_VALID_REPO, LOC_ADD_ALL, LOC_PULL_OVERRIDE),
        done_when=SAFETY_DONE_STATE,
        implementation_owner="useful_helpers.tools.git_pusher safety module",
    ),
    ToolCapability(
        key="stage_explicit_working_set",
        label="Stage Explicit Working Set",
        target_outcome=(
            "Stage only checked files/folders or a reviewed file list from the "
            "Useful Helpers explorer instead of blindly staging the whole repo."
        ),
        expected_inputs=("repository path", "explorer operation inclusion set", "status records"),
        expected_outputs=("staged paths", "skipped paths", "git command records"),
        reference_locators=(LOC_ADD_ALL, LOC_STATUS, LOC_QUICK_PUSH),
        done_when=(
            "The user can see exactly what will be staged, and backend tests prove "
            "the adapter can build path-specific git add commands."
        ),
        implementation_owner="useful_helpers.tools.git_pusher staging module",
    ),
    ToolCapability(
        key="commit_changes",
        label="Commit Changes",
        target_outcome=(
            "Create a git commit with an explicit message after staging has passed "
            "safety checks and the user confirms the final plan."
        ),
        expected_inputs=("repository path", "commit message", "staged path summary", "confirmation token"),
        expected_outputs=("commit command record", "commit stdout/stderr", "commit success/failure"),
        reference_locators=(LOC_QUICK_PUSH, LOC_STATUS),
        done_when=(
            "Useful Helpers refuses empty commit messages, reports nothing-to-commit "
            "states clearly, and records the commit command result."
        ),
        implementation_owner="useful_helpers.tools.git_pusher commit module",
    ),
    ToolCapability(
        key="pull_before_push",
        label="Pull Before Push",
        target_outcome=(
            "Optionally pull from the current branch's upstream before push, with "
            "conflict/failure handling that defaults to stop."
        ),
        expected_inputs=("repository path", "current branch", "user pull option", "confirmation state"),
        expected_outputs=("pull command record", "pull stdout/stderr", "blocked push decision on failure"),
        reference_locators=(LOC_PULL, LOC_CURRENT_BRANCH, LOC_PULL_OVERRIDE, LOC_QUICK_PUSH),
        done_when=(
            "Pull failure does not proceed to push unless a high-risk confirmation "
            "path is explicit, visible, and logged."
        ),
        implementation_owner="useful_helpers.tools.git_pusher sync module",
    ),
    ToolCapability(
        key="push_commits",
        label="Push Commits",
        target_outcome=(
            "Push committed changes to the configured upstream/default remote after "
            "inspection, optional pull, and confirmation."
        ),
        expected_inputs=("repository path", "remote/upstream state", "confirmation token"),
        expected_outputs=("push command record", "push stdout/stderr", "push success/failure"),
        reference_locators=(LOC_PUSH, LOC_QUICK_PUSH),
        done_when=(
            "Push is never hidden behind staging/commit side effects and always "
            "shows command output and failure state."
        ),
        implementation_owner="useful_helpers.tools.git_pusher push module",
    ),
    ToolCapability(
        key="manage_branches",
        label="Manage Branches",
        target_outcome=(
            "List, checkout, and create branches with dirty-state checks and "
            "explicit confirmation before changing branch state."
        ),
        expected_inputs=("repository path", "branch action", "target branch", "confirmation state"),
        expected_outputs=("branch list", "checkout/create command result", "dirty-state warnings"),
        reference_locators=(LOC_ALL_BRANCHES, LOC_CHECKOUT_BRANCH, LOC_BRANCH_MANAGER, LOC_STATUS),
        done_when=(
            "Branch changes are blocked or confirmed when the working tree is dirty, "
            "and the UI refreshes branch/status after success."
        ),
        implementation_owner="useful_helpers.tools.git_pusher branch module",
    ),
    ToolCapability(
        key="initialize_repository_remote",
        label="Initialize Repository And Remote",
        target_outcome=(
            "Initialize a repository, set main branch, add remote, create initial "
            "commit, and push only through a deliberate setup workflow."
        ),
        expected_inputs=("target folder", "remote URL", "initial commit message", "confirmation token"),
        expected_outputs=("step-by-step command records", "initialized repo result", "push result"),
        reference_locators=(LOC_FULL_INIT, LOC_FULL_INIT_UI, LOC_SETTINGS_DEFAULT, LOC_SETTINGS_FILE),
        done_when=(
            "Full initialization has a previewable step plan, validates URL/message, "
            "checks .gitignore risk, and records each command result."
        ),
        implementation_owner="useful_helpers.tools.git_pusher init module",
    ),
    ToolCapability(
        key="manage_git_pusher_settings",
        label="Manage Git Pusher Settings",
        target_outcome=(
            "Store non-secret user preferences such as default remote base URL in "
            "Useful Helpers configuration without embedding personal defaults in runtime code."
        ),
        expected_inputs=("settings file", "remote base URL", "user update"),
        expected_outputs=("persisted settings", "settings validation messages"),
        reference_locators=(LOC_SETTINGS_MANAGER, LOC_SETTINGS_MODAL, LOC_SETTINGS_DEFAULT, LOC_SETTINGS_FILE),
        done_when=(
            "Settings are local, inspectable, non-secret, and do not leak old personal "
            "paths or defaults into a vendorable Useful Helpers runtime."
        ),
        implementation_owner="useful_helpers.tools.git_pusher settings module",
    ),
    ToolCapability(
        key="git_pusher_gui_workflow",
        label="Git Pusher GUI Workflow",
        target_outcome=(
            "Present repository selection, status, branches, commit message, pull "
            "option, push/init controls, confirmations, and logs inside Useful Helpers."
        ),
        expected_inputs=("selected project root", "git operation options", "confirmation decisions"),
        expected_outputs=("operation form state", "command logs", "success/error messages"),
        reference_locators=(LOC_UI, LOC_REFRESH, LOC_BRANCH_MANAGER, LOC_QUICK_PUSH, LOC_FULL_INIT_UI),
        done_when=(
            "The GUI exposes the expected git controls but routes through local "
            "safety-checked adapters, not the reference app or raw hidden commands."
        ),
        implementation_owner="Useful Helpers UI plus git_pusher adapter",
    ),
    ToolCapability(
        key="cli_compatibility",
        label="CLI Compatibility",
        target_outcome=(
            "Provide the CLI behavior promised by the reference README, even though "
            "the inspected source app does not currently implement it."
        ),
        expected_inputs=("repo path", "message", "push-only", "force-without-gitignore", "dry-run/confirm policy"),
        expected_outputs=("exit code", "stdout/stderr message", "optional git operation results"),
        reference_locators=(LOC_README_CLI, LOC_README_SAFETY, LOC_RUN),
        done_when=(
            "A headless path can inspect, dry-run, commit, and push through local "
            "Useful Helpers code with the same safety gates as the GUI."
        ),
        implementation_owner="useful_helpers.tools.git_pusher cli module",
    ),
    ToolCapability(
        key="packaging_reference_only",
        label="Packaging Reference Only",
        target_outcome=(
            "Treat the old PyInstaller spec as historical packaging evidence, not "
            "as a Useful Helpers runtime or build dependency."
        ),
        expected_inputs=("none for runtime",),
        expected_outputs=("deferred packaging note",),
        reference_locators=(LOC_SPEC,),
        done_when=(
            "Useful Helpers packaging is designed separately and contains no old "
            "absolute local paths from the reference spec."
        ),
        implementation_owner="deferred packaging tranche",
    ),
)


GIT_PUSHER_CONTRACT = ToolContract(
    key=TOOL_KEY,
    label=TOOL_LABEL,
    status=STATUS,
    source_reference=SOURCE_REFERENCE,
    reference_app_path=REFERENCE_APP_PATH,
    reference_retirement_rule=REFERENCE_RETIREMENT_RULE,
    done_state=DONE_STATE,
    capabilities=CAPABILITIES,
)


def get_tool_contract() -> ToolContract:
    """Return the semantic integration contract for the Git Pusher tool."""

    return GIT_PUSHER_CONTRACT


def list_capabilities() -> tuple[ToolCapability, ...]:
    """Return all Git Pusher capabilities currently planned for re-homing."""

    return GIT_PUSHER_CONTRACT.capabilities


def has_temporary_reference_locators() -> bool:
    """Return True while runtime tool code still carries parts-bin anchors."""

    return bool(GIT_PUSHER_CONTRACT.reference_app_path)


def reference_dependency_notice() -> str:
    """Return the rule that governs when reference locators must be retired."""

    return GIT_PUSHER_CONTRACT.reference_retirement_rule
