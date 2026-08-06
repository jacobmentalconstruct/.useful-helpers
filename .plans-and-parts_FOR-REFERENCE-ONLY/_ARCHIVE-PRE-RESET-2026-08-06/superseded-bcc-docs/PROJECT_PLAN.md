# Project Plan

Status: active. Created Tranche 0, 2026-08-05.

Tranche numbering in this document is **this project's only valid numbering**.
Identifiers appearing in inherited material belong to predecessor projects.

Every tranche follows the BCC required tranche workflow
(anchor `BCC-WORKFLOW-REQUIRED-TRANCHE-LOOP`) and ends in a documented park
state.

---

## Progress

| # | Tranche | Status |
| --- | --- | --- |
| 0 | Establish Current Authority | **Complete** |
| 1 | Capability and Command-Surface Audit | **Complete** (findings provisional) |
| 2 | Minimal Runtime Scaffold | Next |
| 3 | Project Context Core | Pending |
| 4 | Explorer-First GUI Shell | Pending |
| 5 | Unified Operation Framework | Pending |
| 6 | Toolkit Bridge and Read-Only Integration | Pending — gated |
| 7 | Project Mapper Vertical Slice | Pending |
| 8 | Safe File-Mutation Foundation | Pending |
| 9 | Git Workflow | Pending |
| 10 | Structural Intelligence | Pending |
| 11 | Monaco Shared Session | Pending |
| 12 | Optional Chat and DAC Workflow | Pending |
| 13 | Reversible Evidence and Retrieval | Pending |
| 14 | Runtime Packaging Decision | Pending |
| 15 | Packaging, Hardening, and Closure | Pending |

---

## Tranche 0 — Establish Current Authority · COMPLETE

**Goal.** Convert the copied sandbox into a truthful new project starting point.

Delivered: BCC placeholders resolved for this root; `.bcc/` established as
builder-control storage; active journal created at `_docs/AppJOURNAL/0001`;
`CURRENT_STATE.md`, `PROJECT_PLAN.md`, `SOURCE_PROVENANCE.md`, `TESTING.md`
created; inherited zones recorded as reference-only or conditional; absence of
any workbench runtime recorded; ignore rules defined.

Non-goals honoured: no application code, no source migration, no GUI scaffold,
no tool implementation.

---

## Tranche 1 — Capability and Command-Surface Audit · COMPLETE

**Goal.** Prevent duplicate implementations by deciding how the twelve plans and
the toolkit relate.

Delivered: all twelve reference contracts enumerated; 99 toolkit manifests
enumerated; capabilities grouped by domain; overlaps mapped; unique capabilities
identified; toolkit root resolution, invocation, and result envelope audited;
workbench operation request/result/event/manifest/authority contracts drafted in
`ARCHITECTURE.md` §8; toolkit bridge boundary decided; conclusion that **no
toolkit changes are necessary** for target-root binding.

**Central question answered.** See `CAPABILITY_MATRIX.md` §6.

**Carried gap.** No toolkit code was executed. Findings are provisional and a
mandatory safety gate precedes Tranche 6.

Non-goals honoured: no tool GUI, no broad source copying, no mutation tool
implementation.

---

## Tranche 2 — Minimal Runtime Scaffold · NEXT

**Goal.** A runnable, testable workbench package with no product functionality
beyond startup.

Work: `src/app.py`; package structure; logging; path and configuration
providers; state-root resolution with test and development overrides; a
`--status` smoke mode; test configuration; run and setup scripts; root README.

Completion: package imports; status smoke passes; tests run from the root; no
runtime module imports a reference source; no runtime state is checked in.

Non-goals: no GUI, no tools, no toolkit calls, no scanning.

---

## Tranche 3 — Project Context Core

Deterministic project scanning and selection. Typed path and project-item
models; text/binary classification; exclusion policy; `.gitignore`-informed
filtering; typed scanner; skipped-path records; folder and file inspection;
browse-selection and operation-inclusion models; stable relative-path identity;
scan generation and fingerprint.

Completion: core behavior fully testable without Tk.
Non-goals: no snapshot compiler, no GUI tool operations, no mutation.

---

## Tranche 4 — Explorer-First GUI Shell

Main window; project-open workflow; explorer tree; visible browse selection;
visible operation inclusion; context inspection; rescan; skipped-path summary;
status bar; empty tool workspace; safe startup and shutdown.

Completion: a user can open, browse, inspect, include, exclude, and rescan.
Non-goals: no tool execution, no chat, no editor service, no Git mutation.

---

## Tranche 5 — Unified Operation Framework

The shared command path, built before any tool is integrated. Manifest model;
registry; authority rules; dispatcher; background task queue; cancellation;
event stream; result model; operation persistence; confirmation tokens;
dry-run/apply distinction; target-root containment; target-fingerprint
revalidation; GUI result surface; CLI test client.

Completion: a synthetic Observe tool and a synthetic Apply tool invoke
identically through GUI and headless clients, with recorded events.
Non-goals: no reference-app migration, no dynamic Python loading, no agent host.

---

## Tranche 6 — Toolkit Bridge and Read-Only Integration · GATED

**Blocked until the safety gate in `CAPABILITY_MATRIX.md` §7 is executed.**

Manifest translation; explicit target-root, toolkit-home, state and artifact
root binding; subprocess invocation; result normalization; error propagation;
event attribution; read-only capability allowlist.

Completion: at least three deterministic read-only toolkit tools operate on an
externally selected project without writing into it unexpectedly.

Mandatory acceptance: target root unchanged; toolkit state lands only in its
approved roots; GUI and headless calls share the dispatch path; failure
diagnostics remain visible.

---

## Tranche 7 — Project Mapper Vertical Slice

The first complete user workflow, and the proof that explorer selection,
background work, storage, artifact generation, and results work end to end
without mutating the project.

---

## Tranche 8 — Safe File-Mutation Foundation

Common mutation layer — target planning, containment, encoding detection,
newline policy, backup policy, atomic writes, diff generation, multi-file
preflight, batch policy, per-file results — then TextTOUCHER, Line Numberizer,
and Tokenizing Patcher on top of it.

Completion: all three share one write authority. No tool owns a private write
path.

---

## Tranches 9–15

9 Git Workflow · 10 Structural Intelligence · 11 Monaco Shared Session ·
12 Optional Chat and DAC Workflow · 13 Reversible Evidence and Retrieval ·
14 Runtime Packaging Decision · 15 Packaging, Hardening, and Closure.

Scope for these follows the governing blueprint. They are not elaborated here
until their predecessors are parked, to avoid planning ahead of evidence.

---

## Backlog

| Item | Origin | Priority |
| --- | --- | --- |
| Execute the toolkit safety gate | Tranche 1 | High — blocks Tranche 6 |
| Measure precept-guard cost on a large target | Tranche 1 | Medium |
| Decide per-tool timeout policy | Tranche 1 | Medium — Tranche 5 |
| Confirm `linenumber` covers strip as well as annotate | Tranche 1 | Medium — Tranche 8 |
| Confirm `bd_*` verbatim reconstruction | Tranche 1 | Medium — Tranche 13 |
| Decide whether `attach` is safe against a user project | Tranche 1 | Medium — Tranche 6 |
| Resolve WASM naming honestly | Blueprint | Low — Tranche 14 |
