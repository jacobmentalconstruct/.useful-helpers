# TheDISMANTLER Tool Contract

Status: contract reviewed; implementation pending; primary value is GUI-side
dispatch prior art; auto-discovery is an unsafe pattern to adopt as-is

Reference app:
`_PARTS-FOR-PLANS/_TheDISMANTLER/`

10,632 lines of Python. Reviewed for architecture, not line by line. Primary
files:

- `src/app.py` (158 lines): Tk bootstrapper and system console.
- `src/backend/main.py` (172 lines): `BackendEngine`, `execute_task`, tool
  auto-discovery.
- `src/backend/tools/base_tool.py` (148 lines): `BaseTool` abstract interface.
- `src/backend/modules/workflow_engine.py` (230 lines): JSON-driven sequential
  orchestrator over the same dispatch.
- `src/ui/main_window.py` (647 lines): Tk UI issuing dispatch calls.
- `TOOLS_README.md`, `TRANSFORMER_README.md`, `README.txt`.

Runtime contract surface:
`src/useful_helpers/tools/the_dismantler/adapter.py`

## Intent

This reference serves two purposes, kept separate in this contract.

**Primary purpose: GUI-side dispatch prior art.** TheDISMANTLER is the third and
last input to Root Tranche 15, and the only one that is actually a Tkinter
application. It demonstrates a Tk UI and an automated non-human caller driving
the same backend through a single chokepoint. That is the workbench's problem,
in the workbench's toolkit.

**Secondary purpose: monolith decomposition capability.** Curation, AST walking,
manifest building, sliding-window context, transformation, patch preview, and
export. Useful, but not why the review was prioritized.

## The Rule Worth Adopting

`BackendEngine.execute_task(schema)` is the single entry point. The schema
carries a `system` key naming the target and an `action` key naming the
operation. `src/backend/modules/refinement_engine.py:228` states the rule
outright, as a constraint the app feeds to its own AI:

> All UI-backend communication goes through `BackendEngine.execute_task()`

Twenty-plus UI call sites obey it. More importantly, `WorkflowEngine` takes
`execute_fn=backend.execute_task` and drives multi-step sequences through the
identical path with zero UI dependencies. A human clicking a menu item and an
automated workflow running unattended are already indistinguishable to the
backend.

That is the human/agent symmetry the project wants, demonstrated in Tkinter.

This is now the **third independent statement** of the same principle:

| Reference | Statement of the rule |
| --- | --- |
| MonacoVIEWER (14F) | Session symmetry: neither client privileged, one event record |
| manifold-mcp (14G) | "Do not fork behavior between MCP and CLI paths" |
| TheDISMANTLER (14H) | "All UI-backend communication goes through `execute_task()`" |

Three references arriving at it independently settles the question. The Root
Tranche 15 framework must be built on a single dispatch chokepoint.

## What Each Reference Contributes

Root Tranche 15 now has four inputs, and they are complementary rather than
competing on capability:

- `tools/` (in repo, 91 tools): the safety and authority layer. Path
  containment, confirmation gating, scoped roots, evidence attachment,
  `authority` (`Observe`/`Apply`/`Sandbox`) and `operates_on`
  (`project`/`toolkit`). CLI only.
- manifold-mcp: the agent transport and machine-readable schema. `input_schema`
  per tool, agent-visible tool list generated from the same metadata the CLI
  validates against.
- TheDISMANTLER: the GUI dispatch chokepoint and the in-process tool interface,
  in Tk, plus a workflow orchestrator proving a non-human caller can share it.
- MonacoVIEWER: the requirement that the event record be observable by all
  clients, not just that the command path be shared.

None of the three references has a safety layer. The repository's own `tools/`
has the only one. That asymmetry is the central design fact for Tranche 15.

## Required Stop State

The tool is complete when Useful Helpers can:

- dispatch every tool operation through one owned chokepoint that the GUI, the
  agent, and automated workflows all use,
- declare each tool's input schema in a machine-readable form so callers can
  discover it without reading source,
- route by a stable declared identifier rather than a mutable display name,
- keep tool namespaces separate from core subsystem namespaces,
- load tools without executing arbitrary code found in a drop-in directory,
- enforce authority and containment on every dispatched operation,
- run long operations without blocking the Tk event loop,
- record every dispatch with its originating client for later review,
- do all of this from local Useful Helpers modules with no runtime dependency on
  the parts bin.

## Capabilities

- `single_dispatch_chokepoint`
- `declared_tool_interface`
- `stable_routing_identity`
- `namespace_isolation`
- `safe_tool_loading`
- `authority_enforced_dispatch`
- `workflow_orchestration`
- `non_blocking_execution`
- `dispatch_provenance`

## Safe Loading Rule

Tools must be loaded from a declared, reviewed registry. Discovery must not mean
executing arbitrary `.py` files found in a directory at boot. Any drop-in
loading path must require an explicit manifest entry, and the loader must never
grant a newly-dropped file the ability to run code merely by existing.

This rule exists because the reference violates it, and because the violation is
materially worse in a workbench an agent can write files into. See frailties.

## Reference Frailties

Loading and security:

- `src/backend/main.py:118`-`:135` lists `src/backend/tools/`, dynamically
  imports every `.py` file that does not start with `_`, and calls
  `spec.loader.exec_module(module)` on it during `boot()`. `TOOLS_README.md`
  advertises this as a feature: "Drop a `.py` file in `src/backend/tools/` and
  it's loaded automatically." In a workbench where an agent can write files,
  this is arbitrary code execution at next launch.
- There is no signature, manifest, allowlist, or review gate on discovered
  tools.
- `tool.initialize()` runs during discovery, so a dropped file executes code
  before any user action.

Routing and namespace:

- `src/backend/main.py:153` derives the routing key from
  `tool.name.lower().replace(" ", "_")`. A display-name change silently breaks
  routing, and two tools with names differing only in case or spacing collide.
- Tools are registered into `self.controllers`, the same dict as core
  controllers. `_RESERVED_KEYS` guards only the five known core names; any
  future controller name is unprotected, and the guard is a hardcoded literal
  rather than derived from the registered controllers.

Interface and contract:

- `BaseTool.handle(schema)` takes an untyped dict. There is no declared input
  schema, so no caller can discover a tool's parameters without reading its
  source. `validate_schema` exists but is opt-in and requires the tool to pass
  its own `required_keys`.
- `WorkflowEngine._STEP_REGISTRY` hardcodes `(system, action)` pairs as a class
  attribute, and `register_step` mutates that class-level dict at runtime, so
  workflow vocabulary is global mutable state.

Safety and hygiene:

- There is no authority model and no confirmation gate. Every registered
  controller and tool is equally callable through `execute_task`.
- There is no path containment. `project_root` is derived from
  `os.path.dirname` applied three times to `__file__`, the same fragile
  path-depth pattern found in manifold-mcp.
- `execute_task` catches every exception and returns
  `{"status": "error", "message": str(e)}`, discarding the traceback. Failures
  are diagnosable only through the log callback.
- UI call sites invoke `execute_task` directly on the Tk thread. Long operations
  block the event loop. `WorkflowEngine.run` documents that it must be called
  from a background thread, but nothing enforces it.
- `FileController` auto-archives to `_backupBIN/` inside the reference app,
  which is a reasonable idea with an unreviewed retention and growth policy.

Envelope:

- The envelope is `{"status": "ok"|"error", "message": ..., ...}`, matching
  manifold-mcp's `status` key and conflicting with the repository's own
  `{"ok": bool}`. Two of three references use `status`; the in-repo convention
  uses `ok`. Root Tranche 15 must settle this.

## Non-Goals For This Contract Review

- no runtime implementation,
- no dispatch framework implementation, which is Root Tranche 15,
- no envelope decision,
- no adoption of auto-discovery,
- no Ollama or local-model integration,
- no changes to the existing 91 tools under `tools/`,
- no import/read dependency on the parts bin.
