"""TextTOUCHER tool contract and reference implementation map.

This module is intentionally semantic, not operational. It defines the
TextTOUCHER behavior Useful Helpers may re-home from the reference app before
runtime adapters start creating or touching text files.

Temporary reference rule:
The parts-bin locators below are implementation review anchors only. When the
TextTOUCHER tool no longer depends on the reference app for design recovery,
runtime modules must not import from, read from, or require the parts bin.
"""

from __future__ import annotations

from useful_helpers.tools.contracts import ReferenceLocator, ToolCapability, ToolContract


TOOL_KEY = "text_toucher"
TOOL_LABEL = "TextTOUCHER"
STATUS = "contract reviewed; implementation pending"

SOURCE_REFERENCE = "_PARTS-FOR-PLANS/_TextTOUCHER/"
REFERENCE_APP_PATH = f"{SOURCE_REFERENCE}src/app.py"
REFERENCE_README_PATH = f"{SOURCE_REFERENCE}README.md"
REFERENCE_REQUIREMENTS_PATH = f"{SOURCE_REFERENCE}requirements.txt"
REFERENCE_RUN_PATH = f"{SOURCE_REFERENCE}run.bat"
REFERENCE_SETUP_PATH = f"{SOURCE_REFERENCE}setup_env.bat"

REFERENCE_RETIREMENT_RULE = (
    "Parts-bin references are temporary review anchors. Once each TextTOUCHER "
    "capability is re-homed into Useful Helpers runtime modules, remove "
    "parts-bin references from runtime tool code and keep historical provenance "
    "in docs only."
)

DONE_STATE = (
    "TextTOUCHER integration is complete when Useful Helpers can create one or "
    "more UTF-8 text files from the explorer-selected folder or an explicitly "
    "chosen output folder, compose safe filenames with user-selected extensions "
    "or no extension, optionally append timestamp suffixes, preview the exact "
    "target paths and overwrite decisions, prevent path traversal or writes "
    "outside the approved project/output root, write text with predictable "
    "newline handling, surface success/failure per file, reset or preserve form "
    "state according to user choice, and do all of that from local Useful "
    "Helpers modules with no runtime dependency on the parts-bin reference app."
)

FILE_WRITE_SAFETY_RULE = (
    "No TextTOUCHER write is complete until the target path is resolved, proven "
    "inside the approved output root, checked for existing files, previewed to "
    "the user when overwrite risk exists, and written through a local adapter "
    "that reports path, encoding, newline policy, and error state."
)

REFERENCE_FRAILTIES = (
    "README is empty, so source code and scripts are the only behavior evidence.",
    "CLI parser only supports verbose GUI launch; it does not create files headlessly.",
    "Reference save path joins folder and raw filename without explicit containment or path traversal validation.",
    "Tk Text reads through tk.END, which can include a trailing newline unless Useful Helpers normalizes content intentionally.",
    "Reference writes directly to the final path and does not use an atomic-write or rollback strategy.",
)


def locator(reference_path: str, label: str, symbol: str, line: int, purpose: str) -> ReferenceLocator:
    return ReferenceLocator(label, symbol, line, purpose, reference_path)


LOC_README_EMPTY = locator(
    REFERENCE_README_PATH,
    "empty README",
    "",
    1,
    "README has no behavior description; source code is the authority for this review.",
)
LOC_STDLIB_REQUIREMENTS = locator(
    REFERENCE_REQUIREMENTS_PATH,
    "stdlib dependency note",
    "Standard Library",
    1,
    "Declares that the reference app relies only on Python standard library modules.",
)
LOC_TKINTER_REQUIREMENT = locator(
    REFERENCE_REQUIREMENTS_PATH,
    "tkinter dependency note",
    "tkinter",
    5,
    "Names Tkinter as the GUI dependency included with common Python installs.",
)
LOC_CONFIG = locator(
    REFERENCE_APP_PATH,
    "app config",
    "CONFIG =",
    23,
    "Defines window size, title, default extension, and fonts.",
)
LOC_APP_TITLE = locator(
    REFERENCE_APP_PATH,
    "app title",
    "APP_TITLE",
    26,
    "Names the old standalone app Quick Text Generator.",
)
LOC_DEFAULT_EXT = locator(
    REFERENCE_APP_PATH,
    "default extension",
    "DEFAULT_EXT",
    27,
    "Defines the default .txt extension.",
)
LOC_CLASS = locator(
    REFERENCE_APP_PATH,
    "text file generator class",
    "class TextFileGenerator",
    33,
    "Owns the old Tk form and save behavior.",
)
LOC_FOLDER_VAR = locator(
    REFERENCE_APP_PATH,
    "selected folder state",
    "selected_folder_path",
    46,
    "Stores the output folder selected through the file dialog.",
)
LOC_TIMESTAMP_VAR = locator(
    REFERENCE_APP_PATH,
    "timestamp toggle state",
    "use_timestamp",
    47,
    "Stores whether the timestamp suffix is applied.",
)
LOC_EXTENSIONS = locator(
    REFERENCE_APP_PATH,
    "extension dropdown",
    "extensions =",
    103,
    "Defines selectable extensions and the no-extension option.",
)
LOC_SAVE_DISABLED = locator(
    REFERENCE_APP_PATH,
    "save disabled until folder",
    "state=\"disabled\"",
    147,
    "Starts the save button disabled until a folder is selected.",
)
LOC_SELECT_FOLDER = locator(
    REFERENCE_APP_PATH,
    "folder chooser",
    "def select_folder",
    156,
    "Opens a folder picker and stores the selected output path.",
)
LOC_ASK_DIRECTORY = locator(
    REFERENCE_APP_PATH,
    "ask directory",
    "filedialog.askdirectory",
    157,
    "Uses Tk's directory chooser as the old output-root picker.",
)
LOC_SAVE_FILE = locator(
    REFERENCE_APP_PATH,
    "save file command",
    "def save_file",
    169,
    "Coordinates filename, content, extension, timestamp, overwrite, write, and reset behavior.",
)
LOC_RAW_NAME = locator(
    REFERENCE_APP_PATH,
    "raw filename read",
    "raw_name",
    170,
    "Reads and strips the filename entry.",
)
LOC_NO_EXTENSION = locator(
    REFERENCE_APP_PATH,
    "no extension option",
    "default_ext == \" (None)\"",
    181,
    "Converts the no-extension dropdown value into an empty extension.",
)
LOC_SPLITEXT = locator(
    REFERENCE_APP_PATH,
    "user extension precedence",
    "os.path.splitext",
    184,
    "Lets a typed filename extension override the dropdown extension.",
)
LOC_TIMESTAMP = locator(
    REFERENCE_APP_PATH,
    "timestamp suffix",
    "datetime.now",
    189,
    "Appends a formatted local timestamp before the extension.",
)
LOC_JOIN = locator(
    REFERENCE_APP_PATH,
    "target path join",
    "os.path.join",
    194,
    "Builds the final path from selected folder and composed filename.",
)
LOC_EXISTS = locator(
    REFERENCE_APP_PATH,
    "overwrite existence check",
    "os.path.exists",
    197,
    "Checks whether the target path already exists.",
)
LOC_OVERWRITE_PROMPT = locator(
    REFERENCE_APP_PATH,
    "overwrite prompt",
    "messagebox.askyesno",
    198,
    "Prompts before overwriting an existing target file.",
)
LOC_OPEN_WRITE = locator(
    REFERENCE_APP_PATH,
    "UTF-8 write",
    "open(full_path",
    207,
    "Writes content with UTF-8 encoding and newline=''.",
)
LOC_SUCCESS = locator(
    REFERENCE_APP_PATH,
    "success report",
    "messagebox.showinfo",
    210,
    "Reports the saved path after a successful write.",
)
LOC_RESET = locator(
    REFERENCE_APP_PATH,
    "form reset",
    "delete(0, tk.END",
    213,
    "Clears filename/content and focuses the filename field after save.",
)
LOC_MAIN = locator(
    REFERENCE_APP_PATH,
    "GUI launch entrypoint",
    "def main",
    221,
    "Parses verbose flag and launches the Tk GUI.",
)
LOC_ARGPARSE = locator(
    REFERENCE_APP_PATH,
    "argparse GUI launcher",
    "argparse.ArgumentParser",
    222,
    "Defines a CLI parser that only launches the GUI.",
)
LOC_VERBOSE = locator(
    REFERENCE_APP_PATH,
    "verbose launch flag",
    "--verbose",
    223,
    "Supports status output when launching the GUI.",
)
LOC_TK_ROOT = locator(
    REFERENCE_APP_PATH,
    "Tk root launch",
    "tk.Tk",
    230,
    "Creates the old standalone Tk root window.",
)
LOC_RUN_SCRIPT = locator(
    REFERENCE_RUN_PATH,
    "batch launcher",
    "python -m src.app",
    23,
    "Runs the old standalone module through a local virtual environment.",
)
LOC_SETUP_SCRIPT = locator(
    REFERENCE_SETUP_PATH,
    "environment setup",
    "pip install -r requirements.txt",
    14,
    "Installs the empty/std-library requirements through a local virtual environment.",
)


CAPABILITIES = (
    ToolCapability(
        key="choose_output_folder",
        label="Choose Output Folder",
        target_outcome=(
            "Use the explorer-selected folder as the default output root, with "
            "an explicit folder picker when the user wants a different destination."
        ),
        expected_inputs=("browse selection", "optional folder-picker result"),
        expected_outputs=("approved output root", "visible output path state", "disabled/enabled write state"),
        reference_locators=(LOC_FOLDER_VAR, LOC_SAVE_DISABLED, LOC_SELECT_FOLDER, LOC_ASK_DIRECTORY),
        done_when="The tool cannot write until an output root is explicit and visible.",
        implementation_owner="Useful Helpers UI plus text_toucher planning module",
    ),
    ToolCapability(
        key="compose_safe_filename",
        label="Compose Safe Filename",
        target_outcome=(
            "Build a filename from user input, selected extension, typed extension "
            "override, optional no-extension mode, and optional timestamp suffix."
        ),
        expected_inputs=("raw filename", "selected extension", "timestamp toggle", "current clock"),
        expected_outputs=("display filename", "final extension", "timestamped filename", "validation findings"),
        reference_locators=(LOC_DEFAULT_EXT, LOC_EXTENSIONS, LOC_RAW_NAME, LOC_NO_EXTENSION, LOC_SPLITEXT, LOC_TIMESTAMP),
        done_when=(
            "Filename composition is deterministic, test-covered, and rejects "
            "empty names, reserved names, path separators, and unsafe absolute paths."
        ),
        implementation_owner="useful_helpers.tools.text_toucher filename module",
    ),
    ToolCapability(
        key="validate_write_target",
        label="Validate Write Target",
        target_outcome=(
            "Resolve the composed target path and prove it remains inside the "
            "approved output root before any file operation occurs."
        ),
        expected_inputs=("approved output root", "composed filename"),
        expected_outputs=("resolved target path", "inside-root decision", "blocked-path reason"),
        reference_locators=(LOC_JOIN,),
        done_when=FILE_WRITE_SAFETY_RULE,
        implementation_owner="useful_helpers.tools.text_toucher safety module",
    ),
    ToolCapability(
        key="preview_overwrite_decision",
        label="Preview Overwrite Decision",
        target_outcome="Detect existing target files and require an explicit overwrite decision before replacing content.",
        expected_inputs=("resolved target path", "overwrite preference", "user confirmation"),
        expected_outputs=("exists flag", "overwrite allowed/blocked decision", "visible warning"),
        reference_locators=(LOC_EXISTS, LOC_OVERWRITE_PROMPT),
        done_when="Existing files are never overwritten silently and the final plan shows every replace action.",
        implementation_owner="useful_helpers.tools.text_toucher safety module",
    ),
    ToolCapability(
        key="write_utf8_text_file",
        label="Write UTF-8 Text File",
        target_outcome="Write the requested text content to the approved target path with explicit encoding and newline policy.",
        expected_inputs=("resolved target path", "text content", "encoding", "newline policy", "overwrite decision"),
        expected_outputs=("write result", "bytes/chars written", "path", "error state"),
        reference_locators=(LOC_OPEN_WRITE, LOC_SUCCESS),
        done_when="A write reports exact success/failure details and never depends on the old standalone app.",
        implementation_owner="useful_helpers.tools.text_toucher writer module",
    ),
    ToolCapability(
        key="normalize_text_content",
        label="Normalize Text Content",
        target_outcome=(
            "Preserve or normalize text content intentionally, including the "
            "trailing newline that Tk text widgets can add when reading through tk.END."
        ),
        expected_inputs=("editor text", "trailing-newline policy", "newline policy"),
        expected_outputs=("normalized text", "content warnings"),
        reference_locators=(LOC_SAVE_FILE,),
        done_when="Content written by Useful Helpers matches the previewed content byte-for-byte after chosen newline policy.",
        implementation_owner="useful_helpers.tools.text_toucher content module",
    ),
    ToolCapability(
        key="reset_or_preserve_form_state",
        label="Reset Or Preserve Form State",
        target_outcome="After a write, clear or preserve filename/content fields according to a visible user setting.",
        expected_inputs=("write result", "reset preference", "current form state"),
        expected_outputs=("next form state", "focus target", "status message"),
        reference_locators=(LOC_RESET,),
        done_when="Successful writes leave the form in a predictable state for repeated file creation.",
        implementation_owner="Useful Helpers UI plus text_toucher adapter",
    ),
    ToolCapability(
        key="text_toucher_gui_workflow",
        label="TextTOUCHER GUI Workflow",
        target_outcome=(
            "Expose folder selection, filename, extension, no-extension mode, "
            "timestamp toggle, text editor, preview, save, overwrite prompt, and result state inside Useful Helpers."
        ),
        expected_inputs=("selected project/folder", "filename", "extension option", "timestamp toggle", "text content"),
        expected_outputs=("tool form state", "target preview", "write result", "error or success message"),
        reference_locators=(LOC_CONFIG, LOC_APP_TITLE, LOC_CLASS, LOC_SAVE_FILE, LOC_MAIN, LOC_TK_ROOT),
        done_when="TextTOUCHER is available from the Tools menu without replacing the explorer-first workbench shell.",
        implementation_owner="Useful Helpers UI plus text_toucher adapter",
    ),
    ToolCapability(
        key="headless_create_file",
        label="Headless Create File",
        target_outcome=(
            "Provide a backend/API path for tests and possible CLI use to create "
            "text files without launching Tk."
        ),
        expected_inputs=("output root", "filename", "extension option", "content", "timestamp option", "overwrite policy"),
        expected_outputs=("operation plan", "write result", "exit/error state"),
        reference_locators=(LOC_ARGPARSE, LOC_VERBOSE),
        done_when=(
            "The behavior promised by the GUI can be tested headlessly, while the "
            "reference CLI launcher is treated only as evidence."
        ),
        implementation_owner="useful_helpers.tools.text_toucher backend module",
    ),
    ToolCapability(
        key="packaging_scripts_reference_only",
        label="Packaging Scripts Reference Only",
        target_outcome="Treat old run/setup batch scripts as launch provenance, not Useful Helpers runtime behavior.",
        expected_inputs=("none for runtime",),
        expected_outputs=("deferred packaging note",),
        reference_locators=(LOC_STDLIB_REQUIREMENTS, LOC_TKINTER_REQUIREMENT, LOC_RUN_SCRIPT, LOC_SETUP_SCRIPT),
        done_when="Useful Helpers packaging does not depend on the reference .venv, run.bat, or setup_env.bat scripts.",
        implementation_owner="deferred packaging tranche",
    ),
)


TEXT_TOUCHER_CONTRACT = ToolContract(
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
    """Return the semantic integration contract for the TextTOUCHER tool."""

    return TEXT_TOUCHER_CONTRACT


def list_capabilities() -> tuple[ToolCapability, ...]:
    """Return all TextTOUCHER capabilities currently planned for re-homing."""

    return TEXT_TOUCHER_CONTRACT.capabilities


def has_temporary_reference_locators() -> bool:
    """Return True while runtime tool code still carries parts-bin anchors."""

    return bool(TEXT_TOUCHER_CONTRACT.reference_app_path)


def reference_dependency_notice() -> str:
    """Return the rule that governs when reference locators must be retired."""

    return TEXT_TOUCHER_CONTRACT.reference_retirement_rule
