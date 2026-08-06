# Useful Helpers — Integration Field Report

**Audience:** the developer/agent building the `.useful-helpers` sidecar.
**Author:** an external coding agent that used the sidecar as its instrument to revive and
harden a real, unrelated application (**Forge** — a Python **Typer** CLI + **FastAPI** web UI +
application-service architecture, using local **Ollama** models).
**Date:** 2026-07 · **Scope:** everything I changed in the sidecar, every capability the sidecar
did *not* give me (forcing external tools), and every place the sidecar's *opinions* produced
false positives against equally-valid design tactics.

---

## 0. Thesis (the one takeaway)

The sidecar is a **strong idea trapped behind rigid, specific assumptions.** It was built as if it
*is* the project, encoding one particular design philosophy (strict layering, no framework-invoked
entrypoints, async-purity, one storage layout). The moment it met a real, "alien" framework it had
to be **retrofitted to be project-aware**, and even then several of its analysis tools **flagged
valid, deliberate design choices as defects.**

**To become a general instrument it must get more flexible and less specific:** configurable
policies, framework-awareness, and *advisory-with-confidence* signals instead of verdicts. Detail
follows. Each item below gives **Context → What → Why → Effect → Limitations still faced.**

---

## PART A — Modifications I made to the sidecar itself

> Note: the *foundational* change — splitting "toolkit home" from "work target" (`project_root`),
> and running tools with `cwd = project_root` while exporting `SUITE_HOME` / `SUITE_PROJECT_ROOT`
> (`src/core/config.py`, `src/core/invoke.py`) — was made by the project owner. Everything below is
> the **consistency work that change required**, which I had to do because the rest of the toolkit
> had not caught up to "I am an instrument on a parent project," not "I am the project."

### A1. Exclude the toolkit's own home from project scans
- **Context:** Once tools ran with `cwd = the parent project`, every scanner (`file_tree`,
  `repo_search`, `report`, and the `code_intel_shared` walkers) descended into `.useful-helpers/`
  itself. A single `file_tree` of the project returned **39 sidecar directories vs. 14 real project
  dirs** — the instrument drowned the project view. (This is the exact mirror of a host project that
  forgets to ignore its own tooling.)
- **What:** Added `toolkit_home_names()` to `tools/_toolkit.py` (derives the home dir name from
  `SUITE_HOME`, falls back to `.useful-helpers`) and unioned it into the ignore/prune sets of
  `file_tree`, `repo_search` (both the ripgrep glob and the Python fallback), `report`, and
  `code_intel_shared`.
- **Why:** A project-aware instrument must never present its own internals as part of the project.
- **Effect:** Project scans went to **0 sidecar references** while the full project stayed
  searchable; verified an explicitly-targeted scan *inside* the toolkit still works (the prune only
  fires when the home appears as a child of the scan root).
- **Limitations:** The exclusion is name-based (keyed off `SUITE_HOME`). It is correct for the
  standard install but is not a general "ignore rules" system — there is still **no per-project
  ignore configuration** for other instrument/vendor dirs a host might have.

### A2. `sidecar_install` was vending the wrong tree (real bug the cwd change exposed)
- **Context:** `sidecar_install` is meant to vend "the running toolkit" into a new host. Its source
  was `Path.cwd()`. After the cwd change, `cwd` = the **host project**, so the installer would have
  copied the host project instead of the toolkit. The smoke test caught it: `file_count` was **415**
  (host + toolkit) where it should be ~**203** (toolkit only).
- **What:** Changed the source to `SUITE_HOME` (`tools/sidecar_install/cli.py`).
- **Why:** The installer vends *itself*, independent of where its tools happen to run.
- **Effect:** `file_count` corrected to 203; the self-overlap guard still works.
- **Limitations:** None known for this tool, but it is a symptom of a broader issue — **many tools
  conflated "where I run" (cwd) with "what I operate on/produce," and with "where I live."** Three
  distinct roots (`cwd` work-target, `SUITE_HOME` instrument, output destination) needed teasing
  apart tool by tool.

### A3. Route generated artifacts/state to `SUITE_HOME`, not the host project
- **Context:** After the cwd change, tools that *write* defaulted their output under
  `cwd = the host project`, littering it with sidecar artifacts (e.g., `session_record` sessions,
  `bd_graph` DBs, `vendor_export` output, `projectmapper` snapshots). That violates "the project
  stays ignorant of the sidecar."
- **What:** Added `suite_home()` to `tools/_toolkit.py` and repointed default outputs in
  `memory_workflow_shared.artifact_root`, `bd_graph_shared.default_db_path`/`db_path_from_args`,
  `vendor_export` (`out_root`), `apps/projectmapper` (`out_db`), and `artifact_cleaner` (default
  root). **Inputs still read from `cwd` (the project); only default *output* moved.** Explicit
  destination args still let a caller opt into writing into the project.
- **Why:** Generated state belongs to the instrument; only deliverables the user explicitly asks for
  should land in the project.
- **Effect:** Verified in real mode: `bd`/`session_record` write under `.useful-helpers/_artifacts`,
  **no project-level `_artifacts` created.**
- **Limitations:** This was applied **tool-by-tool**, by hand. There is **no shared convention** —
  each tool independently decides its output root. A single `output_root()` policy (and a documented
  rule: "inputs = work target, outputs = SUITE_HOME unless overridden") would prevent the next tool
  from regressing.

### A4. Read side had to match the write side (`workspace_audit`, `artifact_catalog`)
- **Context:** With outputs moved to `SUITE_HOME`, tools that *audit the toolkit* or *scan for
  generated artifacts* were now pointing at the wrong place. `workspace_audit` defaulted `root="."`
  = the project and reported the toolkit's entire control plane (`src/tools/apps/…`) as **missing**;
  `artifact_catalog` scanned `project/_artifacts` where nothing lands anymore.
- **What:** `workspace_audit` now defaults to the toolkit home and additionally surfaces
  `toolkit_home` + `project_root`; `artifact_catalog` defaults its scan to `SUITE_HOME/_artifacts`.
- **Why:** Tools whose subject is the *toolkit* must default to `SUITE_HOME`; tools whose subject is
  the *project* default to `cwd`. Nothing in the codebase encoded which was which.
- **Effect:** `workspace_audit` reports the control plane present + both roots; `artifact_catalog`
  finds real artifacts.
- **Limitations:** The "is this tool about the toolkit or the project?" distinction is still
  **implicit** — a maintainer has to know it per tool. It should be a declared property in each
  tool's `tool.json`.

### A5. Governance event log leaked absolute machine paths
- **Context:** `event_log` stores only arg *key names* + a hash (good hygiene) — but it also stores
  **error strings verbatim**, and tool errors frequently embed a resolved absolute path
  (`C:\Users\...\project\...`). This is a privacy leak in what is otherwise "safe to share" state.
- **What:** Added `_relativize()` to `src/core/event_log.py` that strips `SUITE_PROJECT_ROOT` /
  `SUITE_HOME` prefixes from the error before storing (→ `<project>` / `<toolkit>`).
- **Why:** Even audit state should be path-scoped, not machine-scoped.
- **Effect:** New error records are relativized.
- **Limitations:** Only the `event_log` error field is covered. **Python logging to
  `logs/suite.log` still writes raw absolute paths** (separately gitignored, so not committed, but
  not sanitized). There is no central "path scrubber" the whole toolkit shares.

### A6. Host `AGENTS.md` onboarding pointer
- **Context:** The installer's host pointer was terse. The owner wanted `AGENTS.md` to be the
  deliberate "read this first" entrypoint that unfolds onboarding.
- **What:** Rewrote `_HOST_AGENTS_POINTER` in `tools/sidecar_install/cli.py` (mental model + 30-sec
  boot + unfold path) and rendered it to the live host `AGENTS.md`.
- **Why/Effect:** Turns the one deliberate project→sidecar breadcrumb into a genuine onboarding ramp.
- **Limitations:** It is still a single static template; no per-host customization hooks.

### A7. Smoke suite had to be told it was testing *itself*
- **Context:** The toolkit's own `tests/test_smoke.py` exercises tools against the toolkit's own
  files (`src/core`, `smoke_test.py`, `class SpineSmokeTest`). The cwd change flipped the work target
  to the parent project, so **7 smoke tests failed** (looking for toolkit files in the host project).
- **What:** Scoped `setUpClass` to set `SUITE_PROJECT_ROOT` to the toolkit home *only around*
  `resolve_paths()`, so the self-test suite treats the toolkit as its own work target — without
  disturbing `test_project_root_resolution`.
- **Why:** A toolkit's self-test's work target *is* the toolkit.
- **Effect:** 49/49 smoke tests pass again.
- **Limitations:** This is a workaround in the test harness. The deeper point: **the toolkit had no
  notion of "run against myself" vs "run against a host,"** so its own tests broke the instant it
  became project-aware.

---

## PART B — Capabilities the sidecar did NOT provide (I had to use external tools)

The single biggest gap: **the sidecar can analyze and remember, but it cannot *drive the target
project's own toolchain.*** For a real revival I constantly had to run the project's CLI, tests,
linters, server, model provider, a browser, git, downloads, and SQLite writes — none of which the
sidecar offers. Each row: **need → what I used → why the sidecar couldn't → recommendation.**

| # | Need | I used | Why the sidecar couldn't | Recommendation |
|---|------|--------|--------------------------|----------------|
| B1 | Run the target app's CLI / tests / formatters (`forge …`, `pytest`, `ruff`, `black`) | **Bash** (`.venv/Scripts/forge.exe`, `python -m pytest/ruff/black`) | No tool runs an arbitrary project command; `command_profile` only *detects* commands, it doesn't run them | A governed "run detected command" tool (build/test/lint/run), capturing structured output as evidence |
| B2 | Verify a running **web UI** (load pages, click, read console/network, screenshot) | **Claude Browser MCP** (`preview_start`, `navigate`, `read_page`, `computer`, `javascript_tool`, `read_network_requests`) | No browser/HTTP-client capability at all | Out of scope to build a browser, but a simple **HTTP probe** tool (GET/HEAD, status, body, headers) would cover most local-server verification |
| B3 | Run a **dev server** and verify against it | Browser MCP `preview_start` | `dev_server_manager` exists but is start/stop/tail only; no integrated verification, and it manages *registered* commands, not ad-hoc | Let `dev_server_manager` return a base URL + health signal that a probe tool can hit |
| B4 | **General git** (`init`, `add`, `commit`, plus `ls-files`, `grep --cached`, `check-ignore`, `log`) — needed for a privacy-gated commit | **native git** via Bash | The `git` tool is **quick-push only** (`init`/`status`/`commit`/`sync`); it exposes none of the inspection verbs a careful commit needs | Add read-only git inspection verbs (`ls-files`, `grep`, `check-ignore`, `log`, `diff`) so an agent can *reason about* a commit through the governed seam |
| B5 | **Download & vendor** two JS libraries (offline-proofing the UI) | **curl** | No HTTP/download tool | A governed, confirm-gated `fetch` tool (URL → workspace file, with size/host reporting) — high value, fits the dry-run-first ethos |
| B6 | **Modify SQLite data** (scrub absolute paths out of journal/evidence/event_log; reset a DB) | **native Python `sqlite3`** via Bash | `sqlite_inspect` is **read-only** (schema/rows/counts) | An `sqlite_exec` (parameterized UPDATE/DELETE, confirm-gated) or at least a "redact/scrub" helper |
| B7 | Precise **code edits** (multi-hunk refactors, exact string edits) | native editor tools | `edit` (regex) and `patch` (JSON hunks) exist but are coarse for large structured refactors | Fine as-is for small edits; agents will bring their own for big refactors — not a priority |
| B8 | Run **model inference** against the project's provider (Ollama) for real end-to-end tests | `forge` itself + `ollama` CLI | `ollama_gov` exists (governed inference) but is decoupled from the *project's* model config; I needed the project's own provider path exercised | Keep `ollama_gov` for sidecar-side model use; it's not meant to replace the project's provider |

**Pattern:** the sidecar is rich in *understand / remember / package* verbs and nearly empty in
*execute the project* verbs. Real work needs both.

---

## PART C — Design-philosophy conflicts (false positives against valid tactics)

This is the heart of your instinct. Several analysis tools encode **one** valid architecture and
report **other** valid architectures as defects. Each cost real time to triage and, worse, would
mislead a less-skeptical agent.

### C1. `domain_boundary_audit` - generic policy flags intended layering
- **Observed historically:** Reported 239 crossings as disallowed. Intended
  `cli/web -> services -> domain` dependencies drowned out one genuine reverse edge.
- **Required fix:** project-supplied layers, neutral output without policy, and no assumption that
  one architecture fits every project.
- **Resolved 2026-07-15:** the analyzer supports inline policies and validated sidecar-owned
  `policy_profile` files. Profiles are discoverable, path-confined, and local to the
  instrument; unmapped domains are strict and visible. Current Forge scan: 147 files, 22 mapped
  domains, 263 crossings, one violation, zero parse errors. The one violation is the retained
  `planning.planner -> services.planning_service` compatibility shim, not adapter/service
  noise.

### C2. `dead_code` — no notion of framework-invoked entrypoints
- **Observed:** Flagged `plan_list`, `memory_timeline` (Typer **CLI commands**, invoked by decorator,
  never called in code) and `normalize_model_name` (a provider-interface method) as dead.
- **Reality:** Decorator-registered commands, FastAPI routes, plugin entrypoints, and interface
  methods are **live** but have **no static caller.** ~half the 50 candidates were false positives
  of this kind.
- **Impact:** Following the tool literally would delete working CLI commands.
- **Fix the sidecar needs:** framework-awareness (treat `@app.command`, `@router.*`, `@*.callback`,
  ABC/interface methods, `__all__` exports as roots), or a config allowlist of "entrypoint
  decorators." At minimum, **rank by confidence** and label the framework-decorated ones.

### C3. `blocking_call_scan` — no async/execution-context awareness
- **Observed:** Flagged 11 `subprocess`/filesystem calls as "blocking."
- **Reality:** They are intended `subprocess` (git, ripgrep, verification) and fs walks, called from
  **synchronous** FastAPI routes (which FastAPI runs in a threadpool — they do **not** block the
  event loop) or from CLI code (where blocking is entirely fine).
- **Impact:** Zero of the 11 are bugs in context; the tool cannot tell an `async def` handler from a
  `def` handler from a CLI function.
- **Fix the sidecar needs:** classify by context — only blocking calls **inside `async def`** (or on
  the event loop) matter. Report others as informational, not findings.

### C4. The workspace-boundary model itself — "I am the project" vs "I am an instrument"
- **Observed:** Originally every boundary-guarded tool hard-refused any `root` outside
  `.useful-helpers` ("root must stay inside the project workspace"), and `invoke()` pinned tool cwd
  to the toolkit root. The toolkit literally **could not analyze the project it was attached to.**
- **Reality:** A sidecar's whole purpose is to operate on the *parent* project. This required the
  owner's `project_root` redesign, then all the A1–A4 consistency work above.
- **Fix the sidecar needs:** ship the "toolkit home vs work target" model as a **first-class,
  documented contract** with a shared helper API (`suite_home()`, `project_root()`,
  `toolkit_home_names()`, `output_root()`), so no tool re-derives roots ad hoc and new tools can't
  regress it.

### C5. The sidecar doesn't meet its own standard (self-inconsistency)
- **Observed:** The sidecar has **no ruff/black config**, and its own source trips **69+ ruff errors**
  under default rules (even untouched files). Meanwhile it is used to review projects (like Forge)
  that *do* enforce ruff/black. When I edited sidecar code I had to match its longer-line house style,
  not the standard it might be asked to check.
- **Impact:** A tool that critiques code quality should model the quality bar it implies, or be
  explicit that it is style-agnostic.
- **Fix the sidecar needs:** either adopt a lint config for its own code, or clearly declare "the
  toolkit is style-agnostic; it inspects, it does not conform."

---

## PART D — Overall recommendations (make it flexible, not specific)

1. **Policies over verdicts.** Every opinionated analyzer (`domain_boundary_audit`, `dead_code`,
   `blocking_call_scan`) should read an optional **per-project config** and, absent it, emit
   *signals with confidence*, not pass/fail. Valid alternative tactics must not read as defects.
2. **Framework-awareness.** Recognize the big Python framework idioms (Typer, FastAPI/Starlette,
   click, pytest, dataclasses/ABCs) so entrypoints and route handlers aren't "dead," and sync vs
   async is understood.
3. **One roots contract.** Promote `toolkit home / work target / output root` to a documented,
   shared API used by *every* tool. This is the single change that would have prevented most of
   Part A.
4. **Execute-the-project verbs.** Add governed tools to run the project's detected commands (B1), an
   HTTP probe (B2/B3), general read-only git inspection (B4), a confirm-gated `fetch` (B5), and
   SQLite writes/redaction (B6). The sidecar can *understand* a project but not *operate* it.
5. **A central path scrubber** used by logging + event_log + any state writer, so machine paths never
   leak into shareable state.
6. **Declare each tool's subject** (`operates_on: project | toolkit`) in `tool.json` so defaults and
   audits are correct by construction.

---

## PART E — Limitations still outstanding (honest status)

- **Resolved 2026-07-15:** `domain_boundary_audit` now has a local Forge policy profile.
  It reduces 263 crossings to one explicit compatibility inversion, with zero unmapped domains.

- **Artifact-output routing is per-tool, not systemic** (A3) — a new tool can still default to the
  wrong root; no shared `output_root()` yet.
- **Path scrubbing covers only `event_log.error`** (A5) — `logs/suite.log` still holds raw paths.
- **The "toolkit vs project subject" distinction is implicit** (A4/C4) — not declared per tool.
- **Self-lint debt remains** (C5) — untouched sidecar files still trip ruff.
- **No execution/probe/fetch/git-inspect/sqlite-write tools** (Part B) — every project-operation
  still requires an external tool outside the governed seam, which means those steps are **not
  audit-logged by the sidecar** (a governance blind spot for exactly the highest-impact actions).

---

---

## PART F — Functional tool workflows (the directional knowledge the docs omit)

`_docs/TOOLS.md` documents **what** each tool does. It does **not** document **how to drive them**
— the sequencing, the flags you must set, the escaping realities, and which outputs to trust. That
"directional" knowledge is where all the real friction lived. This section is the missing operator's
manual, written from what actually worked.

### F0. The governed seam and the JSON-escaping reality (most important)
- **Documented path:** `python -m src.app cli tool-call --tool <id> --args-json "{...}"` (run from
  inside `.useful-helpers/`), or `run.bat tool <id> "<json>"`.
- **What actually happens:** the moment args contain arrays, nested objects, quotes, long text, or
  Windows paths (backslashes), shell-escaping the JSON string breaks — repeatedly. I lost real time
  to this. **The only reliable workflow** for non-trivial args is to *not* hand-write the JSON in the
  shell. I drove every non-trivial call through a tiny Python wrapper that builds a dict and lets
  `json.dumps` handle escaping, invoking the seam as a subprocess:
  ```python
  import json, subprocess, sys
  args = {"action": "add", "title": "...", "files": [...], "decisions": [...]}   # real structures
  subprocess.run([sys.executable, "-m", "src.app", "cli", "tool-call",
                  "--tool", "journal", "--args-json", json.dumps(args)],
                 capture_output=True, text=True)
  ```
- **Directional need the sidecar should meet:** accept args from a **file or stdin**
  (`--args-file -`), and steer agents to the **MCP entrance** (`python -m src.app mcp`) for anything
  structured — MCP takes native JSON and sidesteps the shell entirely. The CLI seam is fine for
  humans typing `{"action":"list"}`; it is hostile for programmatic use.

### F1. The dry-run-first flag is real, and its NAME is inconsistent (a trap)
Every `Apply`-authority tool defaults to **preview** and does nothing until you pass an explicit
"really do it" flag — good ethos, but **the flag name differs per tool**, which silently no-ops your
call if you guess wrong:
- `artifact_cleaner` → `{"confirm": true, "dry_run": false}`
- `session_record` create → `{"write": true}`
- `bd_scribe` / `bd_index` → `{"dry_run": false, "confirm": true}`
- `sidecar_install` → `{"dry_run": false, "confirm": true}`
- `edit` / `patch` / `test_scaffold` → `{"write": true}`

I hit this with `session_record` (returned `{"ok": false, "error": "create requires write:true"}`)
and again reasoning about the cleaner. **Directional need:** standardize on ONE confirm flag
(`apply: true`) across all Apply tools, and have the preview response state the exact flag needed.

### F2. Pointing a tool at the work target
- **Boundary-guarded tools** (`command_profile`, `dependency_check`, `repo_search`, `file_tree`,
  `secret_audit`, the `code_intel` tools, `sqlite_inspect`) reject any `root` outside cwd. Post
  project-awareness, `cwd = the parent project`, so pass `{"root": "."}` (or a project-relative
  subpath) to analyze the project. **Before** the project-awareness redesign these tools *could not
  reach the project at all* — a hard wall.
- **Path-based tools** (`report`, `codebase_bundle`, the `bd_*` family) take an arbitrary `path`.
  Before project-awareness I had to feed them **absolute** paths to escape the boundary; after, a
  relative `.` works.
- **Directional need:** nothing tells you which class a tool is in until it errors. Declare scoping
  in `tool.json`.

### F3. The "understand + audit an unfamiliar project" tool-chain (order + trust)
There is no documented workflow for "use these tools to actually understand and vet a codebase."
This is the chain I used, in order, with the **signal quality** you should assign each output:

1. `report {"path":"."}` — macro structure (purpose/classes/functions/imports per file). **Trust:
   high.** Orientation first.
2. `import_graph {"root":"forge"}` — internal edges, fan-in/out, **cycles**. **Trust: high**; cycles
   are real and high-value (this is how I found the planning import cycle).
3. `complexity_score {"root":"forge"}` — function/module hotspots. **Trust: high**; points straight
   at risk/refactor targets.
4. `module_decomp_plan {"root":"forge"}` — oversized modules. **Trust: high** (size is objective).
5. `dead_code {"root":"forge"}` — unused-symbol candidates. **Trust: medium** — *must triage*;
   framework entrypoints (Typer commands, routes) are false positives.
6. `blocking_call_scan {"root":"forge"}` — **Trust: low** for web/CLI; it can't see sync-vs-async
   context.
7. `domain_boundary_audit {"root":"forge"}` — **Trust: low** without a project layering policy;
   mostly flags intended architecture.
8. `secret_audit {"root":"."}` — **Trust: high** for a first pass.

**The rule that made this usable:** run the *deterministic structural* tools first and believe them;
treat the *opinionated* tools (5–7) as **leads, not verdicts**, and **verify every finding by hand**
(`grep`/read the actual code) before acting. I confirmed the import cycle at `planner.py:48`,
confirmed `generate_payload` was truly unused, and confirmed the "dead" `plan_list` was a live Typer
command — all by hand — before touching anything. A less skeptical agent, taking the tools at face
value, would have deleted working commands and "fixed" a correct architecture.

### F4. The bd-graph build→inspect→retrieve loop
The tools exist but the *loop* isn't written down. What works end-to-end:
```
bd_index   {"path":"forge/git", "dry_run":false, "confirm":true}   # split -> emit -> scribe
bd_status  {}                                                       # table presence + row counts
bd_query   {"query":"return current branch name", "top_k":3, "hops":2}   # anchors + projected subgraph
bd_project {"occurrence_ids":[...], "hops":2}                        # neighborhood around known nodes
```
- The DB defaults to `SUITE_HOME/_artifacts/bd_graph/cold_anatomy.sqlite3` (after the artifact-routing
  fix). `bd_status` on a fresh index of `forge/git` showed **13 content / 13 occurrence / 10
  relations**; `bd_query` returned ranked `GitService` AST fragments with `structural_path`,
  `node_kind`, `score`, and a content snippet.
- **Read the output like this:** `anchors` = entry points ranked by match; `graph`/subgraph = the
  projected neighborhood to actually reason over. Query → get anchors → project around them = the
  retrieval motion. (This loop is the seed of Part G.)

### F5. Memory workflow + the path-token discipline (a real leak I caused and fixed)
- **Record work:** `journal {"action":"add","title":..,"summary":..,"files":[..],"decisions":[..],
  "backlog":[..],"status":"closed"}`; **ground claims:** `evidence {"action":"attach","kind":
  "tool_output","summary":..,"body":..,"attached_to":<journal_uid>,"attached_to_type":"journal"}`.
- **Undocumented gotcha I learned the hard way:** the journal exports a **committed** Markdown mirror
  (`JOURNAL.md`). If you write an absolute machine path into an entry's *text*, it lands in
  `JOURNAL.md` and leaks on commit. I did exactly this in a "parked" entry and had to scrub it twice.
  **Directional rule:** keep journal/evidence prose **path-tokened** (`<project>`, `<toolkit>`),
  never raw `C:\Users\...`. The sidecar should scrub on write (see A5/Part D).

### F6. Verifying a running app (not a sidecar capability, but part of the loop)
The sidecar can't drive a browser, so the real verification motion used the Browser MCP:
`preview_start {name}` → `get_page_text` / `read_page` (structure) → `read_network_requests`
(prove no external calls / correct API hits) → `read_console_messages onlyErrors` → `javascript_tool`
(computed state, e.g. `typeof lucide`, rendered-icon count). **Screenshots timed out every time** in
this headless pane, so I verified via **text + network + console + JS**, never pixels. Any agent
using the sidecar on a web project needs this loop; the sidecar gives it none of these verbs (see B).

---

---

## PART G — The graph-of-graphs RAG as a plug-in prosthetic (priority)

**The goal, stated concretely:** a portable, project-attached memory such that **any agent, with zero
prior context, can `attach()` and immediately KNOW the project** — its purpose, shape, entry points,
subsystems — and can then retrieve at **any granularity**, moving fluidly between the macro map and a
single line of code, and between the *code* ("what/where") and the *rationale* ("why"). A prosthetic
you plug in and wear like an external drive.

Everything below is a build spec grounded in what the `bd-graph` toolset **already is**, because it
is 70% of the way there and shipping unused.

### G1. What already exists (the seed) — do not rebuild it
- **Storage:** one portable SQLite DB (`SUITE_HOME/_artifacts/bd_graph/cold_anatomy.sqlite3`). This is
  the "external drive." ✔
- **CAS/CIS dedup:** `content_nodes(hunk_id=sha256(content) PK, node_kind, content, attention_weight,
  static_mass)` — identical content stored once. ✔
- **Atomic node with surfaces:** `occurrence_nodes(occurrence_id, hunk_id→content, origin_id,
  layer_type, structural_path, sibling_index, metadata_json, vector_json, dimensions)` — one content
  hunk, many placements, each carrying structural + (stub) semantic + metadata surfaces. ✔
- **Edges:** `relations(source_occ_id, op, target_occ_id, weight)` — a typed, weighted graph. ✔
- **Pipeline:** `split_*` (AST-aware for Python: class/function → fragments) → `emit_node` →
  `ingest_nodes` (scribe) → `query_db` (anchors + hop projection) → `project_db` (neighborhood). ✔
- **Proven:** indexing `forge/git` produced 13/13/10 nodes/edges; a natural-language query returned
  the right ranked AST fragments.

**It already realizes: CAS, multi-surface nodes, a structural DAG, typed edges, projection, and a
portable store.** The gaps below are what stand between "a neat prototype" and "a prosthetic."

### G2. The atomic node's surfaces — what a node must carry to answer an agent

| Surface | Answers | Status | How to complete it |
|---|---|---|---|
| **Content** (verbatim, CAS) | "show me exactly" | ✔ | — |
| **Structural** (path, parent, siblings, layer) | "where am I / what contains me" | ✔ | — |
| **Type / node_kind** ("what am I") | "function? class? doc? test? config?" | ✔ partial | broaden kinds beyond Python AST (markdown sections, config keys, test cases) |
| **Provenance** (origin file + **line range** + hash) | "point me at the source" | ✖ line range | store `start_line`/`end_line` on occurrence so `expand()` can cite `file:Lx-Ly` |
| **Semantic vector** (real embedding) | "what is this *about*; find similar" | ✖ **stub** | **wire local embeddings** (G4) — highest-leverage fix |
| **Derived** (summary, keywords, intent/role) | "what does this do, in one line" | ✖ **missing** | **LLM surfaces** via local model (G5) |
| **Symbolic** (defines / references / imports / calls) | "who uses this; what does it call" | ✖ mostly | build a def↔use/import graph as `relations` (G6) |

The stub semantic vector (`vectorize()` = sha256 of tokens → 16 floats) is the single biggest lie in
the system: "vector" retrieval today is really lexical. Fixing it (G4) unlocks everything downstream.

### G3. The sub-graphs, and what the hypergraph SPINE binds
"Graph of graphs" = several graphs over the **same** occurrence nodes, connected by a spine:
1. **Containment tree** — folder→file→class→function→fragment (`parent_occurrence_id`). ✔
2. **Structural DAG** — sibling/order relations. ✔
3. **Symbol/reference graph** — `defines`, `references`, `imports`, `calls` edges. ✖ (G6)
4. **Semantic similarity graph** — k-NN over real embeddings (materialized or on-demand). ✖ (G4)
5. **Knowledge graph** — decisions / lessons / plans / evidence (from `journal`+`evidence`) as nodes,
   linked to the code they touch. ✖ (G7) — **this is the missing "why" layer.**
6. **(later) statistical/co-occurrence** — files/symbols that change or appear together.

The **spine is a hypergraph**: higher-order edges that bind a *set* of nodes across these sub-graphs
into one addressable unit. Example hyperedge: `{decision "use JWT", the auth module it motivated, the
plan that implemented it, the test that verifies it, the evidence of the passing run}` — one node an
agent can grab to get the whole story. The current `relations` table is **binary only**; the spine
needs an n-ary construct (a `hyperedges` table + a `hyperedge_members` join, or reified
"bundle" occurrence nodes whose relations point at their members).

### G4. Real embeddings via local models (do this first — biggest win)
- **Replace** `bd_graph_shared.vectorize()`'s sha256 stub with a call to a **local Ollama embedding
  model** already installed on this rig: `nomic-embed-text` (768-dim, strong general code/text) or
  `all-minilm` (384-dim, faster). Workflow per node at `emit`/`scribe` time:
  `POST http://localhost:11434/api/embeddings {"model":"nomic-embed-text","prompt":<content>}` → store
  the returned vector in `vector_json` + set `dimensions`.
- **Query side:** embed the query with the same model, score anchors by cosine similarity (blend with
  the existing lexical score, e.g. `0.6*cosine + 0.4*lexical`).
- **Index:** JSON-in-row + brute-force cosine is fine to a few thousand nodes on this rig; add
  `sqlite-vec` (or hnswlib) only when it grows. Do **not** prematurely optimize.
- **Free lunch from CAS:** because vectors key off `hunk_id` (content hash), re-indexing only embeds
  *new/changed* content — embeddings are computed once per unique hunk, ever.
- **Governance:** route this through the existing `ollama_gov` seam so embedding calls are token-
  governed and audit-logged.

### G5. LLM-derived surfaces (makes it legible to an agent)
- On index, for each **coarse** node (module / class / function / doc-section — *not* every fragment,
  for cost), call a **small local model** (`qwen2.5-coder:7b`, or `:3b` for speed) to produce:
  a **one-line summary**, **keywords**, and an **intent/role** tag ("HTTP adapter", "domain service",
  "pure util", "test"). Store in `metadata_json`.
- **Why it matters:** (a) `attach()`'s project map is built from these summaries; (b) semantic
  retrieval improves if you *also* embed the summary; (c) an agent reading `expand()` gets a sentence,
  not 120 lines to skim.
- **Cost control:** cache by `hunk_id` (never re-summarize unchanged content); only summarize nodes
  above a size/importance threshold (`attention_weight`).

### G6. The symbol/reference graph (the code's real wiring)
- From the Python AST already parsed in `split_*`, additionally emit `relations`:
  `defines(module→symbol)`, `imports(module→module)`, and best-effort `references`/`calls`
  (name → definition in scope). This turns "13 fragments" into "this function calls that service,
  which is defined here, imported there" — the graph an agent needs to trace impact.
- This is also what makes `dead_code`/`domain_boundary` **correct** if the sidecar reuses it: real
  def↔use edges + framework-entrypoint roots.

### G7. Unify `journal`/`evidence` INTO the graph (the step that makes it "know everything")
Today code lives in `bd-graph` and knowledge (decisions/plans/lessons/evidence) lives in separate
SQLite DBs. **For an agent to KNOW the project, the "why" must be in the same graph as the "what."**
- Ingest each `journal`/`evidence` item as a **knowledge node**; link it to the code nodes it names
  (by file path in `related_files`, or by symbol) with `relates_to` edges.
- Now `why("forge/planning/planner.py")` traverses from a code node to the decisions/plans/evidence
  that touched it. That linkage is the difference between "a code index" and "project memory."

### G8. The agent-facing attach protocol (the prosthetic API, over MCP)
A **minimal, stable verb set** an agent binds to once and reuses on any attached project:
- `attach(project) → PROJECT_MAP` — a generated orientation: languages, architecture/layers, entry
  points, top subsystems (by graph centrality), key modules with their one-line summaries. **This is
  the "plug in and instantly know" surface.** Built from G5 summaries + G6 structure + centrality.
- `query(text, k, hops) → {anchors, subgraph}` — semantic+lexical anchors and their projected
  neighborhood (macro→meso). (= today's `bd_query`, upgraded by G4.)
- `project(node_ids, hops) → subgraph` — neighborhood around known nodes (meso→micro). (= `bd_project`.)
- `expand(node_id) → {content@file:Lx-Ly, summary, defines/references, neighbors}` — everything about
  one node (needs G2 line ranges + G5 summary + G6 edges).
- `why(path_or_symbol) → knowledge_nodes` — the linked decisions/plans/lessons/evidence (needs G7).
- `neighbors(node_id, kind) → nodes` — traverse one edge type (containment | references | semantic |
  knowledge).

Expose all six through the **MCP server** so any agent (you, or a future local one) plugs in with no
bespoke glue — that is the "wear it like an external drive" moment.

### G9. The zoom workflow (macro↔micro rumination — the thing you asked for)
The prosthetic's value is the *motion* between altitudes:
1. **Macro:** `attach()` → read `PROJECT_MAP` → pick a subsystem ("planning").
2. **Meso:** `query("planning pipeline", hops=2)` → anchors → subgraph of the pipeline modules.
3. **Micro:** `expand(node)` → exact source + its summary + what it calls/defines.
4. **Lateral:** `neighbors(node, "semantic")` (similar code elsewhere) · `neighbors(node,
   "references")` (impact) · `why(node)` (rationale).
An agent never loads the whole repo; it *walks* the graph at the altitude the task needs. That is the
"ruminate at any level of macro or micro" you described, made mechanical.

### G10. Freshness / incrementality (so it stays true)
- **Detect stale:** compare each source file's mtime/hash to its indexed nodes; re-index only changed
  files (re-`split`→`scribe`).
- **CAS makes updates cheap:** unchanged hunks keep their `hunk_id` → their vector and summary are
  reused; only genuinely new/changed content pays the embed/summarize cost.
- **Governance:** every (re)index is an audit-logged `invoke` — the memory's provenance is itself
  recorded.

### G11. Build order (tranches to "optimal")
| # | Tranche | Unlocks | Effort |
|---|---------|---------|--------|
| **Ga** | Real embeddings via Ollama (G4) | actual semantic retrieval | small |
| **Gb** | Line ranges + provenance on nodes (G2) | `expand()` can cite exact source | small |
| **Gc** | LLM summary/keywords/intent per coarse node (G5) | legibility + the project map | medium |
| **Gd** | Symbol/reference graph edges (G6) | impact tracing; correct dead-code/boundary | medium |
| **Ge** | Ingest journal/evidence as knowledge nodes + links (G7) | the "why" layer | small-med |
| **Gf** | `attach()` → generated PROJECT_MAP (G8) | zero-context orientation | medium |
| **Gg** | Hypergraph spine (n-ary bundles) (G3) | cross-subgraph "whole story" nodes | medium |
| **Gh** | Incremental/staleness reindex (G10) | stays fresh cheaply | small |
| **Gi** | The 6-verb attach API over MCP (G8) | any agent plugs in | small |

Recommended first three: **Ga → Gb → Ge** (real vectors, citable source, and the why-links) give the
biggest jump in "an agent actually knows the project" for the least work, all on local models.

### G12. Definition of "optimal" (acceptance)
- A fresh agent calls `attach()` and can state the project's purpose, architecture, entry points, and
  subsystems **without reading a file**.
- `query()` returns **semantically** relevant hunks (paraphrase-tolerant), not just lexical matches.
- `expand()` yields exact source (`file:Lx-Ly`) + a one-line summary + defines/references + the linked
  "why."
- Re-indexing a changed repo is **incremental** (seconds), thanks to CAS.
- The whole thing is **one portable SQLite file** plus a **six-verb MCP surface** — nothing else to
  install to "know" the project.

---

*Cross-references: the sidecar's own `journal` holds the change-by-change record (entries incl. uids
`585e57905a99`, `08af00bbc529`, `efa0fa204628`, and the audit/remediation entries). This report is
the meta-analysis those entries point toward. Part G is grounded in `tools/bd_graph_shared.py` and the
`bd_*` tool suite, and in the project-memory note the author keeps on the graph substrate.*


---

## POST-RE-VEND ADDENDUM - 2026-07-16 ORCHESTRATION-SPINE WORK

This addendum supersedes stale capability statements in Part B where the re-vended instrument now
contains the requested tools. It records observations from the later acceptance-contract, evidence,
structured-edit, semantic-gate, exact-snapshot, and targeted-repair phases.

### Capabilities now present

The re-vend materially improved the execute/inspect surface:

- `project_run` now provides governed dry-run-first project command execution.
- `dev_server_manager` now owns registered server lifecycle, state, log tails, port, and health.
- `http_probe`, `fetch`, and `git_inspect` are present.
- The graph/RAG and boundary-aware code-intelligence tool families are present.
- Journal, evidence, and event-log memory survived the re-vend; the targeted-repair phase is
  journal entry 42.

These additions resolve the architectural absence described by B1-B5. They do not remove host
sandbox restrictions, but they provide the correct governed contracts.

### New F1 - regex edit needs literal and expected-count guards

**Observed:** The `edit` tool reports replacement count after writing. A non-greedy regex beginning
at a repeated validation guard matched an earlier similar guard and removed a larger workflow block
than intended. Immediate inspection caught it and the code was restored.

**Recommended change:**

- Add `literal: true` for exact replacement.
- Add `expected_replacements`; refuse writes unless the dry-run count matches.
- Return bounded before/after context for every dry-run match.
- Require confirmation when a match spans a configured size threshold.

### New F2 - patch hunk vocabulary needs a nested schema example

A patch call using `old` and `new` failed because the actual fields are `search_block` and
`replace_block`. Define the nested hunk schema and one atomic multi-hunk example in `tool.json`.

### New F3 - server start reports process creation, not startup success

`dev_server_manager start` returned `started: true` immediately after process creation. The child
then exited before binding because sandboxed Windows Python could not initialize `_ctypes`.
`health` correctly failed and `tail` exposed the traceback.

When a port or health URL is supplied, optionally wait through a bounded grace period and return
`startup_status: healthy|exited|timeout`. Distinguish `process_created` from `started`, and
include a bounded log tail when the child exits during startup.

### New F4 - process inspection degrades usefully under restricted permissions

`process_port_inspector` could not use `tasklist`, but accurate `netstat -ano` evidence still
showed Ollama listening and Forge absent. Preserve this graceful degradation and enrich listener
metadata through a secondary bounded method when available.

### New F5 - governed execution inherits host limits

The host approval service exhausted its allowance. External pytest/server execution was rejected;
sandboxed Windows Python could collect tests but could not create fixture temp directories, and the
managed server child could not initialize `_ctypes`. This is primarily an environment limitation.
Future command results could classify policy, temp-ACL, missing-DLL, and project failures separately.

### Boundary outcome

Forge runtime and product configuration no longer contain a hardcoded instrument directory name.
Forge ignores dot-prefixed host tooling/configuration by generic convention and supports additional
names through `FORGE_EXTERNAL_DIRS`. The instrument derives its target and excludes itself; Forge
has no identity-level knowledge of the instrument.
