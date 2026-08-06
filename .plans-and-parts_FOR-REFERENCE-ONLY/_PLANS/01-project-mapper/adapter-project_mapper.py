"""Project Mapper tool contract and reference implementation map.

This module is intentionally semantic, not operational. It defines the
Project Mapper behavior Useful Helpers will re-home from the reference app
before the runtime adapter starts executing snapshot/export work.

Temporary reference rule:
The parts-bin locators below are implementation review anchors only. When the
Project Mapper tool no longer depends on the reference app for design recovery,
runtime modules must not import from, read from, or require the parts bin.
"""

from __future__ import annotations

from useful_helpers.tools.contracts import ReferenceLocator, ToolCapability, ToolContract


TOOL_KEY = "project_mapper"
TOOL_LABEL = "Project Mapper"
STATUS = "backend implemented; GUI wiring pending"

SOURCE_REFERENCE = "_PARTS-FOR-PLANS/_ProjectMAPPER/"
REFERENCE_APP_PATH = f"{SOURCE_REFERENCE}src/app.py"

REFERENCE_RETIREMENT_RULE = (
    "Parts-bin references are temporary review anchors. Once each capability is "
    "re-homed into Useful Helpers runtime modules, remove parts-bin references "
    "from runtime tool code and keep historical provenance in docs only."
)

DONE_STATE = (
    "Project Mapper integration is complete when Useful Helpers can use the "
    "explorer-selected working set to compile a SQLite project snapshot, export "
    "tree/filedump/combined/manifest markdown projections, preserve exclusion, "
    "skipped-path, environment, mapper-state, warning, and error metadata, and "
    "perform all of that from local Useful Helpers modules with no runtime "
    "dependency on the parts-bin reference app."
)

def reference_locator(label: str, symbol: str, line: int, purpose: str) -> ReferenceLocator:
    return ReferenceLocator(label, symbol, line, purpose, REFERENCE_APP_PATH)



LOC_APP_METADATA = reference_locator(
    "snapshot app metadata",
    "APP_NAME",
    28,
    "Names the original compiler and version metadata used in snapshot records.",
)
LOC_SUFFIXES = reference_locator(
    "snapshot output suffixes",
    "SNAPSHOT_DB_SUFFIX",
    47,
    "Defines SQLite and markdown artifact naming conventions.",
)
LOC_EXCLUSIONS = reference_locator(
    "default exclusion policy",
    "EXCLUDED_FOLDERS",
    53,
    "Defines folders and filenames omitted from default scans.",
)
LOC_BINARY_POLICY = reference_locator(
    "binary dump policy",
    "FORCE_BINARY_EXTENSIONS_FOR_DUMP",
    64,
    "Defines extensions treated as binary for filedump safety.",
)
LOC_SAFE_READ = reference_locator(
    "safe text reader",
    "safe_read_text",
    226,
    "Reads text files with size, encoding, binary, and error classification.",
)
LOC_SAFE_BLOB = reference_locator(
    "safe blob reader",
    "safe_read_blob",
    244,
    "Reads binary bytes for optional SQLite blob preservation.",
)
LOC_EXCLUSION_POLICY = reference_locator(
    "exclusion policy class",
    "class ExclusionPolicy",
    457,
    "Combines built-in, dynamic, and gitignore-informed exclusions.",
)
LOC_SCAN_TREE = reference_locator(
    "project tree scan",
    "scan_project_tree",
    551,
    "Builds visible tree rows and skipped-path records from a project root.",
)
LOC_SCHEMA = reference_locator(
    "SQLite snapshot schema",
    "create_snapshot_schema",
    599,
    "Creates the authoritative project snapshot tables and indexes.",
)
LOC_WRITERS = reference_locator(
    "snapshot writers",
    "insert_project_tree_row",
    740,
    "Shows row-level insert helpers for tree, file, blob, rule, state, and errors.",
)
LOC_ENVIRONMENT = reference_locator(
    "environment hints",
    "detect_environment_hints",
    853,
    "Captures local platform and project marker metadata for snapshot context.",
)
LOC_TREE_MD = reference_locator(
    "tree markdown projection",
    "build_project_tree_markdown",
    929,
    "Builds a lightweight selected tree map from snapshot rows.",
)
LOC_FILEDUMP_MD = reference_locator(
    "filedump markdown projection",
    "build_filedump_markdown",
    961,
    "Builds selected text file dump markdown with language fences.",
)
LOC_COMPILE = reference_locator(
    "snapshot compiler",
    "compile_snapshot",
    992,
    "Coordinates schema creation, selected file capture, metadata, and outputs.",
)
LOC_EXPORT_OUTPUT = reference_locator(
    "snapshot output export",
    "export_snapshot_output",
    1841,
    "Exports DB-embedded markdown outputs to standalone files.",
)
LOC_EXPORT_TREE = reference_locator(
    "export tree markdown",
    "export_tree_markdown",
    1854,
    "UI command for exporting the tree projection.",
)
LOC_EXPORT_FILEDUMP = reference_locator(
    "export filedump markdown",
    "export_filedump_markdown",
    1857,
    "UI command for exporting filedump markdown, optionally with tree prepended.",
)
LOC_EXPORT_COMBINED = reference_locator(
    "export combined markdown",
    "export_combined_markdown",
    1871,
    "UI command for exporting tree and filedump in one markdown file.",
)
LOC_EXPORT_MANIFEST = reference_locator(
    "export manifest markdown",
    "export_manifest_markdown",
    1883,
    "UI command for exporting the snapshot manifest markdown.",
)
LOC_SELECTION = reference_locator(
    "tree selection behavior",
    "toggle_tree_item",
    1662,
    "Toggles checked state recursively for explorer-selected paths.",
)
LOC_GLOBAL_SELECTION = reference_locator(
    "global tree selection",
    "set_global_selection",
    1675,
    "Sets every visible explorer item to checked or unchecked.",
)
LOC_EXCLUSION_UI = reference_locator(
    "exclusion management UI",
    "manage_exclusions_popup",
    1713,
    "Lets users inspect and mutate dynamic exclusion patterns.",
)
LOC_THREADING = reference_locator(
    "threaded task runner",
    "run_threaded_action",
    1937,
    "Runs long scans/exports without freezing the Tk interface.",
)
LOC_VENDOR_EXPORT = reference_locator(
    "vendor export",
    "create_vendor_export",
    337,
    "Exports a standalone application copy; deferred until product need is explicit.",
)


CAPABILITIES = (
    ToolCapability(
        key="scan_project",
        label="Scan Project Tree",
        target_outcome=(
            "Given a chosen project root and exclusion settings, produce a "
            "typed visible tree plus skipped-path records for the explorer."
        ),
        expected_inputs=(
            "project root path",
            "respect exclusions toggle",
            "default/dynamic/gitignore exclusion policy",
            "optional cancellation signal",
        ),
        expected_outputs=(
            "visible tree rows for folders and files",
            "skipped path records with reason/detail/source",
            "initial checked state for selectable explorer items",
        ),
        reference_locators=(
            LOC_EXCLUSIONS,
            LOC_BINARY_POLICY,
            LOC_EXCLUSION_POLICY,
            LOC_SCAN_TREE,
        ),
        done_when=(
            "The main explorer can rescan a folder, preserve checked state for "
            "stable paths, expose skipped reasons, and avoid scanning excluded "
            "or unsafe paths."
        ),
        implementation_owner="useful_helpers.core.scanner and useful_helpers.core.exclusions",
    ),
    ToolCapability(
        key="compile_sqlite_snapshot",
        label="Compile SQLite Snapshot",
        target_outcome=(
            "Create an authoritative SQLite snapshot from the current checked "
            "working set, including selected text files, optional binary blobs, "
            "tree state, metadata, outputs, and nonfatal errors."
        ),
        expected_inputs=(
            "project root path",
            "output directory",
            "visible tree rows",
            "checked/unchecked mapper state",
            "scan skipped-path records",
            "exclusion policy",
            "include binary blobs toggle",
            "optional cancellation signal",
        ),
        expected_outputs=(
            "root-named *_snapshot.sqlite3 database",
            "snapshot_metadata rows",
            "project_tree rows",
            "project_files rows",
            "optional project_blobs rows with sha256",
            "snapshot_exclusion_rules rows",
            "snapshot_skipped_paths rows",
            "snapshot_mapper_state rows",
            "snapshot_environment rows",
            "snapshot_outputs rows",
            "snapshot_errors rows",
        ),
        reference_locators=(
            LOC_APP_METADATA,
            LOC_SUFFIXES,
            LOC_SAFE_READ,
            LOC_SAFE_BLOB,
            LOC_SCHEMA,
            LOC_WRITERS,
            LOC_ENVIRONMENT,
            LOC_COMPILE,
        ),
        done_when=(
            "A user can select paths in Useful Helpers and compile a complete "
            "or partial SQLite snapshot whose tables can be validated with "
            "repeatable tests."
        ),
        implementation_owner="useful_helpers.tools.project_mapper.backend",
    ),
    ToolCapability(
        key="export_project_tree_markdown",
        label="Export Project Tree Markdown",
        target_outcome=(
            "Export the DB-embedded project tree projection as standalone "
            "markdown for lightweight project mapping."
        ),
        expected_inputs=("latest snapshot database", "project root path", "output directory"),
        expected_outputs=("root-named *_project_tree.md file",),
        reference_locators=(LOC_TREE_MD, LOC_EXPORT_OUTPUT, LOC_EXPORT_TREE),
        done_when=(
            "The Tools menu can write the selected tree projection from the "
            "latest snapshot and report success or actionable failure."
        ),
        implementation_owner="useful_helpers.tools.project_mapper.backend",
    ),
    ToolCapability(
        key="export_filedump_markdown",
        label="Export Filedump Markdown",
        target_outcome=(
            "Export selected text file contents as fenced markdown, optionally "
            "prefixed with the project tree."
        ),
        expected_inputs=(
            "latest snapshot database",
            "include tree in filedump toggle",
            "project root path",
            "output directory",
        ),
        expected_outputs=("root-named *_project_filedump.md file",),
        reference_locators=(LOC_FILEDUMP_MD, LOC_EXPORT_OUTPUT, LOC_EXPORT_FILEDUMP),
        done_when=(
            "The Tools menu can write a filedump projection that includes only "
            "checked, text-readable files and keeps skipped content out."
        ),
        implementation_owner="useful_helpers.tools.project_mapper.backend",
    ),
    ToolCapability(
        key="export_combined_markdown",
        label="Export Tree Plus Filedump Markdown",
        target_outcome=(
            "Export one markdown artifact containing both tree map and selected "
            "filedump content."
        ),
        expected_inputs=("latest snapshot database", "project root path", "output directory"),
        expected_outputs=("root-named *_project_tree_and_filedump.md file",),
        reference_locators=(LOC_TREE_MD, LOC_FILEDUMP_MD, LOC_EXPORT_OUTPUT, LOC_EXPORT_COMBINED),
        done_when=(
            "The Tools menu can write a combined tree/filedump markdown artifact "
            "from the latest SQLite snapshot without recomputing scan state."
        ),
        implementation_owner="useful_helpers.tools.project_mapper.backend",
    ),
    ToolCapability(
        key="export_manifest_markdown",
        label="Export Snapshot Manifest Markdown",
        target_outcome=(
            "Export the snapshot manifest as a standalone onboarding document "
            "for users or agents inspecting the database."
        ),
        expected_inputs=("latest snapshot database", "project root path", "output directory"),
        expected_outputs=("root-named *_snapshot_manifest.md file",),
        reference_locators=(LOC_COMPILE, LOC_EXPORT_OUTPUT, LOC_EXPORT_MANIFEST),
        done_when=(
            "The Tools menu can write the DB-embedded manifest markdown and the "
            "manifest accurately describes schema, counts, queries, and state."
        ),
        implementation_owner="useful_helpers.tools.project_mapper.backend",
    ),
    ToolCapability(
        key="manage_exclusions",
        label="Manage Project Mapper Exclusions",
        target_outcome=(
            "Let the user view and adjust dynamic exclusions that influence "
            "scanning, snapshots, and exports."
        ),
        expected_inputs=("current exclusion policy", "user-entered pattern"),
        expected_outputs=(
            "updated dynamic exclusion list",
            "rescan or snapshot behavior reflecting the updated policy",
        ),
        reference_locators=(LOC_EXCLUSION_POLICY, LOC_EXCLUSION_UI),
        done_when=(
            "The UI can add/remove/list dynamic exclusions and snapshot output "
            "records the active exclusion rules."
        ),
        implementation_owner="useful_helpers.core.exclusions and Useful Helpers UI",
    ),
    ToolCapability(
        key="run_long_project_mapper_tasks",
        label="Run Project Mapper Tasks With Progress",
        target_outcome=(
            "Run scans, snapshot compiles, and exports without freezing the UI, "
            "with visible progress, cancellation, and logged completion state."
        ),
        expected_inputs=("tool command", "progress sink", "optional cancellation signal"),
        expected_outputs=("task status updates", "success/failure/cancelled result"),
        reference_locators=(LOC_THREADING,),
        done_when=(
            "Long Project Mapper operations can be cancelled or completed while "
            "the explorer remains responsive and errors are visible."
        ),
        implementation_owner="Useful Helpers UI/core orchestration layer",
    ),
    ToolCapability(
        key="vendor_export",
        label="Vendor Export",
        target_outcome=(
            "Deferred candidate: export a standalone copy of Useful Helpers or "
            "a selected tool package only if the product plan confirms it."
        ),
        expected_inputs=("source root", "export output root", "zip toggle"),
        expected_outputs=("export folder", "optional zip", "vendor manifest"),
        reference_locators=(LOC_VENDOR_EXPORT,),
        done_when=(
            "Not part of the first Project Mapper integration stop state unless "
            "a later tranche explicitly accepts vendor export as product scope."
        ),
        implementation_owner="deferred",
    ),
)


PROJECT_MAPPER_CONTRACT = ToolContract(
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
    """Return the semantic integration contract for the Project Mapper tool."""

    return PROJECT_MAPPER_CONTRACT


def list_capabilities() -> tuple[ToolCapability, ...]:
    """Return all Project Mapper capabilities currently planned for re-homing."""

    return PROJECT_MAPPER_CONTRACT.capabilities


def has_temporary_reference_locators() -> bool:
    """Return True while runtime tool code still carries parts-bin anchors."""

    return bool(PROJECT_MAPPER_CONTRACT.reference_app_path)


def reference_dependency_notice() -> str:
    """Return the rule that governs when reference locators must be retired."""

    return PROJECT_MAPPER_CONTRACT.reference_retirement_rule
