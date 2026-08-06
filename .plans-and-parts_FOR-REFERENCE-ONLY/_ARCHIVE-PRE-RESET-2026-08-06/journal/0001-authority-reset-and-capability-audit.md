# 0001 — Authority Reset and Capability Audit

- **Date:** 2026-08-05
- **Tranches:** 0 (Establish Current Authority) and 1 (Capability and
  Command-Surface Audit)
- **Status:** Parked, complete, with a recorded verification gap
- **Agent:** first implementing agent

This is the first entry in this project's journal. It begins at `0001`. No
predecessor journal has been copied into this history.

---

## 1. Tranche Declaration

**Goal.** Convert a copied sandbox into a truthful project starting point, then
decide how the twelve inherited plans and the existing toolkit relate — without
writing any application code.

**Scope.** Contract installation; active control documents; ignore rules;
enumeration of twelve tool contracts and 99 toolkit manifests; audit of toolkit
root resolution, invocation, and result envelope; drafted workbench operation
contracts; the capability matrix.

**Declared non-goals, all honoured.** No application code. No source migration.
No GUI scaffold. No tool implementation. No broad source copying. No mutation
tool implementation.

---

## 2. What Was Inspected

- `.bcc/BUILDER-CONSTRAINT-CONTRACT.md` — entry anchors and the required
  tranche loop.
- The governing blueprint, *Useful Helpers Workbench — Clean-Room
  Implementation Blueprint and Agent Instruction*.
- All twelve `*_TOOL_CONTRACT.md` files under
  `.plans-and-parts_FOR-REFERENCE-ONLY/_PLANS/`.
- `toolkit/AGENTS.md`, `toolkit/README.md`.
- `toolkit/src/core/config.py`, `invoke.py`, `policy.py`.
- `toolkit/tools/_toolkit.py`.
- Representative manifests: `file_tree/tool.json`, `write_file/tool.json`.
- The 99 `toolkit/tools/*/tool.json` manifest paths.
- Top-level zone inventory of the repository root.

---

## 3. What Changed and Why

| File | Change | Why |
| --- | --- | --- |
| `.bcc/BUILDER-CONSTRAINT-CONTRACT.md` | Resolved all four `{{BCC_...}}` placeholders; added installed-configuration notes | The contract was a seed, not an installed local contract. Until resolved it had no configured authority over this root. |
| `.bcc/CURRENT_STATE.md` | Created | A resuming agent must be able to determine real current state without reading predecessor journals. |
| `.bcc/PROJECT_PLAN.md` | Created | Establishes this project's own tranche numbering, replacing inherited identifiers. |
| `.bcc/ARCHITECTURE.md` | Created | Records structural intent and the drafted operation contracts. |
| `.bcc/CAPABILITY_MATRIX.md` | Created | Answers the central architectural question that governs the rest of the project. |
| `.bcc/SOURCE_PROVENANCE.md` | Created | Separates inheritance from current implementation. |
| `.bcc/TESTING.md` | Created | Defines conventions and records that no test exists. |
| `_docs/AppJOURNAL/0001-*.md` | Created | This entry. |
| `.gitignore` | Replaced | See §4. |

### 3.1 Configuration installed

```
TARGET_PROJECT_ROOT = "."
SIDECAR_ROOT        = ".bcc"
CONTRACT_PATH       = ".bcc/BUILDER-CONSTRAINT-CONTRACT.md"
JOURNAL_PATH        = "_docs/AppJOURNAL"
```

Values are project-root-relative so the project stays portable.

**Deviation from the blueprint scaffold, authorized by the operator.** The
blueprint places the journal at `.bcc/_AppJOURNAL/`. The operator directed it to
`_docs/AppJOURNAL`. The BCC bootstrap rule permits `_docs/` when the user
explicitly chooses it, and the operator did. Recorded so it is not later read as
drift.

Consequence: `_docs/` is now a builder-control zone. It is non-runtime and
removable. A future product-facing documentation zone is `docs/`, without the
underscore. `TESTING.md` §4.4 carries a boundary assertion for both.

---

## 4. Cleanup Performed

The repository root carried a copy of the **toolkit's own** `.gitignore`. Its
own text described it as ignoring "ONLY the toolkit's own output" and it was
written from the toolkit's perspective — including `config/registry.json`, which
at root would have wrongly ignored a future workbench `config/`.

Replaced with a root-appropriate file preserving the effective ignores and
adding workbench state, artifact, harness-output, log, and crash-record rules.
`toolkit/.gitignore` was **not** touched; the toolkit keeps its own.

No other file was deleted or modified. No reference material was altered.

---

## 5. Principal Findings

### 5.1 The blueprint's central worry is real, and already solved

The blueprint (§11.2) requires resolving toolkit root behavior before any
integration, warning the toolkit treats its parent as the target.

Confirmed by reading `toolkit/src/core/config.py`: `toolkit/.suite_sidecar`
exists, so **with no override the toolkit currently targets this repository
itself.**

Also confirmed: the override already exists. `SUITE_PROJECT_ROOT` is honoured
first, and `invoke.py` exports it plus `SUITE_HOME` and sets `cwd` to the target
on every dispatch.

**Decision: no toolkit fork is required.** The bridge binds roots per
invocation. It must never mutate the workbench process environment to do so.

### 5.2 The toolkit is stronger than the blueprint assumed

`invoke.py` implements a **precept guard**: before an `Observe` tool runs it
manifests the target by mtime and size, re-manifests afterwards, and fails the
call if anything changed. Bounded at 20,000 files, degrading to an honest
"incomplete" rather than a false verdict.

This directly implements the blueprint invariant *"Toolkit calls cannot mutate
the target when manifest authority says Observe"* — in the instrument, before
the workbench exists.

`_toolkit.py::resolve_within_roots` confines every path to the work target or
the toolkit home. `output_root()` defaults disposable artifacts to the toolkit
home, satisfying *"generated default artifacts do not silently appear in the
selected project."*

### 5.3 Four independent sources agree on one dispatcher

`invoke.py`'s own docstring, the MonacoVIEWER contract, the manifold-mcp
contract, and TheDISMANTLER contract each independently state the single-dispatch
rule. That settles it: the workbench owns one dispatcher and the toolkit seam
becomes a backend transport behind `ToolkitBridge`.

### 5.4 Real gaps the workbench must own

Cancellation, progress streaming, per-call timeout, dry-run/apply enforcement,
target fingerprinting, inclusion sets, confirmation tokens, client attribution,
envelope normalization, and diagnostic redaction. `invoke.py` uses a blocking
`subprocess.run` with a module-level 120 s timeout and no cancel path.

### 5.5 Recorded toolkit frailties

- Invalid `SUITE_PROJECT_ROOT` fails **silently** back to the sidecar parent.
- `project_root()` falls back to `Path.cwd()` when the env var is unset.
- A tool emitting unparseable output is treated as **success**.

Each has a named mitigation in `ARCHITECTURE.md` §10.

### 5.6 Dated evidence

Two inherited contracts state the toolkit has 91 tools. It now has 99.
Contract-era descriptions of the toolkit are dated and must be re-verified.

---

## 6. Verification

**No command was executed. No test was run.**

The isolated Linux environment failed to start on four attempts across this
session — at onboarding, after tranche planning, mid-tranche, and at the closing
verification step — reporting "VM service not running" each time. No Windows
shell was available. The operator's chosen approach was to retry the sandbox; it
did not recover.

Every behavioral claim about the toolkit in this entry and in
`CAPABILITY_MATRIX.md` is therefore **provisional under BCC 2.7**, derived from
reading source. Claims are tagged `[READ]`, `[INFERRED]`, or `[UNKNOWN]` in the
matrix.

Checks that **were** possible, and their results:

| Check | Method | Result |
| --- | --- | --- |
| No BCC placeholders remain | Pattern search for `\{\{BCC_[A-Z0-9_]+\}\}` in the contract | Pass — no matches |
| No workbench runtime exists | Glob `src/*` | Pass — no files found |
| Toolkit manifest count | Glob `toolkit/tools/**/tool.json` | 99 |
| Toolkit is sidecar-configured | Glob for `toolkit/.suite_sidecar` | Present |
| Reference zones present and unmodified | Glob of each zone | Confirmed |

This is inspection evidence, not execution evidence. It is not represented as
verification of toolkit behavior.

---

## 7. Unresolved Risks

| Risk | Severity | Disposition |
| --- | --- | --- |
| All toolkit findings unexecuted | High | Mandatory safety gate before Tranche 6 |
| Toolkit currently targets this repository by default | High | Bridge binds roots explicitly |
| Silent fallback on invalid target root | High | Bridge validates and verifies the echoed root |
| No cancellation or progress in the seam | High | Workbench owns the task queue; may need a launcher that bypasses `invoke()` while preserving its guarantees |
| 120 s timeout may be too short for snapshot compiles | Medium | Tranche 5 |
| Unparseable output treated as success | Medium | Bridge treats as failure |
| Precept-guard cost on large targets unmeasured | Medium | Measure before Tranche 6 |
| stderr may leak absolute host paths | Medium | Redact at the bridge |

Open questions are listed in `CAPABILITY_MATRIX.md` §8.

---

## 8. Park Point

**Completed.** Tranche 0 and Tranche 1, to their declared stopping points.

**Deliberately not done.** Any application code, GUI scaffold, tool
implementation, or source migration — all declared non-goals of both tranches
and of the blueprint's first agent instruction.

**Next action.** Tranche 2 — Minimal Runtime Scaffold. Create `src/app.py`, the
package structure, logging, path and configuration providers, state-root
resolution, a `--status` smoke mode, test configuration, run and setup scripts,
and a root README.

Tranche 2 does **not** require the toolkit safety gate. The gate blocks Tranche
6 only.

**Note for the next agent.** Tranche 2 is the first tranche that produces
executable code. Do not declare it complete on inspection alone. If no shell is
available, the honest outcome is a scaffold written but **unverified**, recorded
as such — not a passing status claim.
