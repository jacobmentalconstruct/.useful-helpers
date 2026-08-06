# UiMAPPER Tool Contract

Status: contract reviewed; implementation pending

Date: 2026-08-03

## Reference Dependency Rule

Reference app reviewed:

`_PARTS-FOR-PLANS/_UiMAPPER/`

Primary files reviewed:

- `_PARTS-FOR-PLANS/_UiMAPPER/README.md`
- `_PARTS-FOR-PLANS/_UiMAPPER/src/app.py`
- `_PARTS-FOR-PLANS/_UiMAPPER/src/ui.py`
- `_PARTS-FOR-PLANS/_UiMAPPER/src/backend.py`
- `_PARTS-FOR-PLANS/_UiMAPPER/src/microservices/`
- `_PARTS-FOR-PLANS/_UiMAPPER/tools/`

The locators in this document and in
`src/useful_helpers/tools/ui_mapper/adapter.py` are temporary review anchors.
They may guide implementation, but the Useful Helpers runtime must not import
from, read from, or require the parts-bin app.

When a UiMAPPER capability is fully re-homed, remove the corresponding
parts-bin locator from runtime tool code. Historical provenance may remain in
this document or `_docs/SOURCE_PROVENANCE.md`.

## Reference Frailties Found

- Reference app is Python/Tkinter focused; Useful Helpers must not treat it as a general UI detector yet.
- Reference inference path depends on local Ollama configuration and must remain optional.
- Reference GUI helper microservices overlap with Useful Helpers shell concerns and should inform design, not replace local UI modules wholesale.
- Reference maintenance scripts rewrite imports and inspect microservice constructors; they are provenance/repair tools, not runtime features.

## Tool Done State

The UiMAPPER tool family is done when Useful Helpers can run a local,
stdlib-friendly UI-mapping pipeline over an explorer-selected Python project;
honor exclusions and gitignore rules; enumerate Python files; parse ASTs; detect
Tkinter/customtkinter windows, widgets, layout calls, configuration calls,
bindings, menu calls, and callback targets; build a callback graph; collect
unknown cases; optionally prepare inference/HITL decision plans only when
configured; serialize markdown/json/jsonl report artifacts; surface
progress/cancel/log/session state in the GUI; and run entirely from local Useful
Helpers modules with no runtime dependency on the parts-bin reference app.

Optional inference rule:

Ollama/inference/HITL behavior is optional and must not be required for the base
UiMAPPER done state. A missing Ollama model or service must be a visible skipped
state, not a hard failure.

## Capability Map

### Scan Python Project

Target outcome:

Given an explorer-selected project root, crawl project entries while honoring
exclusions and gitignore-style filters, then enumerate Python files.

Expected inputs:

- project root path
- exclusion policy
- gitignore filter
- optional cancellation signal

Expected outputs:

- crawl entries
- Python file list
- skipped/ignored path evidence

Reference anchors:

- `class GitignoreFilterMS` at line 50
- `class ProjectCrawlMS` at line 50
- `def enumerate` at line 80

Search locator:

```bat
rg -n "class GitignoreFilterMS|class ProjectCrawlMS|def enumerate" "_PARTS-FOR-PLANS\_UiMAPPER\src\microservices"
```

Done when:

Useful Helpers can identify the Python files eligible for UI mapping without
importing the reference app or traversing excluded folders.

### Detect UI Entrypoints

Target outcome:

Score likely Tkinter application entrypoints from the enumerated Python files.

Expected inputs:

- project root path
- Python file list

Expected outputs:

- ranked entrypoint candidates
- score reasons

Reference anchors:

- `def find_candidates` at line 80

Done when:

The right pane/tool surface can show likely UI entrypoints before or after a
full map run.

### Parse Python AST Cache

Target outcome:

Parse eligible Python files into reusable AST results with stable parse-error
records.

Expected inputs:

- Python file list
- encoding policy
- optional cancellation signal

Expected outputs:

- path-to-AST map
- parse error list
- cache hit/miss metadata

Reference anchors:

- `def parse` at line 70
- `ast.parse(text, filename=str(path))` at line 112

Done when:

Full map runs reuse parsed ASTs and report syntax errors without failing the
entire operation.

### Map Tkinter UI Surface

Target outcome:

Detect Tkinter/customtkinter windows, widgets, layout/config/bind/menu calls,
parent-child structure, callback attributes, and unknown cases.

Expected inputs:

- project root path
- path-to-AST map
- parse error list

Expected outputs:

- UiMap windows
- UiMap widgets
- unknown mapping cases
- parse errors

Reference anchors:

- `class TkWidgetDetectorMS` at line 60
- `def map_project` at line 103
- `class UiMap` at line 80

Search locator:

```bat
rg -n "class TkWidgetDetectorMS|def map_project|class UiMap|detect_widget_ctor|detect_bind_call" "_PARTS-FOR-PLANS\_UiMAPPER\src\microservices"
```

Done when:

Useful Helpers can produce a structured UI map for Python Tk projects and
serialize it through local models.

### Build Callback Graph

Target outcome:

Build event-to-handler and internal function-call graph records from the UI map
and ASTs.

Expected inputs:

- path-to-AST map
- UiMap

Expected outputs:

- graph nodes
- graph edges
- unresolved graph unknowns

Reference anchors:

- `def build` at line 81
- `self.cb_graph_ms.build` at line 396

Done when:

Useful Helpers can show or export callback relationships for mapped UI projects.

### Collect Unknown Cases

Target outcome:

Capture uncertain UI detections for reporting, review, and optional inference
routing.

Expected inputs:

- UiMap unknowns
- AST node context
- selection policy

Expected outputs:

- deduplicated unknown cases
- summaries by kind
- summaries by file

Reference anchors:

- `class UnknownCaseCollectorMS` at line 74
- `self.unknown_collector_ms.record` at line 361

Done when:

Unknowns are visible as first-class evidence instead of silent mapping loss.

### Optional Inference And HITL

Target outcome:

Optionally prepare prompts for unknown cases, validate model output, and route
decisions into auto-apply, ask-user, or reject buckets.

Expected inputs:

- unknown cases
- project context
- optional Ollama model
- HITL policy thresholds

Expected outputs:

- prompt text
- validated decisions
- decision plan
- skipped inference state

Reference anchors:

- `settings.enable_inference` at line 416
- `def build_prompt` at line 46
- `def generate` at line 74
- `def validate_json_text` at line 86
- `def build_plan` at line 72
- `_view_decision_plan` at line 546

Done when:

Ollama/inference/HITL behavior is optional and must not be required for the base
UiMAPPER done state. A missing Ollama model or service must be a visible skipped
state, not a hard failure.

### Serialize And Write Reports

Target outcome:

Write markdown, JSON, and JSONL artifacts for the UI map and callback graph.

Expected inputs:

- UiMap
- callback graph
- output directory
- format toggles

Expected outputs:

- markdown report path
- JSON report path
- JSONL report path

Reference anchors:

- `class ReportSerializerMS` at line 42
- `def write_markdown` at line 137
- `self.report_writer_ms.write_markdown` at line 531

Search locator:

```bat
rg -n "class ReportSerializerMS|def write_json|def write_jsonl|class ReportWriterMS|def write_markdown|self.report_writer_ms.write_markdown" "_PARTS-FOR-PLANS\_UiMAPPER\src"
```

Done when:

A completed run produces selected report artifacts with paths surfaced in the
GUI.

### Run Pipeline With Progress

Target outcome:

Coordinate scan, parse, map, graph, optional inference, and reporting as a
cancellable background operation with session-state updates.

Expected inputs:

- project root path
- backend settings
- progress subscriber
- cancellation token

Expected outputs:

- session status
- progress events
- counters
- errors
- report paths

Reference anchors:

- `class BackendSettings` at line 92
- `class BackendOrchestrator` at line 119
- `def start_run` at line 170
- `def cancel_run` at line 225
- `class ProgressEventBusMS` at line 48
- `class RunSessionState` at line 47
- `class CancellationTokenMS` at line 30

Done when:

The workbench can run UiMAPPER without freezing the GUI, cancel an active run,
and inspect the final session snapshot.

### UiMAPPER GUI Workflow

Target outcome:

Expose project selection, run/cancel controls, progress logs, result summaries,
structure tree, report paths, copied JSON, and decision-plan viewing.

Expected inputs:

- selected project root
- run settings
- backend session state
- progress events

Expected outputs:

- tool form state
- log lines
- summary rows
- structure tree
- decision-plan dialog

Reference anchors:

- README `UI map + callback graph + report artifacts` at line 6
- `def main` at line 32
- `build_ui(root, backend)` at line 56
- `class UiOrchestrator` at line 122
- `self.bus.subscribe` at line 150
- `_run_clicked` at line 511

Done when:

Useful Helpers exposes UiMAPPER as a Tools menu workflow while keeping the main
explorer-first shell as the front door.

### Maintenance Tools Reference Only

Target outcome:

Treat reference import-rewrite and constructor-inspection scripts as historical
repair evidence, not product behavior.

Reference anchors:

- `rewrite_imports_in_file` at line 28
- `def main` in `check_ms_inits.py` at line 10

Done when:

No Useful Helpers runtime command depends on these reference maintenance scripts.

## Implementation Notes

- Preserve the reference app's architectural split as a design cue: `app.py`
  composition shell, `ui.py` UI orchestrator, `backend.py` pipeline
  orchestrator.
- Do not copy the reference GUI wholesale into the Useful Helpers front door.
  UiMAPPER should become a Tools menu workflow inside the existing explorer-first
  workbench.
- Keep base mapping stdlib-friendly. Optional local model inference can be added
  only behind explicit settings and clear skipped/failure states.
- The reference app's UI mapping is Python/Tkinter-centered. Broader UI
  framework support must be a later explicit capability.
- The typo in the parts-bin folder name is preserved in locators because it is
  the actual folder path.
