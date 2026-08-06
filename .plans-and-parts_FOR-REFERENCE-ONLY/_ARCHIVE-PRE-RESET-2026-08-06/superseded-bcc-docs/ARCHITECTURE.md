# Architecture

Status: first edition, produced by Tranche 1. No runtime code exists yet.
Date: 2026-08-05.

This document records structural intent and the drafted operation contracts.
It describes what the workbench **will** be. Nothing here is implemented.

---

## 1. Product Shape

Useful Helpers Workbench is a local, explorer-first desktop workspace for
inspecting software projects, selecting bounded working context, and performing
controlled project operations through one unified tool system.

Primary loop:

```
Observe -> Select -> Operate -> Verify
```

It opens directly into an active project workspace, not a landing page.

It is **one application** that absorbs and reorganizes the useful capabilities of
twelve predecessor applications. It is explicitly not twelve applications behind
twelve buttons.

---

## 2. Structural Laws

These derive from the BCC and the blueprint's safety-critical invariants. They
are not preferences.

1. Reference source is never imported at runtime.
2. Browse selection never implies mutation authority.
3. Every mutation has a previewable target plan.
4. Every operation is bound to an explicit project root.
5. Every client uses the same dispatch path.
6. Every mutating tool declares what it may write.
7. No arbitrary Python file is executed merely because it exists in a directory.
8. Git stages explicit approved paths.
9. Pull failure stops push by default.
10. Monaco save is gated.
11. Agent activity uses the same authority system as human UI activity.
12. Deterministic functionality does not require a local model.
13. Graph or inferred relationships do not replace verbatim evidence.
14. Runtime state is not stored in `.bcc/` or `_docs/`.
15. Checked-in source carries no inherited personal paths, remotes, tokens,
    runtime databases, or crash data.
16. The product's name and claims describe what it actually implements.

---

## 3. Zones and Runtime Dependency

| Zone | Role | Runtime dependency |
| --- | --- | --- |
| `.bcc/` | Builder contract, planning, current state, provenance, testing, capability matrix, evidence | Forbidden |
| `_docs/` | Builder-control documentation and the active journal | Forbidden |
| `.plans-and-parts_FOR-REFERENCE-ONLY/` | Plans and original source evidence | Forbidden |
| `_design/` | Historical toolkit design evidence | Forbidden |
| `_harness/` | Historical toolkit proving ground | Forbidden |
| `toolkit/` | Existing tool subsystem and builder instrument | Conditional, through an explicit bridge only |
| `src/` | New workbench runtime | Required |
| `tests/` | New workbench verification | Development only |
| `docs/` | Product-facing documentation | Optional |
| `assets/`, `config/`, `scripts/` | Workbench-owned support | Required when used |

The forbidden zones must be deletable with the completed workbench still
running. This is an enforced boundary test, not an aspiration.

Note the deliberate distinction between `_docs/` (builder-control, underscore)
and `docs/` (product-facing, no underscore). Only the latter may ever be
packaged.

---

## 4. Composition Root

`src/app.py` is the single composition root. It:

- resolves configuration and state roots,
- creates the application-level context,
- initializes storage,
- initializes the operation registry,
- initializes the dispatch authority,
- initializes the background task system,
- builds the UI,
- coordinates startup and shutdown.

It contains no tool implementations and no significant UI logic.

There is exactly one top-level state authority. Competing authorities are a
contract violation.

---

## 5. Layering

```
src/app.py                     composition root
  └─ ui/app_orchestrator.py    UI-side coordination only
  └─ operations/dispatcher.py  the one operation chokepoint
       ├─ operations/registry.py + manifests.py + authority.py
       ├─ operations/task_queue.py + cancellation.py + events.py
       ├─ tools/<family>/       workbench-owned tool backends
       └─ integrations/toolkit_bridge.py -> toolkit/ subprocess seam
  └─ core/                     scanning, selection, inspection, paths
  └─ storage/                  sqlite, state, settings
```

Rules:

- UI code never performs file writes and never calls a tool backend directly.
- Tool backends never bypass the dispatcher.
- `core/` has no dependency on `ui/` or on the toolkit.
- Only `integrations/toolkit_bridge.py` may know the toolkit exists.

---

## 6. The One Operation Path

A capability has **one implementation and one governed dispatch path,
regardless of caller.** GUI actions, CLI commands, workflow steps, agent calls,
optional MCP requests, and tests all converge on the same dispatcher.

No capability may have a GUI implementation, a second agent implementation, and
a third CLI implementation.

This principle is confirmed by four independent sources; see
`CAPABILITY_MATRIX.md` §5.

### 6.1 Backend before UI

Tool behavior is implemented and tested headlessly before any GUI control
invokes it. The UI is never the only way to test a scan, a patch, a snapshot, a
line-map operation, a file write, a Git action, a workflow transition, or a save
gate.

---

## 7. Explicit Roots

Every project operation binds to an explicit target root. The system
distinguishes seven roots and never infers them from the ambient working
directory:

- workbench application root
- toolkit home
- open project root
- runtime state root
- artifact output root
- reference-source root
- builder-control root

Runtime state lives under a state-root provider with a platform-appropriate
user-data location, a test override, and a development override
(`USEFUL_HELPERS_STATE_ROOT`). It is never written into `.bcc/` or `_docs/`, and
never checked into source control.

Generated artifacts default **outside** the opened project unless the user
explicitly chooses a project destination.

---

## 8. Drafted Operation Contracts

Drafted in Tranche 1; to be implemented in Tranche 5. Field names are normative.

### 8.1 Tool manifest

```
id                label             category          description
authority         operates_on       writes            input_schema
output_schema     entrypoint        execution_mode    supports_dry_run
supports_cancel   supports_batch    version           provenance
```

Manifests are the only registration path. Executable entrypoints are
allowlisted and containment-checked. There is no directory scan that grants a
dropped file the ability to run.

### 8.2 Operation request

```
operation_id      tool_id           client            target_root
arguments         inclusion_set     authority_request dry_run
apply             scan_generation   correlation_id    requested_at
```

`client` is one of: `gui`, `cli`, `workflow`, `agent`, `mcp`, `test`.
It is recorded, never used to grant privilege.

### 8.3 Operation result

```
operation_id      tool_id           ok                status
summary           data              artifacts         warnings
errors            diagnostics       stdout            stderr
exit_code         started_at        finished_at       duration_ms
target_fingerprint
```

This is the workbench envelope. Translation from the toolkit's `{"ok": bool}`
shape happens exactly once, inside `ToolkitBridge`. The toolkit is not modified.

### 8.4 Authority ladder

| Level | Meaning |
| --- | --- |
| `Observe` | No project or external mutation. |
| `Prepare` | May create disposable previews or plans outside the target. |
| `Apply` | May modify approved project paths. |
| `External` | May affect Git remotes, networks, processes, dependencies. |

The UI never infers authority from a button label. The dispatcher enforces it.

Mapping to the toolkit's three-level ladder:

| Workbench | Toolkit | Note |
| --- | --- | --- |
| `Observe` | `Observe` | direct |
| `Prepare` | `Sandbox` | toolkit Sandbox runs project code; treated as Prepare |
| `Apply` | `Apply` | direct |
| `External` | `Apply` | **no toolkit equivalent** — the workbench must gate separately |

The `External` gap is material: the toolkit cannot distinguish "writes a file"
from "pushes to a remote". Any bridged tool touching network, remotes, processes
or dependency installation must be classified `External` by the workbench's own
allowlist, never by trusting the toolkit's `authority` field alone.

### 8.5 Dispatcher responsibilities

Manifest resolution, target-root validation, authority validation,
inclusion-set normalization, confirmation validation, task scheduling, process
invocation, output capture, result normalization, event recording,
cancellation, and final state publication.

Tool modules do not bypass it.

### 8.6 Mutation preconditions

A mutating operation requires all of: a concrete target, a declared path set, a
visible action plan, validation, authority approval, explicit confirmation, and
a recorded result.

Confirmation tokens bind to a specific plan **and** a specific
`scan_generation` / `target_fingerprint`. A stale plan is revalidated before
mutation, never applied optimistically.

---

## 9. Application State

### 9.1 Project session

```
project_root      scan_generation   project_tree      skipped_paths
browse_selection  operation_inclusion                 active_tool
active_operations recent_results    project_fingerprint
```

### 9.2 Two separate selection domains

- **Browse selection** answers *what is being inspected?* — zero or one item.
- **Operation inclusion** answers *what may the next operation consider?* —
  many items, preserved across ordinary browsing.

These are distinct state domains. Clicking a file does not authorize writing to
it. This is structural, not a UI convention.

---

## 10. Toolkit Bridge

`integrations/toolkit_bridge.py` is the only module aware of `toolkit/`.

It must:

- discover or import manifest data,
- translate workbench requests into toolkit calls,
- launch the toolkit through its supported command seam,
- supply an explicit target root **per invocation**, never by mutating the
  workbench process environment,
- validate the target root itself before launching, because the toolkit falls
  back silently on a bad root,
- verify the echoed root in the result matches the root requested,
- treat unparseable tool output as failure, not success,
- capture and normalize structured results into the workbench envelope,
- preserve authority metadata,
- redact absolute host paths from diagnostics before display,
- publish progress and events into the workbench,
- avoid importing individual toolkit tool implementations,
- refuse calls whose output or mutation boundary cannot be proven.

If `toolkit/` ships with the product it is a deliberate bundled subsystem with a
documented compatibility contract, not an accidental path dependency.

---

## 11. Heavy Systems Are Optional

Agent hosts, local models, embeddings, graph stores, Monaco, Qt/webview
components, RAG, and WASM runtimes are not startup requirements. The explorer
and the deterministic tools must remain fully useful without them.

A runtime graph engine, message bus, or event-sourcing system is **not** adopted.
The blueprint does not earn one. Coordination is explicit typed interfaces,
services, and managers. An append-only SQLite event log is used as a trace and
audit ledger only, and will not be described as event sourcing unless replay,
reconstruction, snapshotting, and reducer semantics actually exist.
