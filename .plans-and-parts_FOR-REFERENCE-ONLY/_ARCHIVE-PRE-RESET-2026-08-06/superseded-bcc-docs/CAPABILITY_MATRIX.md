# Capability Matrix

Status: second edition. Produced by Tranche 1; **safety gate executed and
findings verified** later the same day.
Date: 2026-08-05.
Verification: the seven-check safety gate has been **run**. See §1.

This document answers the central architectural question posed by the blueprint:

> Which capabilities should the workbench call through the existing toolkit, and
> which capabilities genuinely require new workbench-owned implementations?

It is the governing input to every later tranche. No new backend may be written
for a capability until this matrix explains why existing behavior is
insufficient.

---

## 1. Verification Standing

The findings below were first obtained by reading source. The Linux sandbox then
became available and the **seven-check safety gate in §7 was executed against
the real toolkit.** Results are recorded in `_docs/AppJOURNAL/0002`.

Claim tags:

- `[VERIFIED]` — executed; command and result recorded in journal 0002.
- `[READ]` — read directly from source; not independently executed.
- `[INFERRED]` — reasoned from source; not yet confirmed.
- `[UNKNOWN]` — still undetermined.

### 1.1 Gate results

| # | Check | Result |
| --- | --- | --- |
| 1 | Toolkit runs; manifest count confirmed | **PASS** — 95 tools registered |
| 2 | `SUITE_PROJECT_ROOT` override binds the target | **PASS** |
| 3 | Observe tool leaves target byte-identical | **PASS** |
| 4 | Precept violation fails the call | **PASS** — with a critical caveat, §2.4 |
| 5 | Invalid `SUITE_PROJECT_ROOT` behavior | **FAIL — confirmed frailty**, §4.1 |
| 6 | Timeout behavior | **PASS** — fails cleanly at 120 s |
| 7 | `SUITE_STATE_ROOT` / `SUITE_HOME` redirect | **PASS** |

**Tranche 6 is no longer gated on verification.** It remains gated on the
mitigations in §4.1 being implemented in the bridge.

### 1.2 Corrections to the first edition

- Tool count was stated as 99. **The correct figure is 95 registered tools.**
  The filesystem holds 95 `tools/*/tool.json` files, of which `_template` is a
  scaffold and is not registered; one further registered tool comes from
  `apps/` rather than `tools/`. The earlier 99 was a miscount of glob output.
- The seam's stdout/stderr separation was untested. It is now `[VERIFIED]`
  clean: logs go to stderr, stdout is pure JSON and parses directly.

---

## 2. Toolkit Standing

`toolkit/` is a mature, separately evolved tool system.

- 95 registered tools; `toolkit/VERSION` is `1.1.0` `[VERIFIED]`
- One governed dispatch seam: `toolkit/src/core/invoke.py` `[READ]`
- Authority policy: `toolkit/src/core/policy.py` `[READ]`
- Root resolution: `toolkit/src/core/config.py` `[READ]`
- Shared tool substrate: `toolkit/tools/_toolkit.py` `[READ]`

Note a discrepancy worth recording: the manifold-mcp and TheDISMANTLER contract
reviews both describe "91 tools under `tools/`". The present count is 95. The
toolkit continued to evolve after those reviews were written. Contract-era
statements about the toolkit are therefore dated evidence, not current fact.

The toolkit also ships no third-party runtime dependency for its control plane —
`requirements.txt` declares only `pypdf`, and states the `src/` spine is
standard-library only. `[VERIFIED]` This is why it ran immediately on Linux
despite being a Windows-oriented product.

### 2.1 The decisive finding

The blueprint (§11.2) requires that toolkit root behavior be resolved before any
integration, and warns that the toolkit "understands itself as a sidecar whose
target is associated with its parent or launch context."

That is accurate, **and the override already exists.** `[READ]`

`toolkit/src/core/config.py::_resolve_project_root` resolves the work target in
this order:

1. `SUITE_PROJECT_ROOT` environment variable, if it names an existing directory.
2. Sidecar detection — a `.suite_sidecar` marker file, or a dot-prefixed home
   directory name — in which case the target is the toolkit home's **parent**.
3. Otherwise the toolkit is its own target.

`toolkit/src/core/invoke.py::_dispatch` then launches every tool with
`cwd = paths.project_root` and exports `SUITE_PROJECT_ROOT`, `SUITE_HOME`, and
`PYTHONPATH` into the child environment.

Consequences for this project:

- `toolkit/.suite_sidecar` exists `[READ]`, so with no override the toolkit
  targets `.useful-helpers-workbench/` — this repository itself. This is the
  exact failure mode the blueprint warned about and it is live today.
- A target-root override is available **without modifying the toolkit**, by
  either supplying `SUITE_PROJECT_ROOT` per child process or constructing the
  `Paths` record directly (it is a plain frozen dataclass, so
  `dataclasses.replace(paths, project_root=...)` is sufficient). `[INFERRED]`
- The override must be applied **per invocation**, not by mutating the
  workbench process environment. The blueprint's prohibition on "globally
  changing process working directories in uncontrolled ways" applies equally to
  globally mutating `os.environ`.

**Decision: no toolkit fork is required for target-root binding.** The
`ToolkitBridge` supplies roots explicitly on every call.

### 2.2 Root separation as implemented

| Root | Toolkit resolution | Standing |
| --- | --- | --- |
| Toolkit home | `SUITE_HOME`, else `resolve_paths(root)` | `[READ]` |
| Work target | `SUITE_PROJECT_ROOT`, else sidecar parent, else home | `[READ]` |
| State root | `SUITE_STATE_ROOT`, else `<home>/_state` | `[READ]` |
| Artifact root | `<home>/_artifacts` (`output_root()`) | `[READ]` |
| Process cwd | set to work target by the seam | `[READ]` |

This satisfies the blueprint's boundary requirement that **generated default
artifacts do not silently appear in the selected project** — disposable output
defaults to the toolkit home, not the target. `[READ]`

### 2.3 Path containment

`toolkit/tools/_toolkit.py::resolve_within_roots` resolves a caller-supplied
path against the work target and admits it only if it falls within the work
target **or** the toolkit home; anything else is refused with a reason. `[READ]`

This is the safety layer that all three external references (manifold-mcp,
TheDISMANTLER, MonacoVIEWER) were recorded as lacking entirely.

### 2.4 The precept guard

`invoke.py` implements a target-write guard that is stronger than anything the
blueprint asked for. `[READ]`

Before dispatching a tool whose declared authority is `Observe`, it builds an
mtime+size manifest of the work target; after dispatch it re-manifests and
**fails the call** if anything changed, naming the changed paths.

- Applies only when the target is distinct from the toolkit home.
- Skipped when a tool explicitly declares `writes: target`.
- Disabled by `SUITE_STRICT_OBSERVE=0`.
- Bounded at 20,000 files; above that it degrades to an honest "incomplete"
  rather than issuing a false verdict.

This directly implements the blueprint's invariant *"Toolkit calls cannot mutate
the target when manifest authority says Observe."*

Cost caveat: it walks and stats the entire target twice per Observe call.
On a large opened project this is a real latency cost the workbench must
account for in Tranche 6. `[INFERRED]`

**Verified behavior, and the caveat that matters most.** `[VERIFIED]`

A purpose-built fixture — a tool declaring `authority: Observe` and
`writes: none` that writes a file into the target — was run against a scratch
target in an isolated copy of the toolkit. The seam returned:

```
"ok": false,
"error": "precept violation: 'evil_probe' (writes=none) modified the target
          it may not write to: ['/tmp/victimYlEV/SNEAKY_WRITE.txt']"
```

It named the exact file. But `SNEAKY_WRITE.txt` **was on disk afterwards.**

**The guard is detection, not prevention.** The seam cannot sandbox a
subprocess, so the write lands and is then reported. `invoke.py`'s own comment
states this plainly.

Consequences the workbench must honour:

- A precept violation is a **damage event**, not merely a failed call. The
  workbench must surface it to the user as "this tool modified your project
  when it said it would not", not as a generic error.
- `SUITE_STRICT_OBSERVE=0` silently disables the guard entirely — verified: the
  same fixture returned `ok: true, error: None`. The bridge must therefore set
  `SUITE_STRICT_OBSERVE=1` **explicitly on every invocation** and never inherit
  it from the ambient environment, or the guarantee can be switched off by an
  unrelated setting.

---

## 3. Manifest Field Coverage

The blueprint (§10.1) requires 16 fields per callable capability. The toolkit
manifest supplies 9 of them directly. `[READ]`

| Blueprint field | Toolkit manifest | Bridge action |
| --- | --- | --- |
| `id` | `id` | pass through |
| `label` | — | synthesize from `id` |
| `category` | `category` | pass through |
| `description` | `summary` | pass through |
| `authority` | `authority` | map Observe/Sandbox/Apply → workbench ladder |
| `operates_on` | `operates_on` | pass through |
| `writes` | `writes` (mutators only) | default `none` when absent |
| `input_schema` | `input_schema` (JSON Schema) | pass through |
| `output_schema` | `output_shape` | pass through |
| `entrypoint` | `invocation.entry` | never exposed to UI |
| `execution_mode` | — | constant: `subprocess` |
| `supports_dry_run` | — | derive: `apply`/`write` in `input_schema` |
| `supports_cancel` | — | constant: `false` (see §4) |
| `supports_batch` | — | per-tool allowlist |
| `version` | — | from `toolkit/VERSION` |
| `provenance` | — | synthesized by the bridge |

The seven missing fields are synthesized by the `ToolkitBridge`, not added to
the toolkit. This keeps the toolkit unforked.

### 3.1 Preview-before-mutation already holds

`write_file`'s manifest defaults `write` to `false` and treats `apply: true` as
the execute flag `[READ]`. `_toolkit.py` provides shared `confirmed()` and
`apply_with()` helpers, and the toolkit's own documentation states every writing
tool previews first.

This aligns with blueprint §6.5. The workbench dispatcher must still enforce
dry-run/apply **itself** rather than trusting each tool, because the seam does
not enforce it — it is a per-tool convention. `[READ]`

---

## 4. Gaps the Toolkit Does Not Cover

These are the capabilities the workbench must own. They are the justification
for building a workbench operation framework at all rather than simply shelling
to the toolkit.

| Gap | Evidence | Owner |
| --- | --- | --- |
| **Cancellation** | `invoke.py` uses blocking `subprocess.run`; no cancel token, no process handle exposed `[READ]` | Workbench |
| **Progress streaming** | Output captured only on completion; no incremental channel `[READ]` | Workbench |
| **Per-call timeout** | `DEFAULT_TIMEOUT_S = 120` is module-level, not a parameter of `invoke()`. `[VERIFIED]` — fails cleanly at exactly 120 s with `"timeout after 120s"`, `exit_code: null`, no orphaned child. Correct behavior, but the limit is unconfigurable and too short for large snapshot compiles. | Workbench |
| **Dry-run/apply enforcement** | Convention per tool, not enforced at the seam `[READ]` | Workbench |
| **Target fingerprint / scan generation** | No concept of a stale plan `[READ]` | Workbench |
| **Inclusion sets** | No notion of a user-selected working set `[READ]` | Workbench |
| **Confirmation tokens** | `confirmed()` is a boolean arg, not a bound token `[READ]` | Workbench |
| **Client attribution** | Event log records tool/authority/duration, not calling surface `[INFERRED]` | Workbench |
| **Envelope unification** | Toolkit `{"ok": bool}` vs references' `{"status": ...}` | Workbench |
| **Structured error redaction** | Raw stderr returned; may carry absolute host paths `[READ]` | Workbench |

### 4.1 Recorded frailties in the toolkit seam

- `_resolve_project_root` **silently falls back** when `SUITE_PROJECT_ROOT` names
  a non-directory. `[VERIFIED]` — this is the most dangerous finding in the
  audit. Pointing the toolkit at a non-existent path returned `ok: true` and
  reported `root: /sessions/.../.useful-helpers-workbench`. **A typo in the
  target root causes the toolkit to silently operate on this repository
  instead**, and report success. The bridge must validate the root itself
  *before* launching, and assert that the root echoed in the result equals the
  root requested — treating any mismatch as a hard failure.
- `project_root()` in `_toolkit.py` falls back to `Path.cwd()` when the env var
  is unset. Any invocation path that bypasses the seam inherits the workbench's
  own cwd as the target. The bridge must always set roots explicitly. `[READ]`
- A tool producing no parseable JSON is treated as **success** with
  `{"raw_stdout": ...}` and `ok` defaulting to `True`. A silent tool "passes".
  The bridge must treat unparseable output as a failure. `[READ]`

---

## 5. The Dispatch Decision

Four independent sources converge on a single dispatch chokepoint:

| Source | Statement |
| --- | --- |
| `toolkit/src/core/invoke.py` | "the ONE chokepoint every tool call passes through" `[READ]` |
| MonacoVIEWER contract | session symmetry; neither client privileged |
| manifold-mcp contract | "Do not fork behavior between MCP and CLI paths" |
| TheDISMANTLER contract | "All UI-backend communication goes through `execute_task()`" |

**Decision.** The workbench owns one dispatcher. The toolkit seam becomes a
*backend transport* reached through `ToolkitBridge`, not a second dispatcher and
not a thing UI code touches. Workbench-native tools and bridged toolkit tools
are indistinguishable to callers above the dispatcher.

**Envelope decision.** The workbench normalizes to its own `OperationResult`
(blueprint §10.3) at the bridge boundary. The toolkit's `{"ok": bool}` shape is
preserved unmodified inside the toolkit; translation happens once, in the
bridge. Neither envelope is adopted wholesale — which the manifold-mcp contract
correctly identified as a regression either way.

---

## 6. Capability Ownership by Contract Family

Ownership vocabulary:

- **Bridge** — call the toolkit through `ToolkitBridge`; write no new backend.
- **Wrap** — toolkit provides the primitive; workbench owns orchestration.
- **Own** — workbench implements it; toolkit has no adequate equivalent.
- **Defer** — not in scope until a later tranche decides.

| # | Family | Candidate toolkit tools | Owner | Rationale |
| --- | --- | --- | --- | --- |
| 01 | Project Mapper | `file_tree`, `report`, `codebase_bundle`, `attach`, `sqlite_inspect`, `sqlite_exec`, `snapshot_diff`, `snapshot_verify` | **Wrap** | Tree/report primitives exist. The SQLite snapshot schema, inclusion-set semantics, and projection exports are workbench-specific and must be owned. |
| 02 | Tokenizing Patcher | `patch`, `edit`, `diff` | **Wrap** | Toolkit `edit` offers literal matching and `expected_replacements`. Hunk validation, ambiguity/overlap detection, and multi-file preflight are the contract's real substance and are not present. |
| 03 | Line Numberizer | `linenumber`, `symbol_graph` | **Bridge** then **Wrap** | Annotate/strip likely maps to `linenumber`. AST tree/flat/semantic-block exports need confirmation against the toolkit's code-intel tools. |
| 04 | Git Pusher | `git`, `git_inspect` | **Wrap** | Toolkit supplies command execution and inspection. The safety contract — explicit staging, pull-failure-stops-push, confirmation gates — is workbench policy and must not live in a tool. |
| 05 | UiMAPPER | `tkinter_widget_tree`, `ui_callback_graph`, `import_graph`, `symbol_graph`, `complexity_score` | **Bridge** | Strongest overlap in the whole matrix. Four named tools map almost directly. Presumption: no new backend. |
| 06 | TextTOUCHER | `write_file`, `fs_op` | **Bridge** | `write_file` is preview-first, containment-checked, `writes: target`, Apply authority. It already satisfies most of the contract. Workbench owns only filename validation and target preview UX. |
| 07 | ChatWindowKERNAL | `session_record`, `session_replay`, `operation`, `event_log`, `delegate`, `ollama_gov` | **Defer** | Tranche 12. Optional by blueprint §6.6. |
| 08 | TheCELL | `workflow_decompose`, `workflow_templates`, `journal`, `evidence`, `rag_retrieve` | **Defer** | Tranche 12. Lifecycle must be forward-only; recursion prohibited. |
| 09 | WASM Inference Wrapper | `app_factory`, `scaffold_project`, `dep_install`, `dev_server_manager`, `tempserver` | **Defer** | Tranche 14. Blocked on the honesty decision: real WASM boundary, or rename to local model-node packager. |
| 10 | MonacoVIEWER | — | **Own** | Blueprint and contract both record it as largely unique. Separate process plus session service. No toolkit equivalent. |
| 11 | manifold-mcp | `semantic_chunk`, `bd_*` family, `evidence`, `rag_retrieve` | **Wrap** | The `bd_*` tools appear to be a graph/evidence substrate. Reversible verbatim reconstruction and evidence bags need verification against them. |
| 12 | TheDISMANTLER | `symbol_graph`, `module_decomp_plan`, `dead_code`, `domain_boundary_audit`, `complexity_score`, `patch` | **Bridge** | Contract explicitly says do not port wholesale. Its architectural lesson is already absorbed into §5. |

### 6.1 Capabilities with no toolkit equivalent — workbench-owned

- Explorer browse-selection and operation-inclusion state (blueprint §9.2–9.3).
- Scan generation and project fingerprint; stale-plan revalidation.
- The operation request/result/event contracts (§10.2–10.3).
- Authority ladder `Observe / Prepare / Apply / External` — note this is a
  **four**-level ladder, whereas the toolkit uses three
  (`Observe / Sandbox / Apply`). The mapping is defined in `ARCHITECTURE.md`.
- Background task queue, cancellation, progress.
- Confirmation tokens bound to a specific plan and fingerprint.
- Monaco shared session service.
- The GUI itself.

---

## 7. Mandatory Safety Gate Before Tranche 6 — EXECUTED

**Status: run on 2026-08-05. Results in §1.1; evidence in journal 0002.**

Six of seven passed. Check 5 failed and produced the audit's most important
finding. The gate no longer blocks Tranche 6; the §4.1 mitigations do.

The checks, retained as the standing regression suite for the bridge:

1. `python -m src.app cli tool-list` runs and the manifest count is confirmed.
2. A tool invoked with `SUITE_PROJECT_ROOT` pointed at a scratch directory
   reports that directory as its root — confirming the override works.
3. An `Observe` tool run against a scratch target leaves it byte-identical.
4. A deliberate precept violation is confirmed to fail the call.
5. Behavior is confirmed when `SUITE_PROJECT_ROOT` names a non-existent path.
6. Timeout behavior is confirmed on a tool exceeding 120 s.
7. `SUITE_STATE_ROOT` and `SUITE_HOME` overrides are confirmed to redirect
   state and artifacts away from both the workbench and the target.

Until then, every claim in sections 2–4 remains provisional.

---

## 8. Open Questions

- Does the toolkit's `linenumber` tool cover annotate **and** strip, or only
  annotate? `[UNKNOWN]`
- Do the `bd_*` tools provide verbatim reconstruction, or only chunk-level
  retrieval? `[UNKNOWN]`
- Is `attach` safe to call against an arbitrary user-opened project, given it
  writes a project map into toolkit state? `[UNKNOWN]`
- Does any shipped `Observe` tool declare `writes: target` and thereby opt out
  of the precept guard? `[UNKNOWN]`
- What is the real cost of the precept guard on a 10,000-file project?
  `[UNKNOWN]`
