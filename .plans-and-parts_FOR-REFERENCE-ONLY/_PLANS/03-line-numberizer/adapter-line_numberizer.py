"""Line Numberizer tool contract and reference implementation map.

This module is intentionally semantic, not operational. It defines the Line
Numberizer behavior Useful Helpers will re-home from the reference app before
runtime adapters start annotating, stripping, mapping, or exporting AST data.

Temporary reference rule:
The parts-bin locators below are implementation review anchors only. When the
Line Numberizer tool no longer depends on the reference app for design recovery,
runtime modules must not import from, read from, or require the parts bin.
"""

from __future__ import annotations

from useful_helpers.tools.contracts import ReferenceLocator, ToolCapability, ToolContract


TOOL_KEY = "line_numberizer"
TOOL_LABEL = "Line Numberizer"
STATUS = "backend implemented; GUI/CLI wiring pending"

SOURCE_REFERENCE = "_PARTS-FOR-PLANS/_LineNUMBERIZER/"
REFERENCE_ENGINE_PATH = f"{SOURCE_REFERENCE}src/linenumberizer.py"
REFERENCE_APP_PATH = REFERENCE_ENGINE_PATH
REFERENCE_GUI_PATH = f"{SOURCE_REFERENCE}src/app.py"
REFERENCE_LEGACY_GUI_PATH = f"{SOURCE_REFERENCE}src/legacy_app.py"

REFERENCE_RETIREMENT_RULE = (
    "Parts-bin references are temporary review anchors. Once each line-number, "
    "line-map, or AST capability is re-homed into Useful Helpers runtime "
    "modules, remove parts-bin references from runtime tool code and keep "
    "historical provenance in docs only."
)

DONE_STATE = (
    "Line Numberizer integration is complete when Useful Helpers can annotate, "
    "strip, and map one or many explorer-selected text files; export Python AST "
    "tree, flat, and semantic JSON views where applicable; preserve source text "
    "content while adding or removing only recognized numbering prefixes; write "
    "explicit output files or dry-run previews; surface per-file errors and AST "
    "syntax failures; and do all of that from local Useful Helpers modules with "
    "no runtime dependency on the parts-bin reference app."
)


def engine_locator(label: str, symbol: str, line: int, purpose: str) -> ReferenceLocator:
    return ReferenceLocator(label, symbol, line, purpose, REFERENCE_ENGINE_PATH)


def gui_locator(label: str, symbol: str, line: int, purpose: str) -> ReferenceLocator:
    return ReferenceLocator(label, symbol, line, purpose, REFERENCE_GUI_PATH)


LOC_README_FEATURES = ReferenceLocator(
    "README feature list",
    "Features",
    7,
    "Describes annotate, strip, AST export, and line-map behavior.",
    f"{SOURCE_REFERENCE}README.md",
)
LOC_PREFIX_STYLE = engine_locator(
    "prefix style base",
    "class PrefixStyle",
    38,
    "Defines the line-number prefix style interface.",
)
LOC_PIPE_STYLE = engine_locator(
    "pipe prefix style",
    "class PipeStyle",
    44,
    "Formats lines with the default pipe-style numeric prefix.",
)
LOC_COLON_STYLE = engine_locator(
    "colon prefix style",
    "class ColonStyle",
    48,
    "Formats lines with a colon-style numeric prefix.",
)
LOC_BRACKET_STYLE = engine_locator(
    "bracket prefix style",
    "class BracketStyle",
    52,
    "Formats lines with a bracketed [L#] prefix.",
)
LOC_PREFIX_REGEXES = engine_locator(
    "recognized prefix regexes",
    "PIPE_RE",
    56,
    "Defines conservative regexes for stripping only prefixes created by the tool.",
)
LOC_OPEN_TEXT = engine_locator(
    "open text helper",
    "open_text_maybe",
    71,
    "Reads UTF-8 text from a path or stdin while preserving newline behavior.",
)
LOC_CREATE_TEXT = engine_locator(
    "create text helper",
    "create_text_maybe",
    76,
    "Writes UTF-8 text to a path or stdout and creates parent directories.",
)
LOC_DETECT_TOTAL = engine_locator(
    "detect total lines",
    "detect_total_lines",
    86,
    "Counts lines to compute automatic prefix width.",
)
LOC_ANNOTATE_LINES = engine_locator(
    "annotate lines",
    "annotate_lines",
    93,
    "Adds generated line-number prefixes to an iterable of text lines.",
)
LOC_STRIP_LINES = engine_locator(
    "strip numbered lines",
    "strip_lines",
    99,
    "Removes only recognized Line Numberizer prefixes from text lines.",
)
LOC_LINE_HASH = engine_locator(
    "line hash",
    "line_hash",
    107,
    "Builds SHA-256 hashes for raw line content or semantic source blocks.",
)
LOC_BUILD_MAP = engine_locator(
    "build line map",
    "build_map",
    111,
    "Creates line-number to content-hash records.",
)
LOC_AST_SAFE_FIELDS = engine_locator(
    "AST safe fields",
    "AST_SAFE_FIELDS",
    122,
    "Limits AST JSON payloads to stable, useful fields.",
)
LOC_AST_NODE_DICT = engine_locator(
    "AST node dict",
    "_ast_node_to_dict",
    136,
    "Converts Python AST nodes into JSON-safe dictionaries.",
)
LOC_BUILD_PY_AST = engine_locator(
    "build Python AST",
    "build_py_ast",
    155,
    "Builds Python AST exports in tree or flat mode.",
)
LOC_SEMANTIC_VISITOR = engine_locator(
    "semantic visitor",
    "class SemanticVisitor",
    177,
    "Builds logical source blocks for functions, classes, imports, and top-level statements.",
)
LOC_BUILD_SEMANTIC = engine_locator(
    "build semantic model",
    "build_semantic_model",
    260,
    "Builds a high-level semantic block model from Python source.",
)
LOC_CMD_ANNOTATE = engine_locator(
    "annotate command",
    "cmd_annotate",
    272,
    "CLI command handler for annotation, in-place writes, dry run, and optional map output.",
)
LOC_STRIP_PREFIX_FOR_MAP = engine_locator(
    "strip prefix for map",
    "strip_prefix_for_map",
    315,
    "Removes prefixes before creating content hashes for maps.",
)
LOC_CMD_STRIP = engine_locator(
    "strip command",
    "cmd_strip",
    321,
    "CLI command handler for removing recognized prefixes.",
)
LOC_CMD_MAP = engine_locator(
    "map command",
    "cmd_map",
    344,
    "CLI command handler for line-to-hash JSON maps.",
)
LOC_CMD_AST = engine_locator(
    "AST command",
    "cmd_ast",
    359,
    "CLI command handler for Python AST tree, flat, and semantic JSON exports.",
)
LOC_SYNTAX_ERROR = engine_locator(
    "AST syntax error reporting",
    "Python syntax error at line",
    408,
    "Reports Python syntax failures with exact line number.",
)
LOC_NUMBERED_SUFFIX = engine_locator(
    "numbered suffix",
    "numbered_suffix",
    415,
    "Builds default output suffix for annotated files.",
)
LOC_SUGGEST_OUT = engine_locator(
    "suggest output path",
    "suggest_out_path",
    418,
    "Builds default output paths for generated artifacts.",
)
LOC_BUILD_PARSER = engine_locator(
    "CLI parser",
    "build_parser",
    426,
    "Defines annotate, strip, map, and ast CLI commands and options.",
)
LOC_MAIN = engine_locator(
    "CLI entry point",
    "main",
    471,
    "Runs CLI dispatch and normalizes expected error exit codes.",
)
LOC_GUI_DEFAULT_OUTPUT = gui_locator(
    "GUI default output path",
    "default_output_for",
    35,
    "Suggests user-facing output filenames for annotate, strip, map, and AST operations.",
)
LOC_GUI_ASYNC = gui_locator(
    "GUI async runner",
    "run_cli_async",
    57,
    "Runs the CLI backend in a background thread for the Tk wrapper.",
)
LOC_GUI_APP = gui_locator(
    "GUI app state",
    "class App",
    73,
    "Defines the Tk wrapper controls for file, operation, style, AST mode, output, run, and log.",
)
LOC_GUI_RUN = gui_locator(
    "GUI run operation",
    "on_run",
    269,
    "Builds CLI argv from GUI state and starts the async operation.",
)


CAPABILITIES = (
    ToolCapability(
        key="annotate_text_lines",
        label="Annotate Text Lines",
        target_outcome=(
            "Add stable, parseable line-number prefixes to text files using pipe, "
            "colon, or bracket styles with configurable start and width."
        ),
        expected_inputs=(
            "source text or selected text files",
            "prefix style",
            "starting line number",
            "minimum width or auto width",
            "dry-run/output policy",
        ),
        expected_outputs=(
            "annotated text preview or output file",
            "line numbering metadata",
            "per-file result records for batch operations",
        ),
        reference_locators=(
            LOC_README_FEATURES,
            LOC_PREFIX_STYLE,
            LOC_PIPE_STYLE,
            LOC_COLON_STYLE,
            LOC_BRACKET_STYLE,
            LOC_DETECT_TOTAL,
            LOC_ANNOTATE_LINES,
            LOC_CMD_ANNOTATE,
        ),
        done_when=(
            "Useful Helpers can annotate one or many selected text files without "
            "changing original content after the prefix, and can preview or write "
            "the result according to an explicit policy."
        ),
        implementation_owner="useful_helpers.tools.line_numberizer.backend",
    ),
    ToolCapability(
        key="strip_line_numbers",
        label="Strip Line Numbers",
        target_outcome=(
            "Remove only prefixes generated by Line Numberizer while preserving "
            "all remaining source text exactly."
        ),
        expected_inputs=("numbered text or selected numbered files", "dry-run/output policy"),
        expected_outputs=("stripped text preview or output file", "per-file strip result records"),
        reference_locators=(LOC_PREFIX_REGEXES, LOC_STRIP_LINES, LOC_CMD_STRIP),
        done_when=(
            "Stripping is conservative, repeatably tested across all supported "
            "prefix styles, and never removes unrelated user content."
        ),
        implementation_owner="useful_helpers.tools.line_numberizer.backend",
    ),
    ToolCapability(
        key="build_line_map",
        label="Build Line Map",
        target_outcome=(
            "Generate JSON maps from line numbers to SHA-256 content hashes for "
            "integrity checks and agent-friendly references."
        ),
        expected_inputs=("source text or selected files", "strip-number-prefixes toggle", "output path policy"),
        expected_outputs=("JSON line map", "total line count", "per-line hash entries"),
        reference_locators=(LOC_LINE_HASH, LOC_BUILD_MAP, LOC_STRIP_PREFIX_FOR_MAP, LOC_CMD_MAP),
        done_when=(
            "Useful Helpers can build repeatable line maps for raw or numbered "
            "files and store per-file map outputs with clear source metadata."
        ),
        implementation_owner="useful_helpers.tools.line_numberizer.backend",
    ),
    ToolCapability(
        key="export_python_ast_tree_flat",
        label="Export Python AST Tree Or Flat JSON",
        target_outcome=(
            "Export Python AST data as nested tree JSON or flattened node JSON "
            "with safe fields for project inspection and code navigation."
        ),
        expected_inputs=("Python source text or selected Python files", "AST mode tree or flat", "output path policy"),
        expected_outputs=("AST JSON output", "syntax or unsupported-file errors"),
        reference_locators=(LOC_AST_SAFE_FIELDS, LOC_AST_NODE_DICT, LOC_BUILD_PY_AST, LOC_CMD_AST),
        done_when=(
            "Tree and flat AST exports work for valid Python files, emit clear "
            "syntax errors, and produce a graceful unsupported-file result for non-Python inputs."
        ),
        implementation_owner="useful_helpers.tools.line_numberizer.backend",
    ),
    ToolCapability(
        key="export_python_semantic_blocks",
        label="Export Python Semantic Blocks",
        target_outcome=(
            "Export a high-level semantic JSON model of functions, classes, "
            "imports, top-level statements, signatures, spans, source snippets, "
            "and stable block hashes."
        ),
        expected_inputs=("Python source text or selected Python files", "semantic depth top or all", "output path policy"),
        expected_outputs=("semantic blocks JSON", "file metadata", "syntax errors"),
        reference_locators=(LOC_SEMANTIC_VISITOR, LOC_BUILD_SEMANTIC, LOC_LINE_HASH, LOC_CMD_AST, LOC_SYNTAX_ERROR),
        done_when=(
            "Semantic exports produce stable block IDs and spans suitable for "
            "agent navigation and later patch planning."
        ),
        implementation_owner="useful_helpers.tools.line_numberizer.backend",
    ),
    ToolCapability(
        key="write_line_numberizer_outputs",
        label="Write Line Numberizer Outputs",
        target_outcome=(
            "Write annotate, strip, map, and AST outputs to explicit output paths, "
            "with dry-run support and conservative in-place behavior."
        ),
        expected_inputs=("generated content", "target file path", "output/in-place/dry-run policy"),
        expected_outputs=("written output path", "stdout preview", "write error records"),
        reference_locators=(LOC_OPEN_TEXT, LOC_CREATE_TEXT, LOC_NUMBERED_SUFFIX, LOC_SUGGEST_OUT, LOC_GUI_DEFAULT_OUTPUT),
        done_when=(
            "Output behavior is explicit, testable, and safe for batch operations "
            "over explorer-selected files."
        ),
        implementation_owner="useful_helpers.tools.line_numberizer.backend",
    ),
    ToolCapability(
        key="run_line_numberizer_batch",
        label="Run Line Numberizer Batch",
        target_outcome=(
            "Expand the reference single-file CLI/GUI flow into Useful Helpers "
            "batch operations over checked explorer files."
        ),
        expected_inputs=(
            "explorer operation inclusion set",
            "operation annotate, strip, map, or ast",
            "operation options",
            "dry-run/output policy",
        ),
        expected_outputs=(
            "per-file result records",
            "aggregate success/failure summary",
            "written files or previews",
        ),
        reference_locators=(LOC_CMD_ANNOTATE, LOC_CMD_STRIP, LOC_CMD_MAP, LOC_CMD_AST, LOC_BUILD_PARSER, LOC_MAIN),
        done_when=(
            "The Tools menu can run line numbering, stripping, maps, and AST "
            "exports over multiple selected files with per-file error isolation."
        ),
        implementation_owner="useful_helpers.tools.line_numberizer.backend plus Useful Helpers UI",
    ),
    ToolCapability(
        key="line_numberizer_gui_workflow",
        label="Line Numberizer GUI Workflow",
        target_outcome=(
            "Present operation, style, width, AST mode, output path, run status, "
            "and logs inside the Useful Helpers right pane or a tool dialog."
        ),
        expected_inputs=("selected file or file batch", "operation options", "output policy"),
        expected_outputs=("operation form state", "run log", "success/error messages"),
        reference_locators=(LOC_GUI_DEFAULT_OUTPUT, LOC_GUI_ASYNC, LOC_GUI_APP, LOC_GUI_RUN),
        done_when=(
            "The GUI offers the expected controls without copying the old app as "
            "a separate runtime dependency or separate application identity."
        ),
        implementation_owner="Useful Helpers UI plus line_numberizer adapter",
    ),
    ToolCapability(
        key="cli_compatibility",
        label="CLI Compatibility",
        target_outcome=(
            "Preserve a headless execution path for tests, automation, and future "
            "tooling scripts even if the primary surface is the Useful Helpers GUI."
        ),
        expected_inputs=("CLI argv", "stdin/stdout path sentinel support", "operation-specific options"),
        expected_outputs=("exit code", "stdout/stderr message", "optional written output"),
        reference_locators=(LOC_BUILD_PARSER, LOC_MAIN),
        done_when=(
            "The line-numberizer backend can be exercised without Tk and supports "
            "annotate, strip, map, and ast operations through local Useful Helpers code."
        ),
        implementation_owner="useful_helpers.tools.line_numberizer cli module",
    ),
)


LINE_NUMBERIZER_CONTRACT = ToolContract(
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
    """Return the semantic integration contract for the Line Numberizer tool."""

    return LINE_NUMBERIZER_CONTRACT


def list_capabilities() -> tuple[ToolCapability, ...]:
    """Return all Line Numberizer capabilities currently planned for re-homing."""

    return LINE_NUMBERIZER_CONTRACT.capabilities


def has_temporary_reference_locators() -> bool:
    """Return True while runtime tool code still carries parts-bin anchors."""

    return bool(LINE_NUMBERIZER_CONTRACT.reference_app_path)


def reference_dependency_notice() -> str:
    """Return the rule that governs when reference locators must be retired."""

    return LINE_NUMBERIZER_CONTRACT.reference_retirement_rule
