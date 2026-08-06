<!-- GENERATED FILE - do not edit by hand.
     Regenerate with:  python -m src.app cli docs-refresh
     Source of truth:  tools/*/tool.json (via config/registry.json).
     The smoke suite asserts this file matches the registry, so edits here are reverted. -->

# Tools - the capability catalog

95 tools, grouped by category. Generated from the registry; **what** each tool does is here, **how to drive them** (sequencing, flags, trust) is in [OPERATIONS.md](OPERATIONS.md).

Authority: `Observe` read-only | `Sandbox` temp/artifacts only | `Apply` writes for real. `writes` declares what a tool may touch (`none`/`toolkit`/`target`); the seam enforces it for Observe tools (see [ARCHITECTURE.md](ARCHITECTURE.md)).

## orientation  (4)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `attach` | Observe | toolkit | project | target, domain, refresh, scope | THE front door. Re-engage an already-mapped target, or map a new one. Returns a PROJECT_MAP, the mounted workbench, and the next steps. |
| `genesis` | Apply | toolkit | project | **intent**, name, authority, profile, overwrite, apply | THE 'Start New' front door. Begin a project from an INTENTION (not existing code): record a durable workspace identity + intent + authority and seed the first journal entry. No domain required. |
| `operation` | Apply | toolkit | project | action, op_id, title, goal, steps, tool, args_hash, status, +7 more | Recovery ledger: make a multi-step effort durable and RESUMABLE across crashes. Start/advance/pause/resume with explicit failure classes; resume re-observes the target first and reports drift (stale_witness) rather than continuing onto a changed world. |
| `plan` | Apply | target | project | action, intent, name, map, archetype, root, op_id, overwrite, +1 more | The planner engine: turn an intention + a project map into a real, governed project. Runs genesis -> scaffold -> provenance -> journal as ONE resumable operation; preview-first, idempotent, and the built structure traces back to the intent. |

## introspection  (13)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `command_profile` | Observe | none | project | root | Detect likely setup/test/run/build/dev commands from project files. |
| `dependency_check` | Observe | none | project | root | Check dependency declaration and runtime readiness without installing anything. |
| `diff` | Observe | none | project | a, b, a_text, b_text, context, from_label, to_label | Unified diff between two files (paths within the roots) or inline texts; reports the diff plus added/removed line counts. |
| `file_tree` | Observe | none | project | root, kind, ext, limit, ignore | Snapshot the project file tree (dirs/files) with kind/ext filters and ignore pruning. |
| `glob` | Observe | none | project | **pattern**, root, limit, include_all | Match files by glob pattern (supports ** recursion), pruning noise and the toolkit home by default. |
| `host_probe` | Observe | none | toolkit | - | Probe Python version, platform, and common developer-tool availability (git, node, docker, ...). |
| `ping` | Observe | none | toolkit | message | Echo a message and report the runtime the control plane invoked the tool under. |
| `process_port_inspector` | Observe | none | toolkit | ports, process_name_contains, timeout_seconds, max_processes, max_ports | Read-only inspection of relevant running processes and occupied/listening ports. |
| `read_file` | Observe | none | project | **path**, offset, limit, max_bytes | Read a file's contents (optionally a 1-based line range), byte-capped, within the work target or toolkit home. |
| `repo_search` | Observe | none | project | root, **query**, glob, limit, case_sensitive | Structured repository text search with rg fast path and Python fallback. |
| `schema_diff` | Observe | none | project | **left**, **right** | Compare two SQLite schemas: added/removed tables, columns, and indexes. |
| `sqlite_inspect` | Observe | none | project | **db**, include_samples, sample_limit | Inspect SQLite schema, tables, indexes, counts, and optional sample rows. |
| `workspace_audit` | Observe | none | toolkit | root | Audit workspace boundaries, donor/runtime folders, and control-plane surfaces. |

## code-intel  (10)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `blocking_call_scan` | Observe | none | project | root, max_files, limit | Blocking-call scanner: findings are calls whose nearest enclosing function is async def (can stall the event loop); sync-context calls are informational. |
| `complexity_score` | Observe | none | project | root, max_files, limit | Rank Python functions/classes/modules by simple AST complexity and size hotspots. |
| `dead_code` | Observe | none | project | root, max_files, limit, include_private, entrypoint_decorators | Unused-symbol candidates proven by reachability over the RESOLVED symbol graph - dead clusters and name coincidences included - with an honesty ledger bounding the proof. |
| `domain_boundary_audit` | Observe | none | project | root, max_files, allowed_edges, policy, policy_profile | Report imports crossing top-level domain boundaries, from the resolved symbol graph (relative imports anchored to their real package). Policy comes from the project; without one, crossings are neutral facts. |
| `import_graph` | Observe | none | project | root, max_files, cycle_limit | Build a Python import graph with internal edges, external roots, fan-in/fan-out, and cycles. |
| `module_decomp_plan` | Observe | none | project | root, max_files, limit | Propose Python module decomposition candidates from size, symbols, imports, and complexity cues. |
| `symbol_graph` | Observe | toolkit | project | action, root, symbol, limit, max_files, max_nodes | Resolved symbol graph: who actually defines and refers to whom (bound through imports, not name coincidence), plus CAS-cached one-line module summaries - with an honesty ledger of what static analysis cannot see. |
| `test_scaffold` | Apply | toolkit | project | **path**, framework, module, out, write, overwrite | Generate preview-first unittest/pytest starter tests for a Python module; writes only with write:true. |
| `tkinter_widget_tree` | Observe | none | project | root, max_files | Extract Tkinter/ttk windows, widgets, layout/config calls, commands, and binds without launching UI. |
| `ui_callback_graph` | Observe | none | project | root, max_files | Extract Tkinter command/bind event handlers and conservative function call edges without launching UI. |

## memory  (1)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `provenance` | Apply | toolkit | project | action, subject, relation, object, origin, verb, participants, op_id, +5 more | Formation provenance: record WHY an artifact exists (typed relations with an enforced origin - discovered \| operational \| interpretive), including multi-participant activities, and TRACE any artifact back to the chain that formed it. |

## packaging  (9)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `app_factory` | Apply | toolkit | toolkit | action, template, name, destination, dry_run, confirm, overwrite | List, preview, or stamp small starter app skeletons. |
| `artifact_catalog` | Observe | none | toolkit | root, limit, hash, max_hash_bytes | Catalog generated workspace artifacts by path, kind, size, and optional hash. |
| `codebase_bundle` | Apply | toolkit | project | root, out_dir, formats, include, exclude, max_bytes, include_binaries, limit, +3 more | Create AI-friendly codebase report, JSONL, and AST bundle artifacts. |
| `scaffold_project` | Apply | target | project | action, archetype, map, root, overwrite, apply | Materialize a NEW project from a contract map: create the directories, write the files (boilerplate or documented stubs with FILE/ROLE/DOES headers), and emit PROJECT_PLAN.md. Preview-first; one apply for the whole batch. |
| `sidecar_install` | Apply | toolkit | toolkit | **target**, folder, dry_run, confirm, overwrite, update | Dry-run-first installer: copy a clean-app view of the toolkit into an external project's .useful-helpers/ sidecar. Writes exactly one directory and nothing else  -  the target is never modified. |
| `snapshot_diff` | Observe | none | toolkit | **left**, **right**, limit | Compare two ProjectMapper snapshots by captured file paths and content hashes. |
| `snapshot_verify` | Observe | none | toolkit | **snapshot**, db, sha256, manifest | Verify a ProjectMapper SQLite snapshot, sidecar sha256, manifest JSON, schema, and row-count metadata. |
| `tempserver` | Apply | toolkit | project | root, name, out_dir, port, include, exclude, max_bytes, limit, +3 more | Build a self-contained static project viewer and return a ready-to-run serve command. |
| `vendor_export` | Apply | toolkit | toolkit | root, name, out_root, dry_run, confirm, overwrite, zip, exclude_paths, +2 more | Dry-run-first clean export folder/zip creator excluding donors, git state, caches, artifacts, and local DBs. |

## prompt-eval  (8)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `agent_interview` | Observe | none | project | goal, role, constraints, answers, limit | Build a structured interview script for evaluating agent behavior and supplied answers. |
| `constraint_build` | Observe | none | project | text, path, paths, prefix | Extract stable constraint statements from text or workspace-local docs. |
| `constraint_query` | Observe | none | project | constraints, text, path, paths, query, tags, severity, limit | Filter extracted constraints by query terms, tags, and severity. |
| `model_benchmark` | Observe | none | toolkit | suite, suite_path, suite_name, responses, constraints, limit | Load benchmark cases and either emit a run plan or evaluate supplied responses. |
| `prompt_case_builder` | Apply | toolkit | project | prompt, scenario, constraints, id, label, probe_type, write, out, +1 more | Build deterministic benchmark/training case JSON from a scenario and constraints. |
| `prompt_diff_report` | Observe | none | project | baseline, candidate, baseline_path, candidate_path, required_terms, forbidden_terms | Compare baseline and candidate prompts/responses and report changed terms and risks. |
| `prompt_eval` | Observe | none | project | cases, suite, suite_path, suite_name, responses, response, constraints, limit | Score supplied responses across benchmark/training cases and aggregate results. |
| `prompt_rubric_judge` | Observe | none | project | **response**, case, rubric, constraints | Score a supplied response against deterministic case checks, rubric checks, and constraints. |

## pdf  (8)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `pdf_compress` | Apply | toolkit | project | **path**, out, dry_run, confirm | Rewrite a PDF with compressed content streams; dry-run-first and confirm-gated. |
| `pdf_extract` | Apply | toolkit | project | **path**, pages, mode, write, out, password | Extract selected PDF pages to PDF or text; writes only with write:true. |
| `pdf_info` | Observe | none | project | **path**, password, limit | Report PDF page count, metadata, page boxes, rotations, and file size. |
| `pdf_interleave` | Apply | toolkit | project | **a**, **b**, first, second, out, reverse_second, dry_run, confirm | Alternate pages from two PDFs; dry-run-first and confirm-gated. |
| `pdf_merge` | Apply | toolkit | project | **files**, out, dry_run, confirm | Merge PDFs into one output; dry-run-first and confirm-gated. |
| `pdf_rotate` | Apply | toolkit | project | **path**, pages, degrees, out, dry_run, confirm | Rotate selected PDF pages by 90-degree increments; dry-run-first and confirm-gated. |
| `pdf_split` | Apply | toolkit | project | **path**, max_pages, out_dir, dry_run, confirm, password | Split a PDF into page-count chunks; dry-run-first and confirm-gated. |
| `pdf_thumbnails` | Apply | toolkit | project | **path**, pages, limit, write, confirm, out_dir, zoom | Plan thumbnail pages and optionally render PNGs when PyMuPDF is installed. |

## analysis  (1)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `report` | Observe | none | project | path | Structural logical-analysis of Python code (file or tree): purpose, classes/methods, functions, imports. |

## bd-graph  (9)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `bd_emit` | Observe | none | project | hunks, hunks_path, dimensions, limit | Emit deterministic HyperNode-like records from HyperHunk-like input. |
| `bd_index` | Apply | toolkit | project | path, root, db, max_size, max_files, dimensions, limit, dry_run, +1 more | Run split -> emit -> scribe for a workspace-local source into a BD graph DB. |
| `bd_knowledge` | Apply | toolkit | project | db, journal_db, evidence_db, link_cap, dry_run, confirm, apply | Ingest journal + evidence into the BD graph as knowledge nodes linked to the code they reference (the 'why' layer). Preview-first. |
| `bd_project` | Observe | none | project | db, occurrence_id, occurrence_ids, hops, include_content | Project a neighborhood from a BD graph DB around one or more occurrence IDs. |
| `bd_query` | Observe | none | project | db, **query**, top_k, hops | Find lexical/vector anchors in a BD graph DB and return a projected subgraph. |
| `bd_scribe` | Apply | toolkit | project | action, db, nodes, nodes_path, dry_run, confirm | Dry-run-first ingestion of emitted BD nodes into a workspace-local SQLite graph DB. |
| `bd_split` | Observe | none | project | path, root, text, origin_id, max_size, max_files, limit | Split workspace-local text/code into deterministic HyperHunk-like records. |
| `bd_status` | Observe | none | project | db | Report table presence and counts for a workspace-local BD graph SQLite DB. |
| `bd_why` | Observe | none | project | db, **target**, limit | From a code path or symbol, return the linked knowledge (journal decisions + evidence)  -  the 'why' behind the code. |

## cleanup  (1)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `artifact_cleaner` | Apply | toolkit | toolkit | root, dry_run, confirm, allow_tracked, include_patterns, max_candidates | Dry-run-first cleanup of allowlisted generated runtime artifacts with tracked-file protection. |

## curation  (1)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `projectmapper` | Apply | toolkit | project | action, **root**, name, out, max_bytes, exclude, exclude_paths, respect_gitignore, +3 more | Scan a project tree into a portable, self-describing SQLite snapshot (+ manifest, .sha256, optional Markdown). |

## evidence  (1)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `evidence` | Apply | toolkit | toolkit | action, kind, summary, body, body_json, source_path, source_line_range, attached_to, +6 more | Bag of Evidence: attach content-addressed, verifiable evidence items (verify re-hashes to detect drift). |

## git  (2)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `git` | Apply | toolkit | project | repo, action, message, allow_no_gitignore | Git: init a repo, status, or add -> commit (-> push), with a .gitignore safety gate. |
| `git_inspect` | Observe | none | project | action, repo, n, path, paths, pattern, ref, cached, +1 more | Read-only git inspection: status, branches, log, ls-files, diff (stat/unified), grep, check-ignore  -  the verbs for reasoning about a repo through the governed seam. |

## governance  (1)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `event_log` | Observe | none | toolkit | action, tool_id, limit | Read the governance event log (audit trail of invoke calls): recent, per-tool summary, one tool's history, or a journal-ready rollup. |

## journal  (1)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `journal` | Apply | toolkit | toolkit | action, title, phase, summary, files, decisions, backlog, status, +4 more | Canonical append-only App Journal (SQLite): add/list/show/close entries, export a Markdown mirror. |

## memory-workflow  (8)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `memory_flush` | Apply | toolkit | toolkit | session, root, out, limit, write | Summarize a session memory log and optionally write a flush artifact. |
| `rag_retrieve` | Observe | none | project | **query**, text, path, paths, chunks, chunks_path, top_k, context | Retrieve relevant context from text, files, or precomputed chunks. |
| `rules_eval` | Observe | none | project | path, content, rules, read | Evaluate proposed content and paths against deterministic safety rules. |
| `semantic_chunk` | Observe | none | project | text, path, paths, filename, chunk_size, overlap | Chunk Python, Markdown, and text into deterministic semantic records. |
| `session_record` | Apply | toolkit | toolkit | action, session, description, role, kind, content, metadata, root, +1 more | Create workspace-local sessions and append JSONL memory events. |
| `session_replay` | Observe | none | toolkit | session, root, role, kind, limit | Replay workspace-local session memory as events and transcript text. |
| `workflow_decompose` | Observe | none | project | goal, text, path, paths, template, template_path, max_steps | Turn a goal, task list, or workflow template into ordered task records. |
| `workflow_templates` | Observe | none | toolkit | action, id, path, variables | List, show, or render deterministic workflow templates. |

## model  (2)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `delegate` | Apply | toolkit | project | **task**, model, allow, max_steps, evidence, apply, allow_apply | Hand a bounded task to a local model that drives the sidecar's own Observe verbs through the governed seam, returning a distilled answer plus the full trail. Offloads grunt work from the calling agent. |
| `ollama_gov` | Sandbox | toolkit | toolkit | action, search, model, prompt, tier, num_ctx, num_predict, temperature, +1 more | Hardware-aware Ollama governor: list safety tiers, list local models, run token-governed inference, and report what local inference has cost. |

## operations  (7)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `dep_install` | Apply | target | project | packages, requirements, venv, create_venv, apply | Governed dependency install behind an HITL batch gate: the dry-run lists the COMPLETE dependency set (with sources and target venv); one apply installs the whole batch. Never installs into the system interpreter. |
| `dev_server_manager` | Apply | toolkit | project | action, root, command_id, confirm, health_url, port, tail_lines, timeout_seconds | Guarded start/status/stop/tail/health management for registered project dev-server commands. |
| `fetch` | Apply | toolkit | project | **url**, dest, max_bytes, timeout_s, allow_remote, dry_run, apply | Dry-run-first governed download: HEAD plan (host/size/type), then apply:true streams URL to a file (default under the toolkit's _artifacts/fetch/), size-capped, sha256-reported. |
| `http_probe` | Observe | none | project | **url**, method, timeout_s, allow_remote | GET/HEAD a URL (localhost by default): status, headers, capped body snippet, elapsed ms  -  server verification through the governed seam, without a browser. |
| `project_run` | Apply | target | project | command, profile, cwd, timeout_s, dry_run, apply, evidence | THE governed executor: run any command (explicit string, or a command_profile id) with cwd confined to the roots, bounded timeout, capped output, and a failure classification. The audited replacement for ad-hoc shell. |
| `sqlite_exec` | Apply | target | project | **db**, **sql**, params, apply | Governed SQLite write (INSERT/UPDATE/DELETE/DDL), parameterized, preview-first via transaction rollback (accurate affected-row count, non-destructive). DB confined to the roots. |
| `web_search` | Apply | toolkit | project | **query**, limit, evidence, apply | Governed web search behind a provider adapter (searxng\|brave\|tavily): preview shows what would be sent where, apply returns normalised {title,url,snippet} results. Audit-logged; never fabricates when unconfigured. |

## scaffold  (1)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `stamp` | Apply | toolkit | toolkit | **id**, kind, summary, category, authority | Generate a new tool/app skeleton (cli.py + tool.json) wired to tools._toolkit. |

## security  (1)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `secret_audit` | Observe | none | project | root, limit | Heuristic redacted scan for obvious committed secrets. |

## testing  (1)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `smoke_runner` | Sandbox | toolkit | toolkit | root, targets, timeout_seconds, stop_on_failure, discovery_limit | Discover or run smoke_test.py files and aggregate pass/fail results. |

## text  (5)

| tool | authority | writes | on | inputs | summary |
|---|---|---|---|---|---|
| `edit` | Apply | target | project | **pattern**, **replacement**, text, path, literal, expected_replacements, write, apply, +4 more | Find/replace on text or a file  -  regex or literal  -  with an expected-count guard; preview by default, writes only with write:true (or apply:true). |
| `fs_op` | Apply | target | project | ops, op, path, dest, apply | Governed filesystem mutation: a BATCH of mkdir/touch/copy/move/delete ops (one plan, one approval). Paths confined to the roots. |
| `linenumber` | Observe | none | project | action, text, path, style, start, width | Annotate text with parseable line numbers, strip them, or emit a line->hash integrity map. |
| `patch` | Apply | toolkit | project | action, patch, patch_json, text, path, write, force_indent | Surgical indentation-aware patching via JSON hunks (search/replace blocks); dry-run validate; preview by default. |
| `write_file` | Apply | target | project | **path**, **content**, overwrite, write, apply | Create or overwrite a file (preview-first). The sanctioned, audited way to write into the work target. |

---
_Generated 2026-07-25 from 95 manifests._
