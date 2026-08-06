"""Tokenizing Patcher tool contract and reference implementation map.

This module is intentionally semantic, not operational. It defines the
Tokenizing Patcher behavior Useful Helpers will re-home from the reference app
before runtime adapters start validating or applying patches.

Temporary reference rule:
The parts-bin locators below are implementation review anchors only. When the
Tokenizing Patcher tool no longer depends on the reference app for design
recovery, runtime modules must not import from, read from, or require the parts
bin.
"""

from __future__ import annotations

from useful_helpers.tools.contracts import ReferenceLocator, ToolCapability, ToolContract


TOOL_KEY = "tokenizing_patcher"
TOOL_LABEL = "Tokenizing Patcher"
STATUS = "backend implemented; GUI/CLI wiring pending"

SOURCE_REFERENCE = "_PARTS-FOR-PLANS/_TokenizingPATCHER/"
REFERENCE_APP_PATH = f"{SOURCE_REFERENCE}src/app.py"
REFERENCE_BACKUP_PATH = f"{SOURCE_REFERENCE}src/app_ORIGINAL.py"

REFERENCE_RETIREMENT_RULE = (
    "Parts-bin references are temporary review anchors. Once each patching "
    "capability is re-homed into Useful Helpers runtime modules, remove "
    "parts-bin references from runtime tool code and keep historical provenance "
    "in docs only."
)

DONE_STATE = (
    "Tokenizing Patcher integration is complete when Useful Helpers can build, "
    "validate, preview, and apply structured JSON hunk patches against one or "
    "many explorer-selected text files; preserve newline style and indentation "
    "intent; detect missing, ambiguous, and overlapping hunks before writes; "
    "show per-file diffs and errors; optionally write versioned outputs; and do "
    "all of that from local Useful Helpers modules with no runtime dependency on "
    "the parts-bin reference app."
)


def reference_locator(label: str, symbol: str, line: int, purpose: str) -> ReferenceLocator:
    return ReferenceLocator(label, symbol, line, purpose, REFERENCE_APP_PATH)


LOC_README_SCHEMA = ReferenceLocator(
    "README patch schema",
    "Patch Schema Definition",
    39,
    "Describes the JSON hunk format, including search/replace blocks and indentation mode.",
    f"{SOURCE_REFERENCE}README.md",
)
LOC_BUTTON_CONFIG = reference_locator(
    "button config",
    "class ButtonConfig",
    23,
    "Defines local UI button configuration for validate/apply actions.",
)
LOC_LINK_CONFIG = reference_locator(
    "linked action config",
    "class LinkConfig",
    31,
    "Defines the linked validate/apply visual state.",
)
LOC_UNIFIED_BUTTON_GROUP = reference_locator(
    "linked validate/apply group",
    "class LocalUnifiedButtonGroup",
    37,
    "Runs validate and apply independently or as a linked action sequence.",
)
LOC_PATCH_ERROR = reference_locator(
    "patch error type",
    "class PatchError",
    130,
    "Defines the domain exception used for expected patch validation failures.",
)
LOC_STRUCTURED_LINE = reference_locator(
    "structured line token",
    "class StructuredLine",
    133,
    "Splits a line into leading indent, logical content, trailing whitespace, and original text.",
)
LOC_TOKENIZE_TEXT = reference_locator(
    "tokenize text",
    "tokenize_text",
    149,
    "Tokenizes text into structured lines and detects newline style.",
)
LOC_LOCATE_HUNK = reference_locator(
    "locate hunk",
    "locate_hunk",
    162,
    "Finds exact or content-only hunk matches in tokenized file lines.",
)
LOC_APPLY_PATCH_TEXT = reference_locator(
    "apply patch text",
    "apply_patch_text",
    188,
    "Validates schema, detects missing/ambiguous/overlapping hunks, and returns patched text.",
)
LOC_INDENT_ADJUSTMENT = reference_locator(
    "relative indentation adjustment",
    "patch_base_indent",
    255,
    "Computes relative patch indentation from the matched file anchor.",
)
LOC_APP_STATE = reference_locator(
    "GUI patch state",
    "validation_preview_text",
    316,
    "Tracks dry-run preview validity before applying the patch in the GUI.",
)
LOC_SCHEMA_TEMPLATE = reference_locator(
    "schema template",
    "get_schema_template",
    642,
    "Provides the JSON hunk template shown to the user.",
)
LOC_DIFF_VIEW = reference_locator(
    "diff preview",
    "_show_diff_view",
    661,
    "Builds a unified diff preview from original and patched text.",
)
LOC_VALIDATE_PATCH = reference_locator(
    "validate patch",
    "validate_patch",
    691,
    "Performs dry-run patch validation and records preview/error state.",
)
LOC_APPLY_PATCH = reference_locator(
    "apply patch",
    "apply_patch",
    738,
    "Applies a validated or freshly parsed patch to the editor buffer.",
)
LOC_SAVE_FILE = reference_locator(
    "save patched file",
    "save_file",
    617,
    "Writes patched text to the original path or a version-suffixed output path.",
)
LOC_CLI = reference_locator(
    "CLI patch runner",
    "run_cli",
    790,
    "Reads target and patch JSON files, supports dry-run, output path, and force-indent flags.",
)
LOC_MAIN = reference_locator(
    "hybrid entry point",
    "main",
    847,
    "Routes to CLI mode when arguments are provided, otherwise launches Tk GUI mode.",
)


CAPABILITIES = (
    ToolCapability(
        key="parse_patch_schema",
        label="Parse Patch Schema",
        target_outcome=(
            "Accept a JSON patch object containing one or more hunks with search "
            "and replace blocks plus per-hunk indentation mode."
        ),
        expected_inputs=("patch JSON text or file",),
        expected_outputs=("validated patch object", "schema errors with location/context"),
        reference_locators=(LOC_README_SCHEMA, LOC_SCHEMA_TEMPLATE, LOC_VALIDATE_PATCH, LOC_CLI),
        done_when=(
            "Useful Helpers can parse patch JSON, reject malformed schemas before "
            "file matching, and surface actionable errors in both GUI and backend tests."
        ),
        implementation_owner="useful_helpers.tools.tokenizing_patcher.backend",
    ),
    ToolCapability(
        key="tokenize_lines",
        label="Tokenize Source Lines",
        target_outcome=(
            "Split source text into line tokens that preserve leading indentation, "
            "logical content, trailing whitespace, and newline style."
        ),
        expected_inputs=("source text",),
        expected_outputs=("structured line sequence", "detected newline style"),
        reference_locators=(LOC_STRUCTURED_LINE, LOC_TOKENIZE_TEXT),
        done_when=(
            "Patch matching and reconstruction can round-trip unchanged text and "
            "preserve newline style in repeatable tests."
        ),
        implementation_owner="useful_helpers.tools.tokenizing_patcher.backend",
    ),
    ToolCapability(
        key="locate_hunks",
        label="Locate Patch Hunks",
        target_outcome=(
            "Find each hunk search block in a target file by exact match first, "
            "then content-only floating match when indentation changed."
        ),
        expected_inputs=("tokenized target file", "tokenized search block"),
        expected_outputs=("single match range per hunk", "missing or ambiguous match errors"),
        reference_locators=(LOC_LOCATE_HUNK, LOC_PATCH_ERROR),
        done_when=(
            "Missing hunks, ambiguous matches, and match fallback behavior are "
            "reported before any write occurs."
        ),
        implementation_owner="useful_helpers.tools.tokenizing_patcher.backend",
    ),
    ToolCapability(
        key="apply_single_file_patch",
        label="Apply Single-File Patch",
        target_outcome=(
            "Apply validated hunks to one text file buffer, using relative "
            "indentation by default or strict patch indentation when requested."
        ),
        expected_inputs=(
            "original source text",
            "validated patch object",
            "global force-indent toggle",
        ),
        expected_outputs=("patched source text", "patch result metadata", "patch errors"),
        reference_locators=(LOC_APPLY_PATCH_TEXT, LOC_INDENT_ADJUSTMENT, LOC_PATCH_ERROR),
        done_when=(
            "A backend API can dry-run and apply a patch to one text buffer while "
            "detecting overlapping hunks and preserving intended indentation."
        ),
        implementation_owner="useful_helpers.tools.tokenizing_patcher.backend",
    ),
    ToolCapability(
        key="preview_patch_diff",
        label="Preview Patch Diff",
        target_outcome=(
            "Generate a unified diff preview for a valid patch before the user "
            "chooses to write results."
        ),
        expected_inputs=("original source text", "patched preview text", "file label"),
        expected_outputs=("unified diff text",),
        reference_locators=(LOC_DIFF_VIEW, LOC_VALIDATE_PATCH),
        done_when=(
            "Useful Helpers can show per-file diff previews for validated patches "
            "without mutating the source file."
        ),
        implementation_owner="useful_helpers.tools.tokenizing_patcher.backend",
    ),
    ToolCapability(
        key="apply_multi_file_patch_batch",
        label="Apply Multi-File Patch Batch",
        target_outcome=(
            "Expand the one-file reference behavior into a Useful Helpers batch "
            "operation over explorer-checked files, with per-file dry run, diff, "
            "errors, and write decisions."
        ),
        expected_inputs=(
            "explorer operation inclusion set",
            "one shared patch or per-file patch plan",
            "force-indent toggle",
            "dry-run/apply mode",
            "output/versioning policy",
        ),
        expected_outputs=(
            "per-file patch result records",
            "aggregate success/failure summary",
            "per-file diffs",
            "written files or versioned outputs when apply is approved",
        ),
        reference_locators=(LOC_APPLY_PATCH_TEXT, LOC_VALIDATE_PATCH, LOC_APPLY_PATCH, LOC_CLI),
        done_when=(
            "The Tools menu can validate and apply patch batches against multiple "
            "selected text files without writing any file whose dry run failed."
        ),
        implementation_owner="useful_helpers.tools.tokenizing_patcher.backend plus Useful Helpers UI",
    ),
    ToolCapability(
        key="write_patched_outputs",
        label="Write Patched Outputs",
        target_outcome=(
            "Write patched results to original files or version-suffixed output "
            "paths according to the user's selected safety policy."
        ),
        expected_inputs=("patched text", "target file path", "version/output policy"),
        expected_outputs=("written output path", "write error records"),
        reference_locators=(LOC_SAVE_FILE, LOC_CLI),
        done_when=(
            "Write behavior is explicit, tested, and never overwrites multiple "
            "files without prior validation and user-visible result state."
        ),
        implementation_owner="useful_helpers.tools.tokenizing_patcher.backend",
    ),
    ToolCapability(
        key="patcher_gui_workflow",
        label="Patcher GUI Workflow",
        target_outcome=(
            "Present patch input, validation status, diff preview, indentation "
            "mode, and apply/version options inside the Useful Helpers right pane "
            "or a tool dialog."
        ),
        expected_inputs=("selected file or file batch", "patch JSON", "user options"),
        expected_outputs=("validation state", "diff preview", "apply controls", "operation log"),
        reference_locators=(
            LOC_BUTTON_CONFIG,
            LOC_LINK_CONFIG,
            LOC_UNIFIED_BUTTON_GROUP,
            LOC_APP_STATE,
            LOC_VALIDATE_PATCH,
            LOC_APPLY_PATCH,
        ),
        done_when=(
            "The GUI lets users validate first, inspect diffs, then apply patches "
            "with clear per-file state and no hidden writes."
        ),
        implementation_owner="Useful Helpers UI plus tokenizing_patcher adapter",
    ),
    ToolCapability(
        key="cli_compatibility",
        label="CLI Compatibility",
        target_outcome=(
            "Preserve a headless execution path for tests, automation, and future "
            "tooling scripts even if the primary surface is the Useful Helpers GUI."
        ),
        expected_inputs=("target path", "patch JSON path", "output path", "force-indent", "dry-run"),
        expected_outputs=("exit code", "stdout/stderr message", "optional written output"),
        reference_locators=(LOC_CLI, LOC_MAIN),
        done_when=(
            "The patch engine can be exercised without Tk and supports dry-run "
            "and output-path behavior through local Useful Helpers code."
        ),
        implementation_owner="useful_helpers.tools.tokenizing_patcher cli module",
    ),
)


TOKENIZING_PATCHER_CONTRACT = ToolContract(
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
    """Return the semantic integration contract for the Tokenizing Patcher tool."""

    return TOKENIZING_PATCHER_CONTRACT


def list_capabilities() -> tuple[ToolCapability, ...]:
    """Return all Tokenizing Patcher capabilities currently planned for re-homing."""

    return TOKENIZING_PATCHER_CONTRACT.capabilities


def has_temporary_reference_locators() -> bool:
    """Return True while runtime tool code still carries parts-bin anchors."""

    return bool(TOKENIZING_PATCHER_CONTRACT.reference_app_path)


def reference_dependency_notice() -> str:
    """Return the rule that governs when reference locators must be retired."""

    return TOKENIZING_PATCHER_CONTRACT.reference_retirement_rule
