# 0025 - TheDISMANTLER Tool Contract Review

Date: 2026-08-04

## Tranche

Root Tranche 14H: TheDISMANTLER Tool Contract Review.

Goal: review the last unreviewed parts-bin app and extract the GUI-side dispatch
prior art that completes the input set for Root Tranche 15.

Expected completion point:

- reference architecture inspected,
- the reusable dispatch rule identified and recorded,
- the unsafe pattern identified and explicitly forbidden,
- contract doc written,
- adapter scaffolded,
- registry exposes the tool as pending,
- tests pin capabilities, rules, and frailties,
- parts-bin coverage reaches twelve of twelve.

Non-goals held:

- no runtime implementation,
- no dispatch framework implementation, which is Root Tranche 15,
- no envelope decision,
- no adoption of auto-discovery,
- no Ollama or local-model integration,
- no changes to the existing 91 tools under `tools/`,
- no runtime dependency on the parts bin.

## Current State Before Work

`_TheDISMANTLER` was the last of the three parts-bin apps found unreviewed in
journal 0022. At 10,632 lines it is by far the largest reference, so it was
reviewed for architecture rather than line by line. The dispatch spine, tool
interface, workflow orchestrator, bootstrapper, and a representative UI call
site were read in full.

## Key Findings

**It is a real Tkinter application.** `src/app.py:20` is
`class AppBootstrapper(tk.Tk)`. Unlike MonacoVIEWER, which imports tkinter as a
"contract compliance" gesture and is actually Qt, this reference is in the
workbench's own toolkit. Its architecture is directly applicable rather than
requiring translation.

**It states the single-chokepoint rule in its own source.**
`src/backend/modules/refinement_engine.py:228` feeds its own AI the constraint:
"All UI-backend communication goes through `BackendEngine.execute_task()`".
Twenty-plus UI call sites obey it.

**It already proves a non-human caller can share the human's path.**
`WorkflowEngine` is constructed with `execute_fn=backend.execute_task` and runs
declared multi-step sequences with zero UI dependencies. A human clicking a menu
item and an unattended workflow are indistinguishable to the backend. That is
the human/agent symmetry the project wants, demonstrated in Tk.

**This is the third independent statement of one principle.** MonacoVIEWER
requires session symmetry with one shared event record. manifold-mcp requires
that MCP and CLI never fork behavior. TheDISMANTLER requires that all UI-backend
communication go through one call. Three unrelated designs converging settles
the question: Root Tranche 15 must be built on a single dispatch chokepoint.
Recorded as `CONVERGENT_DOCTRINE_NOTE`.

**Its tool loading is the most dangerous pattern found in any reference.**
`BackendEngine._discover_and_load_tools` (`src/backend/main.py:104`) lists
`src/backend/tools/`, dynamically imports every `.py` file not starting with
`_`, and calls `spec.loader.exec_module(module)` during `boot()`. It then calls
`tool.initialize()` on each discovered class. `TOOLS_README.md` advertises this
as a feature: drop a file in the directory and it loads automatically.

In an ordinary desktop app that is merely risky. In a workbench where an agent
can write files, it is arbitrary code execution at next launch, reached by
writing one file. This is recorded as `SAFE_LOADING_RULE`, an explicit
prohibition rather than a caveat, and pinned by a dedicated test.

**Routing identity is unstable.** `src/backend/main.py:153` derives the routing
key from `tool.name.lower().replace(" ", "_")`, so renaming a display label
silently breaks routing and similarly-named tools collide. Tools register into
`self.controllers`, the same dict as core controllers, guarded only by a
hardcoded `_RESERVED_KEYS` literal listing the five currently-known core names.
Any future controller is unprotected. Recorded as `STABLE_ROUTING_RULE`.

**There is no declared schema.** `BaseTool.handle(schema)` takes an untyped
dict. `validate_schema` exists but is opt-in and requires each tool to supply its
own `required_keys`. No caller can discover a tool's parameters without reading
its source, which is exactly what manifold-mcp's `input_schema` solves.

## The Completed Input Set

Root Tranche 15 now has four inputs, and they are complementary rather than
competing:

| Input | Contributes | Lacks |
| --- | --- | --- |
| `tools/` (in repo, 91 tools) | Safety and authority layer: path containment, confirmation gating, scoped roots, evidence, `authority` and `operates_on` | Any agent transport |
| manifold-mcp | Agent transport and machine-readable `input_schema` generated from one source | Any safety layer |
| TheDISMANTLER | GUI dispatch chokepoint and in-process tool interface, in Tk, plus workflow orchestration | Any safety layer, any declared schema |
| MonacoVIEWER | Requirement that the event record be observable by every client, not just the command path shared | Is not Tk; needs a separate process |

The central design fact: **none of the three parts-bin references has a safety
layer. The repository's own `tools/` has the only one.** Recorded as
`FRAMEWORK_INPUT_NOTE`.

## Decisions

None required from the user. Two rules were recorded as prohibitions rather than
preferences because both references and the existing codebase disagree:

- `SAFE_LOADING_RULE` forbids adopting drop-in code execution.
- `STABLE_ROUTING_RULE` forbids display-name routing and shared namespaces.

The envelope decision remains deferred to Root Tranche 15. This review adds a
data point: TheDISMANTLER also uses `{"status": ..., "message": ...}`, so two of
three references use `status` while the in-repo convention uses `ok`.

## Implementation

Added:

- `_docs/THE_DISMANTLER_TOOL_CONTRACT.md`,
- `src/useful_helpers/tools/the_dismantler/__init__.py`,
- `src/useful_helpers/tools/the_dismantler/adapter.py`,
- `tests/test_the_dismantler_adapter_contract.py`.

Updated `src/useful_helpers/tools/registry.py` so the tool appears as
`TheDISMANTLER` with status `contract reviewed; implementation pending; GUI
dispatch prior art; auto-discovery unsafe to adopt`.

The adapter defines nine capabilities: `single_dispatch_chokepoint`,
`declared_tool_interface`, `stable_routing_identity`, `namespace_isolation`,
`safe_tool_loading`, `authority_enforced_dispatch`, `workflow_orchestration`,
`non_blocking_execution`, and `dispatch_provenance`. It carries 22 reference
locators across six files.

Five capabilities are owned wholly or partly by Root Tranche 15 rather than by
this tool, because they are framework concerns this reference happens to
demonstrate.

Added `test_all_twelve_parts_bin_apps_now_have_reviewed_contracts`, which asserts
the registry covers all twelve parts-bin sources. This is a regression guard
against the coverage gap found in journal 0022 recurring.

## Review Findings And Repairs

No repairs required. The tranche is additive; the only edit to existing runtime
code was the single registry tuple entry.

## Verification

Cross-platform partial run (Linux sandbox; no `tkinter`, so the three
Tk-importing modules were excluded):

```bash
python -m pytest -q -p no:cacheprovider \
  --ignore=tests/test_project_mapper_adapter_contract.py \
  --ignore=tests/test_project_mapper_backend.py \
  --ignore=tests/test_ui_theme_contract.py
```

Result: `2 failed, 104 passed`. The two failures are the known Windows-only
assertions recorded in journal 0022, unchanged by this tranche.

Focused run:

```bash
python -m pytest -q -p no:cacheprovider tests/test_the_dismantler_adapter_contract.py
```

Result: `11 passed`.

Test function count is now 114 (103 after Tranche 14G, plus 11). Debris check
after the run: `_state/` contained only `evidence.sqlite3`.

Authoritative Windows verification: PENDING. Expected `114 passed`. One run
covers Tranches 14F, 14G, and 14H, none of which has been confirmed on Windows.

## Residual Risks

- The envelope conflict is unresolved and now has three data points against the
  in-repo convention by count, but the in-repo convention is the only one with a
  safety layer. Count is not the deciding argument.
- The 91 tools under `tools/` remain unreviewed as a system. Root Tranche 14I is
  planned for this and should run before or during Root Tranche 15.
- Root Tranche 15 is now a larger design task than originally scoped. It must
  reconcile four input designs, settle the envelope, and define authority,
  containment, provenance, threading, and event observability. It may warrant
  splitting.
- TheDISMANTLER's capability surface (curation, AST walking, manifest building,
  sliding-window context, transformation, patch preview, export) overlaps
  existing tools including Project Mapper, Line Numberizer, and Tokenizing
  Patcher. Overlap resolution is deferred and should not be settled by importing
  the reference wholesale.

## Park Point

Root Tranche 14H is complete pending the Windows verification run. All twelve
parts-bin apps now have reviewed contracts and scaffolded adapters, guarded by a
regression test.

Next recommended action: Root Tranche 14I, review the 91 existing `tools/` as a
system, then Root Tranche 15 with all four inputs in hand.

## Session Closeout

Parked for the day at this point. Two closeout artifacts were produced alongside
this tranche:

- `_docs/SESSION_SUMMARY_2026-08-04.md`: narrative of every tranche from the 14D
  closeout through 14H, what was done and why, decisions taken, the convergent
  through-line across three references, and five open questions.
- `scripts/export_docs_bundle.py` plus `_docs/TOOLS.md`: a repeatable
  documentation packager. It collects the plan, contract, architecture, all
  twelve tool contracts, all journal entries, provenance, and testing docs into
  a dated zip with a generated index and reading order, written to
  `artifacts/exports/` (Git-ignored, removable, non-runtime).

First bundle produced: `artifacts/exports/useful-helpers-docs-2026-08-04.zip`,
48 documents, integrity verified.

The script was added rather than doing a one-off zip because the export is
plainly recurring: any future session park, handoff, or review will want the
same bundle. It is CLI-accessible per BCC 10.2 and documented per BCC 10.4.
