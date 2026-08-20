# Parity Matrix — Donor Useful-Product Census

- **Date:** 2026-08-20
- **Closure gate:** 1 of 2 (parity), after T8 parked at `445a68c`, before release certification.
- **Stage:** **CENSUS ONLY.** No row has been executed. No donor repaired, no workbench
  redesigned, no architecture added.

---

## How to read this

A row is a **useful product** — an externally useful output or workflow the predecessor
existed to provide. Not a function, not a class, not a UI feature. "It had a Tools menu"
is not a row; "it produces a SQLite snapshot of a project" is.

**Final dispositions are only three.** No row may remain unresolved at closure:

| | meaning |
| --- | --- |
| **Retained — direct** | produced today by one tool |
| **Retained — composed** | produced by a chain through the existing runtime |
| **Superseded** | the old product deliberately no longer exists, because a current capability replaces its useful outcome |

`PROPOSED` in the disposition column means *this census's reading*, not a decision. A
proposed row becomes final only when its fixture has been executed through the current
governed runtime (stage 2) and re-run with the parts bin absent (stage 3).

**Product parity, not UI parity, not code parity, not internal-architecture parity.**

---

## Three donors were reviewed as prior art, not as products

`_manifold-mcp`, `_TheDISMANTLER` and (in part) `_MonacoVIEWER` were taken into Root
Tranche 15 for the **rules** they demonstrated, and their contracts say so in their own
words: *"the only reference in the parts bin that solves the problem Root Tranche 15
exists to solve"*, *"GUI-side dispatch prior art … that is the workbench's problem, in the
workbench's toolkit."*

Their primary contribution is therefore **Superseded by construction** — the seam *is* the
adopted rule, and T8 certified it end to end over both entrances. Each still carries a
**secondary capability** that is a real product row and is censused separately below.

Recording this distinction matters: counting prior art as an unmet product row would
manufacture parity debt for architecture that has already shipped and been certified.

---

## The matrix

### 01 — `_ProjectMAPPER`

| # | Useful product | Fixture | Candidate capability | Proposed |
| --- | --- | --- | --- | --- |
| 1.1 | SQLite project snapshot of a selected working set | any project dir | `projectmapper` | Retained — direct |
| 1.2 | Project tree markdown | ” | `projectmapper` | Retained — direct |
| 1.3 | Filedump markdown | ” | `projectmapper` | Retained — direct |
| 1.4 | Combined tree + filedump markdown | ” | `projectmapper` | Retained — direct |
| 1.5 | Snapshot manifest markdown | ” | `projectmapper` | Retained — direct |
| 1.6 | Exclusion management preserved in the artifact | ” | `projectmapper` | **OPEN** — see note |

> **Note on 1.6.** Two ProjectMapper parity findings are parked by operator ruling and
> **stay parked until this row is actually certified**: the manifest does not preserve
> user `exclude_paths` / `out` / `markdown`, and dot-directories are pruned
> unconditionally. Row 1.6 is where they come due — not before.

### 02 — `_TokenizingPATCHER`

| # | Useful product | Fixture | Candidate capability | Proposed |
| --- | --- | --- | --- | --- |
| 2.1 | Validate a JSON hunk patch before writing | file + hunk JSON | `patch` (`action: validate`) | Retained — direct |
| 2.2 | Preview a patch as a diff | ” | `patch` preview → `diff` | Retained — composed |
| 2.3 | Apply a single-file patch preserving indentation intent | ” | `patch` (`force_indent`) | Retained — direct |
| 2.4 | Detect missing / ambiguous / overlapping hunks before writes | crafted ambiguous patch | `patch` | Retained — direct *(behaviour unverified)* |
| 2.5 | **Multi-file patch batch** | several files, one patch set | **`patch` takes ONE `path`** — read from `tool.json`, not assumed | **OPEN** — composed chain, or a real gap |

### 03 — `_LineNUMBERIZER`

| # | Useful product | Fixture | Candidate capability | Proposed |
| --- | --- | --- | --- | --- |
| 3.1 | Annotate text with parseable line numbers | any text file | `linenumber` (`annotate`) | Retained — direct |
| 3.2 | Strip line numbers, preserving content | annotated file | `linenumber` (`strip`) | Retained — direct |
| 3.3 | Line → hash integrity map | any text file | `linenumber` (`map`) | Retained — direct |
| 3.4 | **Python AST tree / flat JSON export** | a `.py` file | `symbol_graph` is a *resolved reference graph*, **not** an AST projection | **OPEN** — likely a gap |
| 3.5 | Python semantic blocks export | a `.py` file | `semantic_chunk` | Retained — direct *(shape unverified)* |

### 04 — `_GitPUSHER`

| # | Useful product | Fixture | Candidate capability | Proposed |
| --- | --- | --- | --- | --- |
| 4.1 | Inspect repository state (branch / status / remote) | a git repo | `git_inspect` | Retained — direct |
| 4.2 | Stage an explicit approved working set, then commit | ” | `git` (`add` → `commit`) | Retained — direct |
| 4.3 | Push commits | ” | `git` (`push`) | Retained — direct |
| 4.4 | Safety gate before mutating operations | repo without `.gitignore` | `git` (`allow_no_gitignore`) | Retained — direct |
| 4.5 | Record stdout / stderr / exit code for every git command | ” | seam envelope + `event_log` | Retained — composed |
| 4.6 | **Pull before push** | ” | no `pull` action in `git/tool.json` | **OPEN** |
| 4.7 | **Branch management with dirty-state checks** | ” | no branch action in `git/tool.json` | **OPEN** |

### 05 — `_UiMAPPER`

| # | Useful product | Fixture | Candidate capability | Proposed |
| --- | --- | --- | --- | --- |
| 5.1 | Map a Tkinter UI surface (windows, widgets, layout, bindings, menus) | a Tk project | `tkinter_widget_tree` | Retained — direct |
| 5.2 | Callback graph from UI events to handlers | ” | `ui_callback_graph` | Retained — direct |
| 5.3 | Serialized report artifacts (markdown / json) | ” | `report` | Retained — composed |
| 5.4 | Honour exclusions and gitignore during the scan | ” | shared PRUNE authority | Retained — direct |
| 5.5 | Collect unknown / unresolved cases honestly | ” | *unverified* | **OPEN** |

### 06 — `_TextTOUCHER`

| # | Useful product | Fixture | Candidate capability | Proposed |
| --- | --- | --- | --- | --- |
| 6.1 | Create a UTF-8 text file in an approved folder | a target dir | `write_file` | Retained — direct |
| 6.2 | Preview exact target path and overwrite decision before writing | ” | `write_file` (preview-first, `overwrite`) | Retained — direct |
| 6.3 | Prevent writes outside the approved root | traversal attempt | roots containment (`resolve_within_roots`) | Retained — direct |
| 6.4 | Timestamp-suffixed filenames | ” | `stamp` | Retained — composed *(unverified)* |

### 07 — `_ChatWindowKERNAL`

| # | Useful product | Fixture | Candidate capability | Proposed |
| --- | --- | --- | --- | --- |
| 7.1 | A conversational agent host that can drive the toolkit | an agent client | **MCP entrance** — certified in T8 over the real stdio server | **Superseded** |
| 7.2 | Session persistence and replay | a session | `session_record`, `session_replay` | Retained — direct |
| 7.3 | Background work without blocking the UI | long task | seam job/cancellation (T4) | Superseded |
| 7.4 | Structured logging and crash reports | ” | `logging_setup`, `event_log` | Retained — composed |
| 7.5 | **The chat GUI workspace itself** | — | — | **Superseded — operator confirmation wanted** |

> 7.5 is a *product-shape* question, not a capability question. `SIDECAR:PRODUCT-SHAPE`
> says `mechanical tools → governed tool chains → common runtime/seam → human + agent`,
> **not** `tools → specialised applications`. A chat GUI is a specialised application.
> Recorded as Superseded, flagged because retiring a user-visible surface is the
> operator's call, not a census's.

### 08 — `_theCELL`

| # | Useful product | Fixture | Candidate capability | Proposed |
| --- | --- | --- | --- | --- |
| 8.1 | Bootstrap a workspace bound to one target | empty dir | installer + instance identity (T6) | **Superseded** |
| 8.2 | Identity and state that survive restart | ” | `instance.json`, `_state` | Superseded |
| 8.3 | Run a streamed agent step | a prompt | `delegate` | Retained — direct |
| 8.4 | Execute a declared task queue | a task list | `plan`, `operation`, playbooks | Retained — composed |
| 8.5 | Ingest context for retrieval | a corpus | `rag_retrieve`, `semantic_chunk` | Retained — composed |
| 8.6 | Capture outputs, feedback and exports as evidence | a run | `evidence`, `provenance` | Retained — composed |
| 8.7 | Personas / prompts / templates | ” | `prompt_*` family, `workflow_templates` | Retained — composed *(unverified)* |
| 8.8 | Forward-only lifecycle enforcement | ” | *unverified* | **OPEN** |

> `_theCELL` is simultaneously the **C4-A acceptance target**. Its parity rows and its
> acceptance role are separate obligations and must not be allowed to satisfy each other.

### 09 — `_WasmInferenceWRAPPER`

| # | Useful product | Fixture | Candidate capability | Proposed |
| --- | --- | --- | --- | --- |
| 9.1 | Scaffold a local agent runtime with a manifest | target dir | `scaffold_project`, `app_factory` | Retained — composed |
| 9.2 | Preview all generated files / downloads / installs before acting | ” | preview-first seam convention | Retained — direct |
| 9.3 | Gate model downloads and dependency installs behind confirmation | ” | `dep_install` (Apply), `ollama_gov` | Retained — composed |
| 9.4 | A tested prompt request/response contract | a prompt case | `prompt_eval`, `prompt_case_builder` | Retained — composed |
| 9.5 | **A true WASM runtime boundary** | — | — | **Superseded** — the contract records the reference *never produced one*; it made a Python FastAPI node. There is no useful product here to retain |

### 10 — `_MonacoVIEWER`

| # | Useful product | Fixture | Candidate capability | Proposed |
| --- | --- | --- | --- | --- |
| 10.1 | Human and agent operating on the same file state, each seeing the other's change | a file | **T8's governed loop** — `read_file` → preview → `diff` → witness-bound Apply → measured change → refreshed awareness | **Superseded** |
| 10.2 | Range-precise edits applied to a live buffer | ” | `edit`, `patch` | Retained — direct |
| 10.3 | Headless text operations | ” | `edit`, `write_file`, `read_file` | Retained — direct |
| 10.4 | Gated save | ” | preview-first + `apply:true` + source witness | Superseded |
| 10.5 | **The Monaco editor GUI and vendored assets** | — | — | **Superseded — operator confirmation wanted** (specialised application) |

### 11 — `_manifold-mcp`

| # | Useful product | Fixture | Candidate capability | Proposed |
| --- | --- | --- | --- | --- |
| 11.1 | One tool entry point callable identically from CLI and agent | any tool | the seam; **certified in T8 over both entrances** | **Superseded — prior art adopted** |
| 11.2 | Reversible ingest of text into a corpus with exact evidence spans | text + files | `bd_index`, `semantic_chunk`, `evidence` | Retained — composed |
| 11.3 | Query a corpus returning an evidence bag with provenance | a query | `bd_query`, `rag_retrieve`, `provenance` | Retained — composed |
| 11.4 | **Verbatim reconstruction of source text from an evidence bag** | ” | *unverified — this is the row that proves reversibility* | **OPEN** |
| 11.5 | Path containment on every file read and store write | traversal attempt | roots containment — *the contract notes the reference did NOT do this* | Retained — direct |

### 12 — `_TheDISMANTLER`

| # | Useful product | Fixture | Candidate capability | Proposed |
| --- | --- | --- | --- | --- |
| 12.1 | One dispatch chokepoint for GUI, agent and automation | any tool | `invoke` | **Superseded — prior art adopted** |
| 12.2 | Machine-readable declared input schema per tool | any tool | `tool.json` `input_schema` | Superseded |
| 12.3 | Stable routing identity, not a display name | any tool | `tool.json` `id` | Superseded |
| 12.4 | Authority-enforced dispatch | an Apply tool | `policy.decide`, precept guard | Superseded |
| 12.5 | Dispatch provenance | any call | `event_log` (**with `client`, since T8**) | Superseded |
| 12.6 | Monolith decomposition plan for a large file | a large module | `module_decomp_plan`, `complexity_score`, `import_graph` | Retained — composed |
| 12.7 | Safe tool loading without executing arbitrary drop-in code | a planted tool | *unverified* | **OPEN** |

---

## Census summary

**67 rows.** Counted from the tables above by script, not by hand — my first pass at this
summary said 25 / 17 / 14 / 10 and disagreed with its own matrix. A summary that
contradicts the thing it summarises is worse than no summary.

| disposition | rows |
| --- | --- |
| Retained — direct (proposed) | 28 |
| Retained — composed (proposed) | 15 |
| Superseded (proposed) | 15 |
| **OPEN — must resolve before closure** | **9** |

### The ten open rows

| row | question |
| --- | --- |
| 1.6 | does the snapshot preserve its own exclusion selection? *(the two parked ProjectMapper findings)* |
| 2.5 | multi-file patch batch — composed chain, or a gap? |
| 3.4 | Python AST tree / flat JSON export — `symbol_graph` is a different artifact |
| 4.6 | `git pull` |
| 4.7 | branch management with dirty-state checks |
| 5.5 | honest collection of unknown/unresolved cases |
| 8.8 | forward-only lifecycle enforcement |
| 11.4 | verbatim reconstruction from an evidence bag |
| 12.7 | safe tool loading without executing drop-in code |



Rows **7.5** and **10.5** are proposed *Superseded* rather than OPEN, because the census
does have an answer for them — but both retire a **user-visible surface**, which is an
operator decision and not a census's. They are flagged here so the ruling is deliberate.

**None of these is a licence to build.** Each resolves to one of the three dispositions:
the capability exists (execute the fixture and prove it), a chain produces it (compose and
prove it), or the product is deliberately gone (say so, and say what replaces its useful
outcome).

---

## Three assumptions this census had to correct by reading

Recorded because the alternative was a matrix of plausible-looking rows:

- **`patch` takes one `path`.** I had it down as multi-file capable. Row 2.5 is open
  because `tool.json` says so.
- **`symbol_graph` is a resolved reference graph, not an AST projection.** It answers
  *who refers to whom*, bound through imports — not *what is the syntax tree*. Row 3.4 is
  a likely gap, not a match.
- **`git` has no `pull` and no branch action.** Rows 4.6 and 4.7 exist because I looked
  instead of assuming a "git tool" covers git.

---

## Stages remaining

1. **Resolve the ten open rows** to one of the three dispositions, from evidence.
2. **Execute every retained row** through the current governed runtime, asserting the
   documented useful output on its fixture.
3. **Re-run with the parts bin / reference corpus unavailable**, proving no runtime or
   reference dependency survives.

Then: release certification from a clean clone on a clean machine → **STOP**.
