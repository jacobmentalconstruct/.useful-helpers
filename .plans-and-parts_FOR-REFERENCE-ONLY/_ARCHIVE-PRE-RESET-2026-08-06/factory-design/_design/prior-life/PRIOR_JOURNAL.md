# App Journal

_Authoritative store: `_journalDB/app_journal.sqlite3`. Generated mirror — do not hand-edit; write via `tools/journal`._

## #1 · Forge functional-prototype review + planning-hijack fix  `585e57905a99`  [closed]
*2026-07-12T10:33:44.718771+00:00* · phase: prototype-hardening

Reviewed the Forge workbench (parent project) and drove it to a verified functional prototype on local Ollama. Baseline confirmed: forge doctor all-green, CLI works, 531 tests pass. Exercised the deterministic pipeline end-to-end (repo detect -> workset suggest/create/refresh -> context bundle) and the AI pipeline (forge ask 8s; forge plan 21s) with qwen2.5-coder:7b. Web workbench (uvicorn:8000) verified live across Dashboard/Worksets/Artifacts with zero console errors; Artifact Registry surfaces this session's worksets, context bundle, and plan. Fixed TWO real defects: (1) repo intelligence ignored .git/.forge/.claude but not .useful-helpers, so the sidecar (its own Python project) polluted detect/workset/grep candidates -- added .useful-helpers to IGNORED_DIR_NAMES. (2) Planning-prompt hijack: an unrelated 'mac silicon packaging' memory item was injected last (highest recency) with guidance 'use them to inform your plan', causing the weak local model to copy that prior task+workset verbatim instead of the real task -- hardened build_memory_section framing and added a final task re-anchor so the model reads the real task last. Same weak model now produces a correct, grounded plan. 532 tests pass (added 1 regression test).

**Files:** forge/repository/ignore.py (+ .useful-helpers ignore), forge/planning/prompts.py (memory framing + _final_task_reanchor), tests/test_planning.py (regression test + memory imports), tests/test_execution.py (updated memory-section header assertion)

**Decisions:**
- Prompt hardening is the primary fix (model-agnostic) over tightening memory retrieval; injected memory must never override the stated task regardless of relevance.
- Treat .useful-helpers like .git/.forge/.claude: an instrument dir excluded from repository intelligence.
- Verify the web UI via text extraction (page text + logs + console) since screenshots time out in this headless pane; primary method per the harness workflow.

**Backlog:**
- Full guarded patch pipeline (forge implement -> patch validate -> verify -> policy -> apply) is unproven: Forge-main is not a git repo, so git-apply-check gates cannot run. Needs `git init` (user decision).
- Consider a relevance-score threshold on planning memory injection so clearly-unrelated items are not injected at all (secondary to the prompt hardening).
- .forge/project.json still records the original macOS root <upstream-root> (stale; resolved at runtime, cosmetic).
- Apply the same final task re-anchor to the execution/implementation prompt (execution_prompt.py) for symmetry once the patch pipeline is exercised.


## #2 · Sidecar made consistently project-aware (toolkit-home exclusion + installer source fix)  `08af00bbc529`  [closed]
*2026-07-12T15:29:52.076737+00:00* · phase: sidecar-project-awareness

Followed up the user's config.py/invoke.py change (tools now run with cwd=project_root, the sidecar's parent, with SUITE_HOME/SUITE_PROJECT_ROOT exported). Made the rest of the toolkit consistent: (1) added tools/_toolkit.toolkit_home_names() and wired it into every project-scanning tool (file_tree, repo_search rg+fallback, report, code_intel_shared) so the toolkit's own home is pruned from project scans -- the mirror of the .useful-helpers pollution fixed in Forge. Project view now shows 0 sidecar refs while the full project stays searchable. (2) Fixed a real production bug in sidecar_install: it vended Path.cwd() (now the host project) instead of the running toolkit; now vends SUITE_HOME (file_count 415->203). (3) Scoped the toolkit's own smoke suite (setUpClass) to treat the toolkit as its work target so self-tests exercise the toolkit's real files, without disturbing test_project_root_resolution. All 49 smoke tests pass; import_graph/report/file_tree/repo_search verified clean on the project.

**Files:** tools/_toolkit.py (+toolkit_home_names), tools/file_tree/cli.py, tools/repo_search/cli.py, tools/report/cli.py, tools/code_intel_shared.py (exclude toolkit home), tools/sidecar_install/cli.py (source = SUITE_HOME, not cwd), tests/test_smoke.py (setUpClass scopes work target to toolkit home)

**Decisions:**
- Exclude the toolkit home from project scans by name via a shared helper keyed off SUITE_HOME (install-name agnostic); pruning by dir-name during walk is safe for explicit in-toolkit targeting (verified rg globs match relative to root).
- The toolkit's smoke suite is a SELF-test: scope its project_root to the toolkit home rather than rewrite each test to hardcode paths.
- vendor_export left as-is: it is a generic 'export any folder' tool, so a cwd(project) default is correct; only sidecar_install must vend the toolkit itself.

**Backlog:**
- Artifact-writing tools (vendor_export out_root, projectmapper, bd_scribe, session_record) default their output under cwd=project_root now, so generated artifacts land in the host project; decide whether they should target SUITE_HOME/_artifacts instead.
- workspace_audit still reports the toolkit root as 'root' -- consider surfacing project_root too now that they differ.


## #3 · Route sidecar artifacts to SUITE_HOME + craft host AGENTS.md onboarding  `efa0fa204628`  [closed]
*2026-07-12T15:49:17.238111+00:00* · phase: sidecar-project-awareness

Implemented the 'project stays ignorant of the sidecar' principle for generated output. Added tools/_toolkit.suite_home() and routed every default artifact/state path to it (was cwd=project post-awareness): memory_workflow_shared.artifact_root (session_record, memory_flush), bd_graph_shared default_db_path/db_path_from_args, vendor_export out_root, projectmapper out_db, artifact_cleaner default root. Explicit paths still opt back into the project. Verified in real mode: bd + session_record write under .useful-helpers/_artifacts, no project-level _artifacts created. Inputs still read from cwd=project. Host-pointer decision: KEEP the host AGENTS.md as a deliberate onboarding entrypoint (the project is intentionally not 100% ignorant -- one breadcrumb). Rewrote _HOST_AGENTS_POINTER as a 'read this first' doc (mental model: sidecar knows project / project ignorant of sidecar; one governed seam; memory is history) that unfolds to the sidecar AGENTS/README/ONBOARDING/TOOLS, and rendered it to the live Forge-main/AGENTS.md. 49 smoke tests pass; installer dry-run vends the new pointer (203 files).

**Files:** tools/_toolkit.py (+suite_home), tools/memory_workflow_shared.py, tools/bd_graph_shared.py, tools/vendor_export/cli.py, apps/projectmapper/cli.py, tools/artifact_cleaner/cli.py (default output -> SUITE_HOME), tools/sidecar_install/cli.py (_HOST_AGENTS_POINTER onboarding rewrite), ../AGENTS.md (rendered live host onboarding)

**Decisions:**
- Split input vs output path resolution: inputs stay on cwd (work target), generated artifacts/state default to SUITE_HOME; explicit destination args opt back into the project.
- Keep the host AGENTS.md breadcrumb by design -- the project is deliberately 'ignorant except for one doorway' so a user/custom-agent can say 'read AGENTS.md first' and onboarding unfolds from there.
- vendor_export source still defaults to cwd(project) (generic exporter); only its OUTPUT moved to SUITE_HOME.

**Backlog:**
- artifact_catalog reads artifacts -- confirm it looks under SUITE_HOME now that writes default there.
- workspace_audit still reports only the toolkit root; surface project_root too.
- Forge repo still carries a .useful-helpers entry in forge/repository/ignore.py -- keep (dogfood convenience) consistent with the deliberate-breadcrumb decision.


## #4 · Fix workspace_audit + artifact_catalog defaults for project-awareness  `507bc2bea9a8`  [closed]
*2026-07-12T16:05:18.204610+00:00* · phase: sidecar-project-awareness

Closed the two remaining backlog items — both were genuinely broken by the cwd=project shift. workspace_audit audits the TOOLKIT's control plane (src/tools/apps/config/_docs) but defaulted root='.'=project, so it reported the whole control plane as missing; now defaults to the toolkit home (suite_home()) and additionally surfaces toolkit_home + project_root. artifact_catalog defaulted its scan to cwd/_artifacts=project, but artifacts now write to SUITE_HOME/_artifacts, so it found nothing; now defaults to suite_home()/_artifacts. Both keep explicit `root` as an opt-in override against the work target. Verified: workspace_audit control_plane all true + project_root=Forge-main; artifact_catalog root=.useful-helpers/_artifacts. 49 smoke tests pass.

**Files:** tools/workspace_audit/cli.py (default root -> suite_home; +toolkit_home/+project_root), tools/artifact_catalog/cli.py (default scan root -> suite_home/_artifacts)

**Decisions:**
- Tools that audit/scan the TOOLKIT itself (workspace_audit, artifact_catalog) default to SUITE_HOME; tools that analyze the PROJECT default to cwp=project. The read side now matches the write side.


## #5 · Project cleanup: retire predecessor .scaffold sidecar refs, clean test cruft  `562e6dc774ac`  [closed]
*2026-07-12T16:15:31.084039+00:00* · phase: project-hygiene

Audited the whole project tree for stale sidecars/agent-toolset leftovers. Result: NO foreign agent-tool folders (.cursor/.aider/.continue/etc.), no Mac/editor cruft, no duplicate onboarding docs. Found ONE predecessor toolset -- .scaffold (the sidecar that preceded .useful-helpers) -- removed from disk but with dangling LIVE config references. Repointed them to the current sidecar: .gitignore (.scaffold/ -> .useful-helpers/) and pyproject.toml black+ruff extend-exclude (.scaffold -> .useful-helpers). Left historical .scaffold mentions in DEVELOPMENT_LOG and the dogfood report untouched (accurate history). Cleaned 168 stale sidecar artifacts (test_tmp + __pycache__) via the sidecar's own artifact_cleaner. Verified: Forge black/ruff over '.' now process 159 files (sidecar excluded, else its 69+ style issues would flag); Forge 532 tests pass; sidecar smoke 49 pass. Project is clean and ready for further development.

**Files:** ../.gitignore (.scaffold/ -> .useful-helpers/), ../pyproject.toml (black + ruff extend-exclude -> .useful-helpers), .useful-helpers/_artifacts/test_tmp/* (168 items removed)

**Decisions:**
- Repoint stale predecessor-toolset (.scaffold) config to the current sidecar rather than delete it: the .gitignore/pyproject excludes exist to keep the sidecar out of the project's VCS and lint/format, which is exactly the 'project ignorant of sidecar' principle -- they were just aimed at the dead toolset.
- Leave .scaffold mentions in docs (DEVELOPMENT_LOG, reports) and old .forge context bundles as-is: they are historical record, not live config.


## #6 · PARKED 2026-07-12 - end of day; sidecar commit gated on path sanitization  `6603d7ac8ca7`  [parked]
*2026-07-12T19:10:41.638013+00:00* · phase: parking

Parking the project for the day. State: Forge is a verified functional prototype (532 tests; deterministic + local-Ollama AI pipelines; web workbench). The .useful-helpers sidecar is fully integrated and project-aware; sidecar smoke 49 pass. Hygiene done: no foreign agent-tool folders; predecessor toolset .scaffold's dead config refs repointed to .useful-helpers in .gitignore + pyproject; test cruft cleaned. DECISION: user wants .useful-helpers committed to a PUBLIC GitHub showcase repo to display the working process, but only once path-privacy is clean. Privacy scan: secret_audit=0; journal+evidence DBs clean; LEAKS = absolute <project>\... paths in event_log.sqlite3 (12, from logged tool args), _artifacts/test_tmp/* test DBs, and the project's .claude/launch.json. Per user rule (privacy concern -> defer+park): .useful-helpers/ stays gitignored for now; backburner task spawned to relativize paths then enable a clean commit. RESUME: run sanitization task task_2c56454b, then un-gitignore .useful-helpers/.

**Files:** SPAWNED task_2c56454b - sanitize sidecar paths, then allow commit, ../.gitignore (.useful-helpers/ intentionally still excluded until sanitized)

**Decisions:**
- Commit sidecar to public showcase repo -> YES, gated on removing absolute-path leaks (event_log + _artifacts + launch.json).
- Keep .useful-helpers/ gitignored until sanitization lands; clean showcase content (journal/evidence/code/docs) commits, runtime state scrubbed or excluded.


## #7 · PARKED 2026-07-12 (2) - sidecar sanitized + un-gitignored; safe for showcase commit  `782ffd7ac243`  [parked]
*2026-07-12T19:54:12.004610+00:00* · phase: parking

Performed the path sanitization/scrub and enabled the sidecar for commit, then parking again. Actions: (1) relativized event-log error logging (src/core/event_log.py _relativize strips SUITE_PROJECT_ROOT/SUITE_HOME -> <project>/<toolkit>); (2) scrubbed absolute paths out of app_journal + evidence, reset the gitignored event_log; (3) exported JOURNAL.md as the clean, committable human-readable working-history mirror (DBs stay gitignored as *.sqlite3); (4) fixed the project .claude/launch.json FORGE_WEB_ROOT abs path -> '.'; (5) gitignored .forge/ (Forge runtime artifacts embedded absolute paths); (6) removed the .useful-helpers/ exclusion from the project .gitignore so the sidecar commits (its own .gitignore keeps *.sqlite3/_artifacts/logs out). VERIFIED: none of the user's paths (<project>, <user-home>) appear anywhere in the committable surface; JOURNAL.md clean; sidecar smoke 49 pass; Forge 532 pass. OPEN (not user privacy, flagged for user): the upstream author path <upstream-root> remains in docs/development/DEVELOPMENT_LOG.md line ~1005 (historical record) - left as-is pending a decision. Superseded backburner task task_2c56454b (work done inline).

**Files:** src/core/event_log.py (relativize error logging), ../.gitignore (.forge/ ignored; .useful-helpers/ un-ignored + comment), ../.claude/launch.json (FORGE_WEB_ROOT -> '.'), _docs/_AppJOURNAL/JOURNAL.md (clean committable working-history mirror)

**Decisions:**
- Commit the sidecar now: committable surface is clean of the user's machine paths; runtime state (DBs, _artifacts, logs) stays gitignored; JOURNAL.md carries the readable history.
- Gitignore .forge/ (Forge runtime artifacts) - regenerable and embeds absolute paths.
- Leave the single upstream-author path in DEVELOPMENT_LOG as historical record; flag for user.


## #8 · T1 done — live web activity monitor (agent/UI action feed)  `56aef8170b8a`  [closed]
*2026-07-13T00:42:55.309870+00:00* · phase: observability

Built the watch-layer first tranche. New forge/web/activity.py (in-process async bus: history ring-buffer + SSE subscribers, params truncated for display). app.py: a single http middleware taps every /api/* call (reads body with receive-replay so routes are unaffected), records {source, action, params-with-values, ok, status, duration}, and a GET /api/activity/stream SSE endpoint. base.html: a global collapsible 'Activity' panel (bottom-right) that EventSource-subscribes and renders actions live with dedupe-on-reconnect. Because every UI button is a fetch()->/api, this one tap sees human clicks AND agent-driven-UI clicks uniformly. VALIDATED live: drove the Worksets Suggest button; the panel showed 'WEB POST worksets/suggest ok 219ms query="policy guarded apply gate"'. 532 tests pass, ruff+black clean, 0 console errors. Known scope: taps the web seam only — CLI/agent-direct actions appear once T2 unifies at the service layer. Dev server live on 127.0.0.1:8000.

**Files:** forge/web/activity.py (new — action bus + SSE fan-out), forge/web/app.py (/api tap middleware + /api/activity/stream), forge/web/templates/base.html (global Activity panel + SSE client)


## #9 · Audit A2 done — broke the planning import cycle  `5efa0c67888a`  [closed]
*2026-07-13T01:20:34.129519+00:00* · phase: forge-audit-remediation

First remediation from the sidecar-driven Forge audit (docs/development/FORGE_AUDIT.md). import_graph found 2 cycles: planning.planner <-> services.planning_service (+ via planning.store). Root cause: the planning DOMAIN's planner.py held a service-delegating generate_plan() shim (deferred import at planner.py:48, protecting against re-entrant forge.planning.__init__), while service+store imported the domain types (ImplementationPlan, PlannerError) back FROM planner -> static cycle. Fix: moved the pure domain types to new forge/planning/models.py; planner.py re-exports them (public API intact) and keeps the safe deferred shim; planning_service.py and planning/store.py now import the types from models. Result: import_graph cycles 2 -> 0, 532 tests pass, ruff+black clean. Low risk, no behavior change. Next audit items: A1 (vendor CDN JS lucide+marked for offline local-first — needs a download decision), A3 (tests around patch hunk-header realignment), A4 (decompose 2670-line cli/app.py).

**Files:** forge/planning/models.py (new — ImplementationPlan, PlannerError), forge/planning/planner.py (re-export types; keep deferred shim), forge/services/planning_service.py + forge/planning/store.py (import types from models), docs/development/FORGE_AUDIT.md (findings + remediation plan; F2 marked resolved)


## #10 · Audit A1+A3 done — offline-safe UI + patch-diagnostic tests  `69d097f6395a`  [closed]
*2026-07-13T01:46:16.969256+00:00* · phase: forge-audit-remediation

A1 (F3, offline local-first): vendored the two CDN libraries locally — downloaded lucide.min.js (v1.24.0, 411KB, from unpkg) and marked.min.js (v15.0.12, 40KB, from jsdelivr) into forge/web/static/vendor/, repointed base.html + planning.html to /static/vendor/. Verified in browser: 0 requests to unpkg/jsdelivr, both load from localhost (200), lucide global present, 37 icons render, marked present on /planning, no console errors. The web UI is now fully offline-capable. A3 (F4, patch reliability): realign_patch_hunk_headers was already well-covered (8 tests), but verify_patch_context (2nd-biggest complexity hotspot) had ZERO tests — added 5: clean-patch, line-numbered context mismatch, missing-file, past-EOF, and multi-file attribution. This de-risks the diagnostic that will feed the repair loop when a small model produces a bad diff (T5). Full suite 532 -> 537 pass, ruff+black clean. Remaining audit items: A4 (decompose 2670-line cli/app.py), A5 (triage/prune confirmed-dead symbols), A6 (Forge layering policy for domain_boundary_audit).

**Files:** forge/web/static/vendor/{lucide,marked}.min.js (vendored), forge/web/templates/base.html + planning.html (local script srcs), tests/test_patches.py (+5 verify_patch_context tests), docs/development/FORGE_AUDIT.md (F3,F4 resolved; A1,A3 done)


## #11 · Audit A4 in progress — cli/app.py decomposition (7/12 sub-apps, -24%)  `22990fdf70ab`  [open]
*2026-07-13T11:18:41.018627+00:00* · phase: forge-audit-remediation

Decomposing the 2670-line forge/cli/app.py monolith (audit F1) into per-group modules under forge/cli/commands/, behind the existing Typer app, zero behavior change, full suite green after each slice. Created forge/cli/_shared.py for shared helpers (console, _table, _running, _help_with_examples, _add_command_examples, _join_values, _config_manager, _model_manager, error handlers). Decentralized the former central _install_command_examples registry: each module now attaches its own command examples. Extracted so far (7/12 sub-apps): git, config, models, decision, investigation, patch, policy. app.py 2670 -> 2021 lines (-24%). 537 tests pass throughout. One gotcha handled: tests that monkeypatch 'forge.cli.app._model_manager' must repoint to the new module namespace (fixed models/config smoke tests). Remaining: sub-apps repo, project, memory, workset, workflow; then decide whether to also extract the top-level commands (version/doctor/verify/ask/plan/implement/apply + their render helpers) or leave them as app.py's core.

**Files:** forge/cli/_shared.py (new — shared CLI helpers), forge/cli/commands/{git,config,models,decision,investigation,patch,policy}.py (new), forge/cli/app.py (thin assembler; imports sub-apps), tests/test_cli.py (repointed 2 monkeypatch targets)


## #12 · Field report for the sidecar developer written (_docs/INTEGRATION_FIELD_REPORT.md)  `815cd1884115`  [closed]
*2026-07-13T12:05:34.599425+00:00* · phase: sidecar-feedback

Wrote a granular integration field report for whoever builds the sidecar, at _docs/INTEGRATION_FIELD_REPORT.md. Thesis: the sidecar is too specific/opinionated to be a general instrument and must become more flexible. Sections: (A) every modification I made to the sidecar (toolkit-home exclusion, sidecar_install source fix, artifact routing to SUITE_HOME, workspace_audit/artifact_catalog default roots, event_log path relativization, AGENTS.md onboarding, smoke-suite self-scoping) with context/why/effect/limitations; (B) capabilities the sidecar did NOT provide, forcing external tools (run project CLI/tests/lint -> Bash; web UI verify -> Browser MCP; general git inspect -> native git; download/vendor -> curl; sqlite writes -> python sqlite3) — the sidecar can understand/remember but not execute the project; (C) design-philosophy false positives (domain_boundary_audit flags intended cli/web->services layering; dead_code flags Typer commands as dead; blocking_call_scan ignores sync/async context; the original workspace-boundary 'I am the project' model; self-lint debt); (D) recommendations (policies over verdicts, framework-awareness, one roots contract, execute-the-project verbs, central path scrubber, declare each tool's subject); (E) outstanding limitations.

**Files:** _docs/INTEGRATION_FIELD_REPORT.md (new — meta-feedback for the sidecar builder)


## #13 · Field report expanded: Part F (tool workflows) + Part G (graph-of-graphs prosthetic RAG spec)  `9936ba2882af`  [closed]
*2026-07-13T12:12:08.295344+00:00* · phase: sidecar-feedback

Expanded _docs/INTEGRATION_FIELD_REPORT.md per the owner's request for verbosity, specificity, and a focus on the RAG. Added Part F (functional tool-driving workflows the docs omit): the governed-seam JSON-escaping reality and the python+json.dumps subprocess wrapper; the dry-run-first confirm flag whose NAME varies per tool (confirm/write/dry_run:false); how to point tools at the work target (boundary-guarded vs path-based); the understand+audit tool-chain in order with a trust rating per tool (deterministic structural tools = high signal; dead_code/blocking/boundary = leads to verify by hand); the bd-graph build->status->query->project loop; the journal/evidence path-token discipline (avoid JOURNAL.md leaks); and the browser verification loop. Added Part G (the priority): a full build spec to turn bd-graph into a plug-in prosthetic RAG an agent attaches to and instantly knows the project — node surfaces table, the sub-graphs + n-ary hypergraph spine, real local embeddings (nomic-embed-text/all-minilm via Ollama replacing the sha256 stub), LLM summary/keywords/intent surfaces, a symbol/reference graph, unifying journal+evidence as knowledge nodes (the 'why' layer), a 6-verb MCP attach API (attach/query/project/expand/why/neighbors), the macro<->micro zoom workflow, incremental CAS reindex, a build-order table (Ga real embeddings -> Gb line ranges -> Ge why-links first), and an acceptance definition of 'optimal'.

**Files:** _docs/INTEGRATION_FIELD_REPORT.md (added Part F + Part G)


## #14 · Sidecar re-vended in update mode to v1.1.0  `9aff14fa9945`  [closed]
*2026-07-14T13:01:34.244792+00:00* · phase: sidecar-maintenance

Overlay-updated <project>/.useful-helpers from the repaired Useful Helpers source using sidecar_install update mode. Existing runtime memory was preserved; no clean overwrite was performed.

**Files:** .useful-helpers/, .useful-helpers/VERSION, .useful-helpers/_docs/_AppJOURNAL/JOURNAL.md

**Decisions:**
- Used update:true and overwrite:false to preserve runtime memory.
- Disabled gitignore update because <project> intentionally commits the sidecar for showcase history.
- Verified journal entries and evidence items remained present after the overlay.

**Backlog:**
- Installed-sidecar smoke currently has one git_inspect test assumption: it expects the sidecar folder itself to be a git repository, while Forge tracks the sidecar from the parent repo.


## #15 · Codex onboarding checkpoint — Forge baseline stable after sidecar orientation  `ca36ab912457`  [open]
*2026-07-14T13:13:54.274713+00:00* · phase: forge-onboarding

Read sidecar AGENTS/README/ONBOARDING/TOOLS/ARCHITECTURE/OPERATIONS, inspected prior journal. Found current continuation point is A4 CLI decomposition: previous entry says 7/12 sub-apps extracted, and fresh scan shows repo.py has also been extracted. Fresh sidecar scans show Forge has 141 Python modules, 0 import cycles, 0 secret findings, and cli/app.py remains the main hotspot at 1894 lines / 49 symbols. Test baseline is stable when using <project>/.venv: 537 passed in 29.58s. Global python fails collection because structlog is absent, so commands should use the project venv or run.bat setup path.

**Files:** .useful-helpers/AGENTS.md, .useful-helpers/_docs/TOOLS.md, .useful-helpers/_docs/OPERATIONS.md, docs/development/FORGE_AUDIT.md, forge/cli/app.py, forge/cli/commands/repo.py, pyproject.toml, run.bat

**Decisions:**
- Treat .useful-helpers as the current sidecar name; .helper-scripts was not present in <project>.
- Do not modify Forge code until continuing A4 with a narrow move-and-test slice.
- Use <project>/.venv/Scripts/python for tests, not global python.

**Backlog:**
- Continue A4 by extracting project, memory, workset, and workflow command groups from forge/cli/app.py into forge/cli/commands/.
- After each extracted group, run targeted CLI tests and then full .venv pytest.
- Update journal entry 11 or close it once A4 is finished.


## #16 · Sidecar fix log opened — event_log reader, smoke temp root, git_inspect worktree detection  `70bfc71772bb`  [closed]
*2026-07-14T13:37:09.626713+00:00* · phase: sidecar-maintenance

Opened a running sidecar-only fix log before modifying the toolkit. Current issues to fix for builder handoff: (1) tools/event_log/cli.py reads event_log.sqlite3 from Path.cwd()/_docs while the writer stores under SUITE_HOME/toolkit home, so sidecar installs report an empty ledger even when the DB has rows. (2) tests/test_smoke.py uses tempfile.mkdtemp() directly in several tests; in managed workspaces this resolves to host temp outside writable roots and causes permission failures. (3) tools/git_inspect/cli.py rejects valid Git subdirectories because it requires repo/.git to exist; .useful-helpers is tracked by the parent Forge repo, so Git works but the tool preflight fails.

**Files:** .useful-helpers/tools/event_log/cli.py, .useful-helpers/tools/git_inspect/cli.py, .useful-helpers/tests/test_smoke.py

**Decisions:**
- Fix sidecar internals first because the user explicitly requested toolkit repair before Forge A4.
- Keep this repair log inside the sidecar journal/evidence only.

**Backlog:**
- Change event_log reader to use suite_home() unless SUITE_EVENT_LOG_DB overrides it.
- Make smoke tests use sidecar-local _artifacts/test_tmp as Python tempfile.tempdir.
- Change git_inspect repository validation to use git rev-parse --is-inside-work-tree.
- Run focused tests, then smoke with a writable temp root if needed.


## #17 · A4 slice — project command group extracted from forge/cli/app.py  `5dae780caaf4`  [closed]
*2026-07-14T13:48:06.727262+00:00* · phase: forge-audit-remediation

Continued A4 CLI decomposition after sidecar repair. Extracted the project sub-app (project root/info/paths plus examples) from forge/cli/app.py into forge/cli/commands/project.py, following the existing Forge command-module pattern. app.py now imports project_app and mounts it with app.add_typer; no sidecar logic was imported into Forge. Behavior target: pure move, zero CLI behavior change.

**Files:** forge/cli/app.py, forge/cli/commands/project.py

**Decisions:**
- Use original Forge/Typer command code moved into a native Forge module; do not reuse sidecar code in Forge.
- Keep init and web as top-level app commands for now; this slice only extracts the project sub-app.

**Backlog:**
- Continue A4 with memory command group extraction.
- Then extract workset command group.
- Then extract workflow command group.
- After A4 sub-apps, decide whether to extract top-level plan/implement/apply/verify/ask/web/init commands or leave them as app.py core.


## #18 · A4 slice - memory command group extracted from forge/cli/app.py  `7d6f8e73b60b`  [closed]
*2026-07-14T13:53:16.121621+00:00*

Extracted the Forge memory CLI group into forge/cli/commands/memory.py, mounted it from forge/cli/app.py, and removed stale app.py imports. Verified with tests/test_memory.py and the full Forge pytest suite.

**Files:** forge/cli/app.py, forge/cli/commands/memory.py

**Decisions:**
- Keep the extraction behavior-preserving and native to Forge; do not copy or import sidecar code into Forge.

**Backlog:**
- Continue A4 with workset and workflow command groups, then assess remaining top-level commands for extraction.


## #19 · A4 slice - workset command group extracted from forge/cli/app.py  `50cda0975634`  [closed]
*2026-07-14T13:56:04.390950+00:00*

Extracted the Forge workset CLI group into forge/cli/commands/workset.py, mounted it from forge/cli/app.py, and moved workset command examples with the module. Verified with workset-focused tests and the full Forge pytest suite.

**Files:** forge/cli/app.py, forge/cli/commands/workset.py

**Decisions:**
- Keep the CLI decomposition behavior-preserving and Forge-native; sidecar remains an instrument only.

**Backlog:**
- Continue A4 with workflow command extraction, then reassess remaining top-level commands.


## #20 · A4 slice - workflow command group extracted from forge/cli/app.py  `a4c688ba946f`  [closed]
*2026-07-14T13:58:09.750095+00:00*

Extracted the Forge workflow CLI group and helper render/run functions into forge/cli/commands/workflow.py, mounted it from forge/cli/app.py, and moved workflow command examples with the module. Verified with workflow tests and the full Forge pytest suite.

**Files:** forge/cli/app.py, forge/cli/commands/workflow.py

**Decisions:**
- Move workflow helpers with the workflow commands so the module owns its CLI behavior end to end.

**Backlog:**
- Assess whether remaining top-level commands should stay central or be extracted into focused modules.


## #21 · A4 slice - top-level pipeline commands extracted from forge/cli/app.py  `1de38715b852`  [closed]
*2026-07-14T14:13:42.073301+00:00*

Extracted top-level Forge pipeline commands verify, plan, plan-list, implement, and apply into forge/cli/commands/pipeline.py behind register_pipeline_commands(app). Kept forge.cli.app.verification_service and app-level model-manager lookup compatibility for existing tests while moving command logic out of the central CLI file. Verified targeted pipeline tests, full Forge suite, and git diff whitespace check.

**Files:** forge/cli/app.py, forge/cli/commands/pipeline.py

**Decisions:**
- Use a registration function for top-level commands because they are not a Typer sub-app.
- Preserve existing test monkeypatch seams while reducing central CLI ownership.

**Backlog:**
- Next CLI cleanup candidates: extract ask/explain-project into an AI/context command module and init/web into small app lifecycle modules if desired.


## #22 · A4 optional cleanup - AI context and lifecycle commands extracted  `d73f4435cf79`  [closed]
*2026-07-14T14:21:10.242553+00:00*

Extracted remaining top-level CLI command bodies for ask, explain-project, init, and web into Forge-native command modules. forge/cli/app.py is now a thin CLI composition root plus compatibility aliases for existing model-manager and verification monkeypatch seams. Verified targeted CLI/project/web tests, full Forge suite, diff whitespace check, and compileall over forge/cli.

**Files:** forge/cli/app.py, forge/cli/commands/ai_context.py, forge/cli/commands/lifecycle.py

**Decisions:**
- Keep app-level _model_manager and verification_service aliases for compatibility while moving command behavior into modules.
- Use register_*_commands(app) for top-level commands that are not Typer sub-apps.

**Backlog:**
- Prepare park-phase documentation: sidecar fixes, A4 CLI decomposition, verification evidence, remaining Forge stabilization plan.


## #23 · PARKED 2026-07-14 - Forge rescue checkpoint documented  `07517096f28f`  [parked]
*2026-07-14T14:45:57.955486+00:00* · phase: parking

Documented and parked the current Forge rescue checkpoint. Added docs/development/PARK_2026-07-14.md, updated docs/development/FORGE_AUDIT.md to mark A4 resolved, and appended a pointer entry to docs/development/DEVELOPMENT_LOG.md. State at park: sidecar fixes logged, A4 CLI decomposition complete including optional cleanup, full Forge suite green, whitespace check clean except existing CRLF warnings, temp test root absent.

**Files:** docs/development/PARK_2026-07-14.md, docs/development/FORGE_AUDIT.md, docs/development/DEVELOPMENT_LOG.md

**Decisions:**
- Park at a stable documentation checkpoint before beginning A5 or product hardening work.
- Keep sidecar-builder fix details in sidecar journal/evidence; project park doc records Forge-facing state and resume plan.

**Backlog:**
- Resume with A5 dead-code triage or package the full rescue report for review.
- Continue product hardening with patch reliability and local Ollama API/control UI after documentation review.


## #24 · A5 dead-code triage opened  `052e1a5f6290`  [closed]
*2026-07-15T01:30:36.890297+00:00* · phase: forge-audit-remediation

Reran the sidecar dead_code lens after A4. Current scan: 148 Forge modules, 792 symbols, 66 candidates; most are recognized framework entrypoints. Manually triaging high-confidence top-level candidates and low-confidence methods before any deletion.


## #25 · Sidecar feedback from A5 dead-code triage  `e8b7dea82d5e`  [closed]
*2026-07-15T01:36:09.836613+00:00* · phase: sidecar-feedback

Forge A5 exposed three dead_code lens limitations: aliased imports are not credited to source definitions; global simple-name matching can hide dead definitions behind unrelated methods; narrowed source scans cannot see test-only public contracts. Builder should consider qualified symbol resolution, alias tracking, and separate definition/reference roots or explicit scope reporting.

**Files:** tools/dead_code/cli.py, tools/code_intel_shared.py

**Backlog:**
- Track imported aliases to original symbols
- Resolve references by qualified scope instead of global simple name
- Support reference roots or clearly report excluded test scope


## #26 · Post-A5 rescue transformation review opened  `686386f427a9`  [parked]
*2026-07-15T02:54:30.753168+00:00* · phase: forge-audit-remediation

Reviewing A1-A5 as a coherent unit for behavioral bugs, fragile compatibility seams, separation-of-concern regressions, and missing tests. Scope includes planning, CLI decomposition, web local-first changes, patch diagnostics, and A5 removals.


## #27 · A6 Forge-aware boundary policy opened  `08d8f8d3200a`  [parked]
*2026-07-15T08:23:23.878419+00:00* · phase: forge-audit-remediation

Implementing a Forge-specific layering policy for domain_boundary_audit, with tool-level regression coverage, governed baseline/post-change scans, and separation from Forge runtime code.

**Files:** .useful-helpers/tools/domain_boundary_audit/cli.py, .useful-helpers/tools/domain_boundary_audit/tool.json, .useful-helpers/tests/test_smoke.py

**Backlog:**
- Define policy from observed Forge architecture
- Preserve generic tool behavior
- Validate findings against current Forge imports
- Document and park A6


## #28 · Sidecar feedback from A6 dependency bootstrap  `7b88813b731a`  [closed]
*2026-07-15T08:37:24.560845+00:00* · phase: sidecar-feedback

The full 60-test smoke suite failed before A6 verification because requirements.txt declares pypdf but the documented shared root .venv did not contain it after re-vend. Installed pypdf 6.14.2 manually into the root venv. The installer/update path should reconcile sidecar requirements or the smoke suite should emit a targeted dependency diagnostic instead of failing mid-test.

**Files:** requirements.txt, tests/test_smoke.py

**Decisions:**
- Do not add pypdf to Forge project metadata; keep it an environment dependency of the detachable sidecar.

**Backlog:**
- Builder: install or reconcile sidecar requirements during install/update mode
- Builder: add a preflight dependency check before PDF smoke tests


## #29 · Live visible-browser workflow regression test  `41e5fffc7674`  [open]
*2026-07-15T09:25:02.136610+00:00* · phase: post-A6 stabilization

Started Forge feature workflow cac1fb317d6a47e0 from the visible in-app browser for request tracing. Repository, workset, and context completed; planning failed after 306.4 seconds because Ollama qwen3.5:35b timed out at 300 seconds. The generated context was 609826 characters / 152446 estimated tokens and the model request logged 511256 prompt characters / 127814 estimated tokens. The async web route invoked the synchronous workflow engine inline, blocking all HTTP responses and leaving the UI frozen at Starting until completion.

**Decisions:**
- Use an unapplied workflow run as the browser visibility regression test.
- Treat the run as diagnostic evidence; do not change Forge configuration during the test.

**Backlog:**
- Move workflow execution off the request/event-loop path and return a run ID immediately.
- Expose live stage progress in the workflow UI.
- Reconcile dashboard model display with the actual role/default model used by workflows.
- Bound workset/context and planner prompt budgets before local inference.
- Add a workflow-selectable model or role-based model control surface.


## #30 · Planned bounded context and multiresolution evidence graph  `7cdc921ade51`  [open]
*2026-07-15T09:57:43.441066+00:00* · phase: post-A6 stabilization

Implementation plan derived from live workflow cac1fb317d6a47e0. Immediate recovery: classify and suppress minified/vendor candidates, enforce a final rendered prompt budget for every planning call, compact workflow artifact descriptors, expose effective role models, and dispatch web workflows to a single background worker with atomic status persistence and live polling. Strategic increment: add a Forge-native CAS plus SQLite evidence graph, deterministic syntax-aware occurrences and typed edges, hybrid bounded retrieval, lazy model-derived summary surfaces, and staged plan-DAG generation. The exact request-tracing workflow is the acceptance fixture.

**Decisions:**
- Restore a successful bounded planning stage before introducing graph persistence.
- Keep repository enumeration, workset selection, context compilation, evidence persistence, planning generation, workflow lifecycle, and web presentation in their existing ownership layers.
- Use filesystem CAS plus SQLite metadata, FTS, nodes, edges, occurrences, and derivations; do not add a graph server.
- Preserve verbatim content and provenance as authoritative; model summaries are derived, versioned, cached surfaces.
- Use deterministic parsing first and optional small-model summarization only behind an explicit model slot.
- Return HTTP 202 with a persisted pending run and execute web workflows in one background worker while preserving synchronous CLI behavior.
- Forge must not import or depend on the Useful Helpers sidecar.

**Backlog:**
- P0 add the failed-run fixture and prompt telemetry assertions.
- P1 exclude or demote minified/vendor/generated assets and add byte/token-aware chunks.
- P1 add an always-on final prompt compiler budget, starting at 12000 estimated input tokens with output reserve.
- P1 compact context and workflow records to artifact descriptors instead of embedding complete rendered bundles.
- P1 show effective planning and execution models and set the planning acceptance environment to qwen3.5:9b.
- P1 split workflow creation from execution, add atomic registry writes, one background worker, HTTP 202, and detail-page polling.
- P2 add Forge evidence models, CAS object storage, SQLite occurrence/node/edge/surface schema, and incremental indexing.
- P2 add lexical, path, symbol, and bounded typed-edge retrieval with provenance and token costs.
- P3 add lazy multiresolution summaries with explicit summarization model role and hash-based invalidation.
- P3 generate validated plan-step DAG records through bounded scope, evidence-gap, per-step, and rendering passes.
- Run focused tests, full Forge tests, sidecar boundary/blocking scans, and a visible live replay of the request-tracing workflow.


## #31 · Sidecar smoke_runner rediscovers generated artifacts and times out  `e4a598b3cdb6`  [open]
*2026-07-15T10:26:32.984632+00:00* · phase: sidecar-builder-feedback

During Forge rescue validation, governed smoke_runner with default arguments scanned .useful-helpers/_artifacts/test_tmp, executed eight generated smoke fixtures, then timed out after 30 seconds on .useful-helpers/smoke_test.py. Discovery should exclude SUITE_HOME artifact and runtime directories and distinguish the sidecar pytest suite from project smoke_test.py scripts.

**Files:** .useful-helpers/tools/smoke_runner/cli.py, .useful-helpers/tools/smoke_runner/tool.json

**Decisions:**
- Do not change Forge to accommodate this sidecar-only discovery defect.
- Validate the canonical sidecar pytest suite directly for this run.

**Backlog:**
- Exclude _artifacts, runtime memory, and generated test_tmp trees from smoke discovery.
- Provide an explicit toolkit self-test mode or target contract that runs tests/test_smoke.py without invoking long-lived smoke_test.py entrypoints.


## #32 · Updated sidecar Forge boundary profile for evidence domain  `bdf90b76a46b`  [parked]
*2026-07-15T10:28:15.131837+00:00* · phase: sidecar-project-adaptation

The A6 bounded-evidence implementation introduced forge/evidence as a Forge domain package. The sidecar-owned Forge boundary profile did not map that domain and therefore fabricated seven violations. Added evidence: domain to the profile; rerun reduced the audit from eight violations to the one pre-existing planning compatibility-shim exception, with zero unmapped domains.

**Files:** .useful-helpers/config/domain-boundary/forge.json

**Decisions:**
- Classify Forge evidence storage and retrieval as a domain package.
- Keep the existing planning.planner compatibility-shim violation visible rather than weakening the global layer policy.

**Backlog:**
- Builder may consider profile inheritance or an explicit project-domain extension mechanism so new legitimate domains can be added without editing a vendored profile.


## #33 · Semantic gating and verification-baseline plan checkpoint  `15593a5f5906`  [parked]
*2026-07-15T14:21:47.344857+00:00* · phase: post-A6 stabilization

Paused Forge rescue after reviewing the anchored-edit checkpoint and the follow-up architectural report. The latest isolated implementation attempt mechanically accepted an unapplied patch for the request-ID feature after three anchored repair turns, but semantic review found unreachable middleware logic, exclusion of /api/activity, a function-scoped import, and tests that did not prove uniqueness. Confirmed plan: add narrow Forge-native semantic gates plus task-specific acceptance contracts; feed deterministic findings into anchored repair; execute focused tests in an exact dirty-tree verification snapshot; persist model responses, edits, diagnostics, and verification as a traversable evidence graph; remove hardcoded sidecar identity later through a generic exclusion contract. PostgreSQL migration is explicitly deferred. Keep qwen3.5:9b for implementation and evaluate Phi3:mini-128k only as a controlled planning experiment. No patch was applied, no workflow replay was performed, and no further implementation work is authorized until resume.

**Files:** forge/execution/execution_prompt.py, forge/patches/anchored_edits.py, forge/services/implementation_service.py, forge/workflows/engine.py, forge/evidence/store.py, forge/repository/ignore.py, pyproject.toml, .forge/patches/20260715T130929Z-add-an-x-forge-request-id-response-header-for-every-api-requ.patch

**Decisions:**
- Mechanical patch acceptance is not semantic acceptance.
- Use task-specific acceptance contracts alongside narrow AST and structural checks.
- Never execute generated code during static validation.
- Use an explicit Forge-owned dirty-tree snapshot instead of relying blindly on git stash create.
- Run focused dynamic verification only after static gates pass.
- Persist raw responses and deterministic derived surfaces as evidence graph nodes and edges.
- Defer PostgreSQL migration until a real deployment or concurrency requirement justifies it.
- Keep qwen3.5:9b as the implementation model; reserve Phi3:mini-128k for a controlled planning experiment.
- Keep the Useful Helpers sidecar detachable and out of Forge runtime dependencies.

**Backlog:**
- Implement narrow semantic validation for syntax, changed control-flow reachability, scoped imports, and task-required test evidence.
- Compile explicit acceptance contracts from plan requirements and use them in semantic and dynamic gates.
- Route semantic findings and focused test failures through the anchored repair loop.
- Design and test an exact dirty-tree verification snapshot covering staged, unstaged, untracked, deleted, and ignored files.
- Persist response, edit, diagnostic, repair, and verification nodes with provenance edges.
- Replace hardcoded .useful-helpers exclusions with a generic external-tool exclusion contract.
- Run the Phi3 planning comparison after the planning path is bounded and observable.
- Run focused tests, the full Forge suite, restart the server, and replay the request-tracing workflow visibly.
- Write the final rescue report and sidecar builder feedback after the transformations are complete.


## #34 · Opened Forge orchestration-spine implementation  `f20416814205`  [open]
*2026-07-16T04:04:32.275471+00:00* · phase: forge-orchestration-spine

Documented the ten-phase Forge-native requirement-to-verified-patch plan and captured a fresh baseline. The request-ID workflow remains the vertical acceptance fixture. External custom systems and the Useful Helpers sidecar are design evidence and editing instruments only; no code, names, schemas, prompts, or runtime dependencies will be copied into Forge.

**Files:** docs/development/ORCHESTRATION_SPINE_PLAN_2026-07-15.md, docs/development/DEVELOPMENT_LOG.md

**Decisions:**
- Implement and review one gated phase at a time.
- Keep generated patches unapplied.
- Use deterministic extraction before model inference.
- Keep qwen3.5:9b as implementation model while Phi-3 is evaluated only for planning.
- Defer PostgreSQL and graph-server infrastructure.

**Backlog:**
- Phase 1 acceptance contracts
- Phase 2 durable tasks
- Phase 3 evidence dossiers
- Phase 4 role routing
- Phase 5 structured edits
- Phase 6 semantic gates
- Phase 7 exact snapshots
- Phase 8 targeted repair
- Phase 9 visible proof
- Phase 10 boundary closure and report


## #35 · Phase 1 complete - Forge acceptance contracts  `f91135282441`  [closed]
*2026-07-16T04:19:27.205955+00:00* · phase: forge-orchestration-spine

Implemented the Forge-native acceptance contract domain, deterministic compiler, validation, application-service boundary, canonical workflow persistence, prompt propagation into planning/implementation/anchored repair, and a visible contract stage. Phase review removed duplicated contract truth, restored service ownership, and cleaned scoped lint findings.

**Files:** forge/acceptance/__init__.py, forge/acceptance/contract.py, forge/services/acceptance_service.py, forge/workflows/models.py, forge/workflows/engine.py, forge/workflows/templates.py, forge/planning/prompts.py, forge/services/planning_service.py, forge/execution/execution_prompt.py, forge/services/implementation_service.py, forge/web/templates/workflow_detail.html, tests/test_acceptance_contract.py

**Decisions:**
- Persist one canonical full contract on WorkflowRun.
- Keep artifact-map contract data descriptor-only to avoid drift.
- Compile a conservative contract for standalone planning and implementation calls.
- Treat criterion status as unverified until later gates attach evidence.

**Backlog:**
- Phase 2 durable task records
- Phase 3 evidence-aware contract refinement
- Phase 6 criterion evaluation
- Phase 8 repair evidence


## #36 · Completed orchestration spine Phase 2 durable tasks  `2a3343ca2393`  [closed]
*2026-07-16T04:31:24.399771+00:00* · phase: orchestration-spine-phase-2

Evolved workflow stages into durable task records with explicit dependencies, compact inputs and outputs, retry policy, model role, token budget, typed failure categories, evidence references, and timestamped per-attempt history. Dependency failures and every attempt transition are atomically persisted; interrupted recovery and the workflow UI expose the new record while remaining compatible with old JSON. Review repaired the attempt-history and immediate dependency-save gaps. Verification: 74 workflow/web tests and 609 full-suite tests passed; scoped Ruff and compileall passed.

**Files:** forge/workflows/models.py, forge/workflows/engine.py, forge/workflows/registry.py, forge/web/templates/workflow_detail.html, tests/test_workflow.py, docs/development/ORCHESTRATION_SPINE_PLAN_2026-07-15.md, docs/development/DEVELOPMENT_LOG.md

**Decisions:**
- Extend WorkflowStage compatibly instead of replacing it.
- Keep authoritative large content out of workflow JSON; task records carry compact descriptors.
- Keep outer workflow retries distinct from implementation candidate repair.
- Persist each retry attempt as an independently inspectable outcome.

**Backlog:**
- Populate task evidence references from the Phase 3 dossier.
- Persist bounded patch candidates and targeted repair context in Phase 8.


## #37 · Completed orchestration spine Phase 3 evidence dossiers  `1087157d01d2`  [closed]
*2026-07-16T05:07:22.599518+00:00* · phase: orchestration-spine-phase-3

Implemented a Forge-native deterministic evidence dossier over Forge's existing CAS and SQLite graph. The durable evidence task stores exact source/test windows plus AST-derived routes, imports, symbols, Git state, provenance, token cost, and criterion links; planning receives bounded exact windows while implementation receives compact structural facts. Review repaired token-level source/test starvation, syntax-invalid source loss, a package re-export cycle risk, broad boilerplate ranking, workset/test affinity, and qualified preservation-call routing. The real failed request-ID workset now selects _install_activity_monitor and the activity-preservation API test in a 3,195/3,200-token dossier. Verification: 161 focused and 617 full-suite tests passed; Ruff and Black passed.

**Files:** forge/evidence/dossier.py, forge/evidence/models.py, forge/evidence/indexer.py, forge/services/evidence_service.py, forge/services/planning_service.py, forge/services/implementation_service.py, forge/execution/execution_prompt.py, forge/workflows/engine.py, forge/workflows/models.py, forge/workflows/templates.py, forge/web/templates/workflow_detail.html, tests/test_evidence_dossier.py, tests/test_evidence_graph.py, tests/test_workflow.py, docs/development/ORCHESTRATION_SPINE_PLAN_2026-07-15.md, docs/development/DEVELOPMENT_LOG.md

**Decisions:**
- Use Forge's existing CAS and SQLite evidence graph instead of introducing a new database or graph runtime.
- Persist only compact dossier descriptors in workflow JSON; exact bytes remain in CAS.
- Reserve one source and one test window before supplemental evidence.
- Treat criterion evidence links as grounding only; satisfaction remains unverified.
- Use workset rank and qualified-call preservation bridges to complement lexical task matching.

**Backlog:**
- Sidecar builder feedback: CLI JSON arguments hit Windows command-line limits for large new-file edits; add stdin or args-file support, or a governed chunked-write verb.
- Sidecar builder feedback: indentation-aware patch replacement can reflow a deliberately top-level replacement under the matched block; improve top-level intent controls or diagnostics.
- Phase 4 must persist independent planning/execution model-role telemetry.
- Phase 6 must convert grounding links into criterion-specific gate verdicts.
- Phase 7 must replace informational Git state with a materializable exact snapshot.


## #38 · Forge orchestration spine Phase 4 complete  `663b9d5eb4fa`  [closed]
*2026-07-16T06:41:08.005974+00:00* · phase: Phase 4 model roles and planner experiment

Added durable role-specific model selection, provider usage telemetry, bounded Ollama lifecycle controls, CAS/graph-backed same-dossier planner comparisons, partial-failure retention, and immutable scorer re-projection. The fair request-ID experiment retained Qwen 3.5 9B as planner without changing configuration. Phase regressions: 104 passed; full Forge suite: 631 passed.

**Files:** forge/models/types.py, forge/models/manager.py, forge/models/ollama.py, forge/models/telemetry.py, forge/config/manager.py, forge/planning/comparison.py, forge/services/planner_comparison_service.py, forge/services/planning_service.py, forge/services/implementation_service.py, forge/cli/commands/models.py, tests/test_planner_comparison.py, docs/development/ORCHESTRATION_SPINE_PLAN_2026-07-15.md, docs/development/DEVELOPMENT_LOG.md

**Decisions:**
- Keep qwen3.5:9b for planning, execution, and repair; do not promote Phi or a 35B MoE.
- Treat model summaries and scores as derived surfaces; preserve prompts and raw responses in CAS.
- Use scorer versioning and supersession rather than rewriting prior comparison evidence.
- Require explicit prompt/output/context budgets and immediate model unload for sequential local comparisons.

**Backlog:**
- Sidecar sqlite_inspect rejects ../.forge/evidence/index.sqlite3 as outside the project workspace even though project-aware tools define the sidecar parent as the work target.
- Sidecar patch indentation inference can re-indent an intended top-level replacement under the matched block; several top-level additions required repair with regex edit. Add an explicit indentation mode or preserve-exact option and clearer diagnostics.
- Sidecar CLI JSON transport remains awkward for large structured edits; stdin or args-file support would reduce command-length/escaping failures.


## #39 · Orchestration Spine Phase 5 - Structured Edit IR  `50da0fd56ff9`  [closed]
*2026-07-16T07:18:08.098476+00:00* · phase: Phase 5

Implemented and reviewed Forge-native structured anchored-edit IR, deterministic immutable-source compilation, machine-readable dry-run diagnostics, overlap and authorization gates, hunk provenance, prompt authority, and implementation telemetry. Legacy anchored JSON remains compatible; raw repair diffs are retained but explicitly marked untraceable. Focused 50, broader 156, full 641 passed.

**Files:** forge/patches/edit_ir.py, forge/patches/anchored_edits.py, forge/patches/__init__.py, forge/execution/execution_prompt.py, forge/services/implementation_service.py, tests/test_anchored_edits.py, tests/test_implement.py, docs/development/ORCHESTRATION_SPINE_PLAN_2026-07-15.md, docs/development/DEVELOPMENT_LOG.md

**Decisions:**
- Resolve every operation against immutable original bytes and apply accepted spans in descending source order.
- Require schema-1 provenance while adapting the legacy path/old/new JSON shape.
- Keep legacy raw repair diffs temporarily, but label them traceable=false rather than treating them as structured IR.
- Do not infer criterion satisfaction from edit metadata; Phase 6 owns semantic acceptance.
- Use no external patch dependency and retain complete Forge runtime independence from the sidecar.

**Backlog:**
- Sidecar patch still infers indentation from the search location and repeatedly indents intended top-level definitions or replacement blocks incorrectly; regex edit plus Black is still required.
- Sidecar CLI JSON transport remains fragile and laborious for multiline source edits because PowerShell, JSON, regex, and replacement escaping stack together.
- Sidecar sqlite_inspect project-root contract issue from the prior phase remains open.


## #40 · Forge orchestration spine Phase 6: narrow semantic gates  `2aae164ad6cc`  [closed]
*2026-07-16T08:03:05.266016+00:00* · phase: Phase 6

Implemented, reviewed, verified, documented, and parked Forge-native in-memory patch materialization plus static semantic and contract-to-test gates. The retained request-ID candidate is rejected by four precise criterion-linked findings. Full Forge suite: 666 passed.

**Files:** forge/patches/materialize.py, forge/verification/semantic.py, forge/verification/semantic_models.py, forge/services/semantic_validation_service.py, forge/services/implementation_service.py, forge/workflows/engine.py, forge/workflows/models.py, forge/workflows/templates.py, forge/web/templates/workflow_detail.html, tests/test_patch_materialization.py, tests/test_semantic_validation.py, tests/test_workflow.py, tests/test_implement.py, tests/test_web.py, docs/development/ORCHESTRATION_SPINE_PLAN_2026-07-15.md, docs/development/DEVELOPMENT_LOG.md

**Decisions:**
- Keep static validation non-executing: parse generated Python with ast.parse only and never import, eval, exec, or compile it.
- Require contract-specific observable lineage for multi-observation properties; two operations alone are not semantic evidence.
- Use lexical dominance and executable leaf statements for all-path coverage rather than source-line ordering.
- Authorize semantic targets from the post-grounding implementation result so explicit new-file requests remain possible without broadening initial selection.
- Keep Python static rules in one private cohesive module while retaining separate materialization, report model, application service, and workflow concerns.
- Phase 7 must verify an exact snapshot of analyzed bytes before semantic success can become an acceptance verdict.

**Backlog:**
- Sidecar edit uses regular-expression replacement-template semantics even when users expect literal replacement; a replacement containing \\b was silently converted into backspace bytes. Treat replacement literally by default or require an explicit template mode, and reject unexpected control characters.
- Sidecar patch indentation inference remains fragile for top-level and multiline replacements; preserve replacement indentation by default or expose a reliable literal-indentation mode.
- The sidecar-owned Forge domain-boundary profile is stale: it does not map the Forge acceptance domain and now reports 26 false policy violations. Add acceptance to the profile and consider profile/version drift diagnostics.
- Sidecar domain_boundary_audit emits very large full crossing payloads for routine policy checks; add a bounded summary/findings-only output mode so successful automation does not exhaust response budgets.
- The previously recorded sqlite_inspect project-root contract issue remains open.


## #41 · Orchestration Spine Phase 7 - Exact Analyzed-Tree Verification  `349ef9869cc2`  [closed]
*2026-07-16T12:09:31.876745+00:00* · phase: phase-7

Implemented and reviewed Forge-native exact source snapshots. Planning and implementation now retain raw-byte source identities; a durable snapshot stage captures Git-visible committed, indexed, staged, unstaged, untracked, and deleted state into CAS; structural, semantic, and dynamic verification run only in isolated materializations. The clean-HEAD fallback is removed. Real dirty-tree snapshot snap-15493765d3e7ac62 captured 252 files / 12,426,321 bytes and materialized with matching content identity and cleanup.

**Files:** forge/repository/source_state.py, forge/git/models.py, forge/git/service.py, forge/context/bundle.py, forge/planning/prompts.py, forge/services/planning_service.py, forge/services/implementation_service.py, forge/verification/snapshot.py, forge/services/snapshot_service.py, forge/patches/materialize.py, forge/project/paths.py, forge/services/patch_service.py, forge/services/semantic_validation_service.py, forge/verification/service.py, forge/services/verification_service.py, forge/workflows/models.py, forge/workflows/templates.py, forge/workflows/engine.py, forge/web/templates/workflow_detail.html, tests/test_source_snapshot.py, tests/test_patch_materialization.py, tests/test_workflow.py, tests/test_dogfood_hardening.py, tests/test_web.py, docs/development/ORCHESTRATION_SPINE_PLAN_2026-07-15.md, docs/development/DEVELOPMENT_LOG.md

**Decisions:**
- Capture the live Git-visible filesystem after patch generation and prove model-visible source hashes match it.
- Do not use git stash or a clean-HEAD worktree; snapshot through NUL-safe Git observation and immutable CAS objects.
- Fail closed on drift, unsupported source entries, unsafe paths, tampered objects/manifests, and failed materialization.
- Run structural, semantic, and dynamic gates against separate materializations of one immutable snapshot.
- Preserve LF/CRLF byte identity and reject mixed newlines rather than silently normalize.

**Backlog:**
- Phase 8: bounded criterion-specific repair with complete gate replay per candidate.
- Phase 9: visible request-ID vertical-slice proof.
- Phase 10: replace literal external-tool ignore name with a generic exclusion contract and package final rescue/builder reports.


## #42 · Phase 8 targeted repair implemented and reviewed  `072f282b47fe`  [closed]
*2026-07-16T12:32:44.098232+00:00* · phase: orchestration-spine-phase-8

Added bounded criterion-specific repair over exact source snapshots. Repair retains complete unrelated patch sections, cannot add sections, uses strict anchored-edit allowlists, persists every response/candidate/gate result, and advances only after structural, semantic, and focused executable gates. Workflow now routes semantic findings through visible Targeted Repair before full verification.

**Files:** forge/repair/, forge/services/repair_service.py, forge/patches/composition.py, forge/verification/focused.py, forge/verification/executor.py, forge/verification/service.py, forge/services/verification_service.py, forge/workflows/engine.py, forge/workflows/models.py, forge/workflows/templates.py, forge/web/templates/workflow_detail.html, tests/test_targeted_repair.py, tests/test_workflow.py, docs/development/ORCHESTRATION_SPINE_PLAN_2026-07-15.md

**Decisions:**
- Repair is a bounded inner candidate loop with a maximum of three model calls.
- Every repair anchors against the immutable original snapshot and replaces only existing complete file sections.
- Candidate acceptance order is structural, semantic, then focused execution; final workflow verification remains full.
- Raw command output stays in dedicated verification reports; workflow and attempt records retain compact summaries.

**Backlog:**
- Phase 9 must run fixture-based Phase 8 regressions and the full suite when host execution approval is available.
- Replay the visible request-ID workflow and prove API coverage, uniqueness, activity preservation, and unapplied retention.

