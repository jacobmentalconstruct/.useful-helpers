# Parity Matrix — Donor Useful-Product Census, **Resolved**

- **Date:** 2026-08-20
- **Closure gate:** 1 of 2 (parity), after T8 parked at `445a68c`, before release certification.
- **Stage:** **CENSUS RESOLVED.** Every row carries a disposition. No implementation work
  has been done. No donor repaired, no workbench redesigned, no architecture added.

---

## How to read this

A row is a **useful product** — an externally useful output or workflow the predecessor
existed to provide. Not a function, not a class, not a UI feature.

| disposition | meaning |
| --- | --- |
| **Retained — direct** | produced today by one tool |
| **Retained — composed** | produced by a chain through the existing runtime |
| **Superseded** | the old product deliberately no longer exists, because a current capability replaces its useful outcome |
| **Retained — FAILING** | the useful outcome is still owed and **has no present implementation, direct or composed** |

**`FAILING` is not `Superseded`.** A product is only Superseded when something deliberately
replaces its useful outcome. Missing is not replaced. The failing rows are the **only
permitted implementation work** in parity.

**Product parity, not UI parity, not code parity, not internal-architecture parity.**

---

## Operator ruling, 2026-08-20 — rows 7.5 and 10.5

**7.5 Chat GUI — Superseded. 10.5 Monaco GUI — Superseded.**

The ruling applies to the **specialised application/UI surfaces themselves**, not to useful
behaviours merely exposed through them. `SIDECAR:PRODUCT-SHAPE` supersedes specialised
applications in favour of primitive tools, governed compositions, shared state and
human/agent projections, and the architectural STOP condition requires that the acceptance
walk not depend on specialised application layers.

### Confirmation: every underlying useful behaviour is carried by another row

Each contract capability was checked individually. Nothing is inherited by assertion.

| `_ChatWindowKERNAL` capability | carried by |
| --- | --- |
| Bootstrap host kernel; compose chat/workspace shell; chat layout; input controls | *UI surface only* — superseded with 7.5 |
| Render conversational messages (user/assistant/tool/error/HITL) | *UI rendering* — superseded with 7.5 |
| Manage sessions, models, loops | **7.2** (`session_record`/`session_replay`), `delegate`, `ollama_gov` |
| Host agent turns and HITL approval gates | **7.1** (MCP entrance) + T8's preview → diff → witness-bound Apply |
| run / pause / stop / resume agent work | **`operation`** — verified: it has `pause`/`resume`; `invoke.cancel` covers stop |
| Discover and run tool packages, track execution history | **12.1–12.5** (registry + `invoke` + `event_log`) |
| Queue background tasks off the UI thread | **7.3** (T4 job/cancellation) |
| Persist state and runtime snapshots | **7.2**, `workspace_audit` |
| Structured logging and crash reports | **7.4** — see note below |
| Optional Mindshard adapter seam | `delegate` |

| `_MonacoVIEWER` capability | carried by |
| --- | --- |
| `session_process_lifecycle`, `tab_management`, `vendored_monaco_assets` | *UI surface only* — superseded with 10.5 |
| `session_state_inspection` (cursor, selection, dirty flags) | *editor-internal state* — superseded with 10.5 |
| `session_event_stream` — every client observes every mutation | **`src/core/watch.py`** — an opaque cursor plus what has happened since, for *"any client wanting to observe the other party"*. Certified by the T3 gate |
| `ranged_edit_application` | **10.2** (`edit`, `patch`) |
| `gated_buffer_save` | **10.4** (preview-first + `apply:true` + source witness) |
| `headless_text_operations` | **10.3** |
| `shared_session_provenance` | **10.1** (T7 shared awareness + `event_log`) |

> **On "crash reports".** No dedicated crash-report file is produced. The useful outcome —
> *a failure leaves a diagnosable record after the fact* — is served by `event_log`
> (error + exit_code + client) and structured logging. Recorded as covered by 7.4 rather
> than invented as debt: a debugging affordance of a superseded application is not a
> useful product of its own.

**No unique useful behaviour was found living only inside either GUI.** Both surfaces are
Superseded with no residual parity debt.

---

## The failing retained rows — the only permitted implementation work

| row | owed useful outcome | evidence it is not implemented |
| --- | --- | --- |
| **1.6** | a snapshot records the selection that produced it, so its capture scope is reproducible | manifest omits user `exclude_paths` / `out` / `markdown`; dot-directories pruned unconditionally *(verified 2026-08-19 against a real snapshot)* |
| **2.5** | apply one patch set across many files as one governed operation | `patch` accepts a single `path`; **playbooks are a fixed list of steps with literal args and have no iteration construct** |
| **4.2** | stage and commit **only an explicit approved working set** | `tools/git/cli.py` hardcodes `git add .`; `tool.json` exposes no path selection |
| **4.6** | pull before push, so a push cannot clobber | actions are `init｜status｜commit｜sync`. No `pull` |
| **4.7** | branch management with dirty-state checks | no branch action of any kind |
| **6.4** | a uniquely named file is created rather than refused | `stamp` generates **tool skeletons**, not filename timestamps. `write_file overwrite:false` *refuses* instead of uniquifying — a different outcome |

**Row 4.2 was proposed `Retained — direct` in the first census and is wrong.** Reading
`cli.py` rather than the summary line showed `add .` — it stages everything. The donor's
contract is explicit: *"stage and commit only an explicit user-approved working set."*
Staging the whole tree is not that product, and for a tool whose entire purpose is a
careful commit, the difference is the product.

**Row 6.4 is minor and flagged as such.** The anti-clobber *intent* is served by
`overwrite:false`. If the operator judges auto-uniquification a UI affordance rather than a
useful product, it is a legitimate `Superseded` — but the census will not rule it so merely
because it is absent.

---

## The matrix

### 01 — `_ProjectMAPPER`

| # | Useful product | Fixture | Capability | Disposition |
| --- | --- | --- | --- | --- |
| 1.1 | SQLite project snapshot of a selected working set | any project dir | `projectmapper` | Retained — direct |
| 1.2 | Project tree markdown | ” | `projectmapper` | Retained — direct |
| 1.3 | Filedump markdown | ” | `projectmapper` | Retained — direct |
| 1.4 | Combined tree + filedump markdown | ” | `projectmapper` | Retained — direct |
| 1.5 | Snapshot manifest markdown | ” | `projectmapper` | Retained — direct |
| 1.6 | Artifact preserves its own capture selection | ” | — | **Retained — FAILING** |

> ProjectMapper source was **not touched**. Row 1.6 is adjudicated from the finding
> recorded on 2026-08-19; repair happens when the row is proved, not now.

### 02 — `_TokenizingPATCHER`

| # | Useful product | Fixture | Capability | Disposition |
| --- | --- | --- | --- | --- |
| 2.1 | Validate a JSON hunk patch before writing | file + hunk JSON | `patch` (`validate`) | Retained — direct |
| 2.2 | Preview a patch as a diff | ” | `patch` preview → `diff` | Retained — composed |
| 2.3 | Apply a single-file patch preserving indentation intent | ” | `patch` (`force_indent`) | Retained — direct |
| 2.4 | Detect missing / ambiguous / overlapping hunks before writes | duplicated line | `patch` — **run:** `"Ambiguous match (2 found)"`, `"Search block not found."` | Retained — direct ✔ |
| 2.5 | Multi-file patch batch | several files | — | **Retained — FAILING** |

### 03 — `_LineNUMBERIZER`

| # | Useful product | Fixture | Capability | Disposition |
| --- | --- | --- | --- | --- |
| 3.1 | Annotate text with parseable line numbers | any text file | `linenumber` (`annotate`) | Retained — direct |
| 3.2 | Strip line numbers, preserving content | annotated file | `linenumber` (`strip`) | Retained — direct |
| 3.3 | Line → hash integrity map | any text file | `linenumber` (`map`) | Retained — direct |
| 3.4 | Machine-readable structural projection of a Python file | a `.py` file | `semantic_chunk` (+ `symbol_graph` / `import_graph` for relationships) | Retained — composed |
| 3.5 | Python semantic blocks export | a `.py` file | `semantic_chunk` — **run:** records carry `name`, `type`, `start_line`, `end_line`, `content`, `fingerprint` | Retained — direct ✔ |

> **3.4 is a judgment, stated openly.** No tool emits a literal AST tree or flat `ast.dump`
> projection; `symbol_graph` answers *who refers to whom*, which is a different artifact.
> The **useful outcome** — a machine-readable structure of a Python file, exportable — is
> produced by `semantic_chunk`. If the operator judges the literal AST tree to be the
> product rather than an intermediate representation, this becomes a failing row.

### 04 — `_GitPUSHER`

| # | Useful product | Fixture | Capability | Disposition |
| --- | --- | --- | --- | --- |
| 4.1 | Inspect repository state (branch / status / remote) | a git repo | `git_inspect`, `git status` | Retained — direct |
| 4.2 | Stage **an explicit approved working set**, then commit | ” | `git` hardcodes `add .` | **Retained — FAILING** |
| 4.3 | Commit, and push | ” | `git` (`commit`, `sync`) | Retained — direct |
| 4.4 | Safety gate before mutating operations | repo without `.gitignore` | `git` refuses `add .` without one | Retained — direct |
| 4.5 | Record stdout / stderr / exit code for every git command | ” | `steps[]` per command + `event_log` | Retained — composed |
| 4.6 | Pull before push | ” | no `pull` action | **Retained — FAILING** |
| 4.7 | Branch management with dirty-state checks | ” | no branch action | **Retained — FAILING** |

### 05 — `_UiMAPPER`

| # | Useful product | Fixture | Capability | Disposition |
| --- | --- | --- | --- | --- |
| 5.1 | Map a Tkinter UI surface | a Tk project | `tkinter_widget_tree` | Retained — direct |
| 5.2 | Callback graph from UI events to handlers | ” | `ui_callback_graph` | Retained — direct |
| 5.3 | Serialized report artifacts | ” | `report` | Retained — composed |
| 5.4 | Honour exclusions and gitignore during the scan | ” | shared PRUNE authority | Retained — direct |
| 5.5 | Collect unknown / unresolved cases honestly | ” | `ui_callback_graph` returns `unresolved_events` **and a count** | Retained — direct ✔ |

### 06 — `_TextTOUCHER`

| # | Useful product | Fixture | Capability | Disposition |
| --- | --- | --- | --- | --- |
| 6.1 | Create a UTF-8 text file in an approved folder | a target dir | `write_file` | Retained — direct |
| 6.2 | Preview exact target path and overwrite decision | ” | `write_file` preview-first | Retained — direct |
| 6.3 | Prevent writes outside the approved root | traversal attempt | `resolve_within_roots` | Retained — direct |
| 6.4 | Uniquely named (timestamp-suffixed) file | ” | — | **Retained — FAILING** *(minor)* |

### 07 — `_ChatWindowKERNAL`

| # | Useful product | Fixture | Capability | Disposition |
| --- | --- | --- | --- | --- |
| 7.1 | A conversational agent host that can drive the toolkit | an agent client | MCP entrance, certified in T8 | Superseded |
| 7.2 | Session persistence and replay | a session | `session_record`, `session_replay` | Retained — direct |
| 7.3 | Background work without blocking; run/pause/stop/resume | long task | T4 cancellation + `operation` `pause`/`resume` | Retained — composed |
| 7.4 | Failures leave a diagnosable record | a failing call | `event_log` (error, exit_code, client) + logging | Retained — composed |
| 7.5 | The chat GUI workspace itself | — | — | **Superseded — RULED 2026-08-20** |

### 08 — `_theCELL`

| # | Useful product | Fixture | Capability | Disposition |
| --- | --- | --- | --- | --- |
| 8.1 | Bootstrap a workspace bound to one target | empty dir | installer + instance identity (T6) | Superseded |
| 8.2 | Identity and state that survive restart | ” | `instance.json`, `_state` | Superseded |
| 8.3 | Run a streamed agent step | a prompt | `delegate` | Retained — direct |
| 8.4 | Execute a declared task queue | a task list | `plan`, `operation`, playbooks | Retained — composed |
| 8.5 | Ingest context for retrieval | a corpus | `rag_retrieve`, `semantic_chunk`, `bd_index` | Retained — composed |
| 8.6 | Capture outputs, feedback and exports as evidence | a run | `evidence`, `provenance` | Retained — composed |
| 8.7 | Personas / prompts / templates | ” | `prompt_*` family, `workflow_templates` | Retained — composed |
| 8.8 | Bounded, non-recursive agent work with captured artifacts | ” | `delegate` (one bounded step), `operation` (explicit ledger); **no orchestrator exists by rule** | Superseded |

> **8.8 is Superseded on the donor's own framing.** Its contract defines the capability as
> *"replace recursive spawn/push/inherited-context behavior with explicit Discover, Act,
> Capture steps"* — the useful outcome is that agent work is bounded and captured rather
> than recursively spawning. The current shape delivers that **by construction**: there is
> no second orchestrator, `delegate` is one step, `operation` is an explicit ledger.

> `_theCELL` is simultaneously the **C4-A acceptance target**. Its parity rows and its
> acceptance role are separate obligations and must not satisfy each other.

### 09 — `_WasmInferenceWRAPPER`

| # | Useful product | Fixture | Capability | Disposition |
| --- | --- | --- | --- | --- |
| 9.1 | Scaffold a local agent runtime with a manifest | target dir | `scaffold_project`, `app_factory` | Retained — composed |
| 9.2 | Preview all generated files / downloads / installs before acting | ” | preview-first seam convention | Retained — direct |
| 9.3 | Gate model downloads and dependency installs behind confirmation | ” | `dep_install` (Apply), `ollama_gov` | Retained — composed |
| 9.4 | A tested prompt request/response contract | a prompt case | `prompt_eval`, `prompt_case_builder` | Retained — composed |
| 9.5 | A true WASM runtime boundary | — | — | **Superseded** — the contract records the reference *never produced one*; it made a Python FastAPI node. There is no useful product here to retain |

### 10 — `_MonacoVIEWER`

| # | Useful product | Fixture | Capability | Disposition |
| --- | --- | --- | --- | --- |
| 10.1 | Human and agent operating on the same file state, each seeing the other's change | a file | T8's governed loop + T7 shared awareness | Superseded |
| 10.2 | Range-precise edits | ” | `edit`, `patch` | Retained — direct |
| 10.3 | Headless text operations | ” | `edit`, `write_file`, `read_file` | Retained — direct |
| 10.4 | Gated save | ” | preview-first + `apply:true` + source witness | Superseded |
| 10.5 | The Monaco editor GUI and vendored assets | — | — | **Superseded — RULED 2026-08-20** |
| 10.6 | Every client observes every mutation, whoever caused it | two clients | `src/core/watch.py` cursor + `event_log`; certified by T3 | Retained — direct |

### 11 — `_manifold-mcp`

| # | Useful product | Fixture | Capability | Disposition |
| --- | --- | --- | --- | --- |
| 11.1 | One tool entry point callable identically from CLI and agent | any tool | the seam; certified in T8 over both entrances | Superseded — prior art adopted |
| 11.2 | Reversible ingest of text into a corpus with exact evidence spans | text + files | `bd_index` / `bd_split` → `bd_scribe`; `verbatim.content` + `content_id` sha256 + line spans | Retained — composed |
| 11.3 | Query a corpus returning an evidence bag with provenance | a query | `bd_query` — **run:** anchors carry `occurrence_id`, `hunk_id`, `origin_id`, `structural_path` | Retained — composed ✔ |
| 11.4 | Verbatim reconstruction of source text from an evidence bag | ” | `bd_query` → `bd_project` — **run: returns the verbatim text**, with `sibling_index` for ordering | Retained — composed ✔ |
| 11.5 | Path containment on every file read and store write | traversal attempt | roots containment — *the contract notes the reference did NOT do this* | Retained — direct |

### 12 — `_TheDISMANTLER`

| # | Useful product | Fixture | Capability | Disposition |
| --- | --- | --- | --- | --- |
| 12.1 | One dispatch chokepoint for GUI, agent and automation | any tool | `invoke` | Superseded — prior art adopted |
| 12.2 | Machine-readable declared input schema per tool | any tool | `tool.json` `input_schema` | Superseded |
| 12.3 | Stable routing identity, not a display name | any tool | `tool.json` `id` | Superseded |
| 12.4 | Authority-enforced dispatch | an Apply tool | `policy.decide`, precept guard | Superseded |
| 12.5 | Dispatch provenance | any call | `event_log`, with `client` since T8 | Superseded |
| 12.6 | Monolith decomposition plan for a large file | a large module | `module_decomp_plan`, `complexity_score`, `import_graph` | Retained — composed |
| 12.7 | Load tools without executing arbitrary drop-in code | a planted tool | `registry` reads `tool.json` only — **no import**; `invoke` *"never imports tool code"* and runs a declared `entry` as a subprocess | Retained — direct ✔ |

---

## Resolved totals

**68 rows.** Counted by script from the tables above.

| disposition | rows |
| --- | --- |
| Retained — direct | 30 |
| Retained — composed | 17 |
| Superseded | 15 |
| **Retained — FAILING** | **6** — rows 1.6, 2.5, 4.2, 4.6, 4.7, 6.4 |

*I hand-wrote these totals twice and got them wrong twice* — 25/17/14/10 in the first
census, 27/17/18/6 here. Both were corrected by counting the tables with a script. The
lesson is not "be more careful": a summary maintained by hand beside a table that keeps
changing **will** drift, and a total that disagrees with its own matrix is worse than no
total. Recount by script after any edit.

✔ marks a row confirmed by **running it**, not by reading a summary line.

---

## What the census had to correct by investigating

- **`patch` takes one `path`.** Row 2.5 fails because of it.
- **`symbol_graph` is a resolved reference graph, not an AST projection.**
- **`git` has no `pull` and no branch action** — and **`git commit` stages `add .`**, which
  demoted 4.2 from a proposed pass to a failing row.
- **`stamp` generates tool skeletons**, not filename timestamps — 6.4.
- **Playbooks have no iteration construct** — which is what decides 2.5.
- **`semantic_chunk` returned "0 chunks"** and I nearly recorded a gap. The factory has no
  bound target, so the envelope was `output: null` and my reader defaulted it to `{}`. Run
  against a real fixture it returns full structural records. *A null read as an empty
  result is the same defect this project has now hit at three different layers.*
- **My first summary said 25/17/14/10** and disagreed with its own matrix.

---

## Stages remaining

1. **Build only what the six failing rows prove is owed.** Nothing else.
2. **Execute every retained row** through the current governed runtime, asserting the
   documented useful output on its fixture.
3. **Re-run with the parts bin / reference corpus unavailable.**

Parity closure gets the expensive certification once the retained rows actually execute.
Then: release certification from a clean clone on a clean machine → **STOP**.
