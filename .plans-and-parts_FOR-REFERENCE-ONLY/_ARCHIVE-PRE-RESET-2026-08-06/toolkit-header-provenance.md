# Toolkit Header Provenance (captured before stripping)

`STATUS:` and `TRANCHE:` values as they stood on 2026-08-06, before
`TRANCHE:` and `STATUS: DONE` were removed from source headers.
These belong to the toolkit's own build chronology, not this project's.

| File | STATUS | TRANCHE |
| --- | --- | --- |
| `toolkit/apps/projectmapper/cli.py` | DONE | T7 |
| `toolkit/src/__init__.py` | SCAFFOLD | T2 |
| `toolkit/src/app.py` | DONE   (cli | mcp | ui live; ui-probe = bounded GUI verification) | T3 (cli|mcp) + T-gov (governed seam) + T6 (ui) |
| `toolkit/src/core/__init__.py` | SCAFFOLD | T2 |
| `toolkit/src/core/config.py` | DONE | T3 |
| `toolkit/src/core/docs.py` | DONE | T5 (REGENERATE) |
| `toolkit/src/core/event_log.py` | DONE | T-gov (slice 1) |
| `toolkit/src/core/invoke.py` | DONE | T3 (dispatch) + T-gov (event log) |
| `toolkit/src/core/playbook.py` | DONE | T-compose |
| `toolkit/src/core/policy.py` | DONE | T-gov (slice 2) |
| `toolkit/src/core/registry.py` | DONE | T3 |
| `toolkit/src/interfaces/__init__.py` | SCAFFOLD | T2 |
| `toolkit/src/interfaces/cli.py` | DONE | T3 |
| `toolkit/src/interfaces/mcp_server.py` | DONE | T3 |
| `toolkit/src/lib/__init__.py` | SCAFFOLD | T2 |
| `toolkit/src/lib/common.py` | DONE | T3 (+ T-roots scrubber) |
| `toolkit/src/lib/logging_setup.py` | DONE | T3 (+ T-roots scrubber) |
| `toolkit/src/lib/theme.py` | DONE | T6 |
| `toolkit/src/ui/__init__.py` | DONE | T6 |
| `toolkit/src/ui/app_ui.py` | DONE | T6 |
| `toolkit/src/ui/installer_view.py` | DONE | T-vend |
| `toolkit/src/ui/mapper_view.py` | DONE | T6-ops (human-experience: bespoke views over governed tools) |
| `toolkit/src/ui/planner_view.py` | DONE | E7 (the cockpit) |
| `toolkit/src/ui/registry_view.py` | DONE | T6 |
| `toolkit/tests/__init__.py` | DONE | T3.5 (smoke suite) |
| `toolkit/tests/test_smoke.py` | DONE | T3.5 |
| `toolkit/tools/__init__.py` | DONE | T4.0 |
| `toolkit/tools/_template/cli.py` | SCAFFOLD | T4.0 (exemplar) |
| `toolkit/tools/_toolkit.py` | DONE | T4.0 |
| `toolkit/tools/agent_interview/cli.py` | DONE | T-prompt-eval |
| `toolkit/tools/app_factory/cli.py` | DONE | T-packaging-more |
| `toolkit/tools/artifact_catalog/cli.py` | DONE | T-packaging-core |
| `toolkit/tools/artifact_cleaner/cli.py` | DONE | T-ops-apply |
| `toolkit/tools/attach/cli.py` | SKELETON | T-attach (walking skeleton) |
| `toolkit/tools/bd_emit/cli.py` | DONE | T-bd-graph |
| `toolkit/tools/bd_graph_shared.py` | DONE | T-bd-graph |
| `toolkit/tools/bd_index/cli.py` | DONE | T-bd-graph |
| `toolkit/tools/bd_knowledge/cli.py` | DONE | T6 / Ge (the "why" layer) |
| `toolkit/tools/bd_project/cli.py` | DONE | T-bd-graph |
| `toolkit/tools/bd_query/cli.py` | DONE | T-bd-graph |
| `toolkit/tools/bd_scribe/cli.py` | DONE | T-bd-graph |
| `toolkit/tools/bd_split/cli.py` | DONE | T-bd-graph |
| `toolkit/tools/bd_status/cli.py` | DONE | T-bd-graph |
| `toolkit/tools/bd_why/cli.py` | DONE | T6 / Ge (the "why" layer) |
| `toolkit/tools/blocking_call_scan/cli.py` | DONE | T-code-intel |
| `toolkit/tools/code_intel_shared.py` | DONE | T-code-intel |
| `toolkit/tools/codebase_bundle/cli.py` | DONE | T-packaging-more |
| `toolkit/tools/command_profile/cli.py` | DONE | T-operational-audit |
| `toolkit/tools/complexity_score/cli.py` | DONE | T-code-intel |
| `toolkit/tools/constraint_build/cli.py` | DONE | T-prompt-eval |
| `toolkit/tools/constraint_query/cli.py` | DONE | T-prompt-eval |
| `toolkit/tools/dead_code/cli.py` | DONE | D2 / G6 (was T-code-intel heuristic; rebuilt on the graph) |
| `toolkit/tools/delegate/cli.py` | DONE | C7 (the compute payoff: a cheap local model does the grunt work  -  search, read, |
| `toolkit/tools/dep_install/cli.py` | DONE | C5 (seam-completeness: reviving a real project used to require leaving the seam) |
| `toolkit/tools/dependency_check/cli.py` | DONE | T-operational-audit |
| `toolkit/tools/dev_server_manager/cli.py` | DONE | T-ops-server |
| `toolkit/tools/diff/cli.py` | DONE | C4 (only schema_diff/snapshot_diff existed; this is the general text diff) |
| `toolkit/tools/domain_boundary_audit/cli.py` | DONE | T-code-intel-more |
| `toolkit/tools/edit/cli.py` | DONE | T-mine + C3 (field report New F1: literal + expected-count guards) |
| `toolkit/tools/embed_shared.py` | DONE | T6 / Ga (real embeddings) |
| `toolkit/tools/event_log/cli.py` | DONE | T-gov (slice 1) |
| `toolkit/tools/evidence/cli.py` | DONE | T-evidence |
| `toolkit/tools/fetch/cli.py` | DONE | T-operate (field report B5  -  vendoring a library needed curl outside the seam; |
| `toolkit/tools/file_tree/cli.py` | DONE | T4 (stamped by tools/stamp, then implemented) |
| `toolkit/tools/fs_op/cli.py` | DONE | C3 (mutation verbs) |
| `toolkit/tools/genesis/cli.py` | DONE | E3 / genesis (Start-New first-class) |
| `toolkit/tools/git/cli.py` | DONE | T5 |
| `toolkit/tools/git_inspect/cli.py` | DONE | T-operate (field report B4  -  a careful, privacy-gated commit needs ls-files/ |
| `toolkit/tools/glob/cli.py` | DONE | C1 (the hands) |
| `toolkit/tools/host_probe/cli.py` | DONE | T4 (envelope via T4.0 tools._toolkit) |
| `toolkit/tools/http_probe/cli.py` | DONE | T-operate (field report B2/B3  -  most local-server verification needs only an |
| `toolkit/tools/import_graph/cli.py` | DONE | T-code-intel |
| `toolkit/tools/journal/cli.py` | DONE | T-journal |
| `toolkit/tools/linenumber/cli.py` | DONE | T-mine (batch) |
| `toolkit/tools/llm_shared.py` | DONE | D1 / O1 (route local inference through one governed seam) |
| `toolkit/tools/memory_flush/cli.py` | DONE | T-memory-workflow |
| `toolkit/tools/memory_workflow_shared.py` | DONE | T-memory-workflow |
| `toolkit/tools/model_benchmark/cli.py` | DONE | T-prompt-eval |
| `toolkit/tools/module_decomp_plan/cli.py` | DONE | T-code-intel-more |
| `toolkit/tools/ollama_gov/cli.py` | DONE | T-mine (batch) |
| `toolkit/tools/operation/cli.py` | DONE | E4 / recovery |
| `toolkit/tools/operations_shared.py` | DONE | E4 / recovery (recovery as normal operation) |
| `toolkit/tools/packaging_more_shared.py` | DONE | T-packaging-more |
| `toolkit/tools/patch/cli.py` | DONE | T8 |
| `toolkit/tools/pdf_compress/cli.py` | DONE | T-doc-pdf |
| `toolkit/tools/pdf_extract/cli.py` | DONE | T-doc-pdf |
| `toolkit/tools/pdf_info/cli.py` | DONE | T-doc-pdf |
| `toolkit/tools/pdf_interleave/cli.py` | DONE | T-doc-pdf |
| `toolkit/tools/pdf_merge/cli.py` | DONE | T-doc-pdf |
| `toolkit/tools/pdf_rotate/cli.py` | DONE | T-doc-pdf |
| `toolkit/tools/pdf_shared.py` | DONE | T-doc-pdf |
| `toolkit/tools/pdf_split/cli.py` | DONE | T-doc-pdf |
| `toolkit/tools/pdf_thumbnails/cli.py` | DONE | T-doc-pdf |
| `toolkit/tools/ping/cli.py` | DONE | T3 (retrofit T4.0 onto tools._toolkit) |
| `toolkit/tools/plan/cli.py` | DONE | E6 / planner engine (engine before cockpit) |
| `toolkit/tools/process_port_inspector/cli.py` | DONE | T-ops-apply |
| `toolkit/tools/project_run/cli.py` | DONE | T-operate + C2 (the keystone: arbitrary execution through the seam, so `Bash` never |
| `toolkit/tools/prompt_case_builder/cli.py` | DONE | T-prompt-eval |
| `toolkit/tools/prompt_diff_report/cli.py` | DONE | T-prompt-eval |
| `toolkit/tools/prompt_eval/cli.py` | DONE | T-prompt-eval |
| `toolkit/tools/prompt_eval_shared.py` | DONE | T-prompt-eval |
| `toolkit/tools/prompt_rubric_judge/cli.py` | DONE | T-prompt-eval |
| `toolkit/tools/provenance/cli.py` | DONE | E5 / formation provenance |
| `toolkit/tools/provenance_shared.py` | DONE | E5 / formation provenance |
| `toolkit/tools/rag_retrieve/cli.py` | DONE | T-memory-workflow |
| `toolkit/tools/read_file/cli.py` | DONE | C1 (the hands) |
| `toolkit/tools/repo_search/cli.py` | DONE | T-operational-audit |
| `toolkit/tools/report/cli.py` | DONE | T-mine (batch) |
| `toolkit/tools/rules_eval/cli.py` | DONE | T-memory-workflow |
| `toolkit/tools/scaffold_project/cli.py` | DONE | E1 / scaffold (new-project materializer) |
| `toolkit/tools/scaffold_shared.py` | DONE | E1 / scaffold (new-project materializer) |
| `toolkit/tools/schema_diff/cli.py` | DONE | T-operational-audit |
| `toolkit/tools/secret_audit/cli.py` | DONE | T-operational-audit |
| `toolkit/tools/semantic_chunk/cli.py` | DONE | T-memory-workflow |
| `toolkit/tools/session_record/cli.py` | DONE | T-memory-workflow |
| `toolkit/tools/session_replay/cli.py` | DONE | T-memory-workflow |
| `toolkit/tools/sidecar_install/cli.py` | DONE | T-vend (make the toolkit installable) |
| `toolkit/tools/smoke_runner/cli.py` | DONE | T-ops-apply |
| `toolkit/tools/snapshot_diff/cli.py` | DONE | T-packaging-core |
| `toolkit/tools/snapshot_verify/cli.py` | DONE | T-packaging-core |
| `toolkit/tools/sqlite_exec/cli.py` | DONE | C4 (field report B6: sqlite_inspect was read-only; data-curation and state scrubbing |
| `toolkit/tools/sqlite_inspect/cli.py` | DONE | T-operational-audit |
| `toolkit/tools/stamp/cli.py` | DONE | T4.0 |
| `toolkit/tools/summarize_shared.py` | DONE | T6 / Gf (attach returns purpose) |
| `toolkit/tools/symbol_graph/cli.py` | DONE | D2 / G6+G5 (symbol graph + node summaries) |
| `toolkit/tools/symbol_graph_shared.py` | DONE | D2 / G6 (symbol graph) |
| `toolkit/tools/tempserver/cli.py` | DONE | T-packaging-more |
| `toolkit/tools/test_scaffold/cli.py` | DONE | T-code-intel-more |
| `toolkit/tools/tkinter_widget_tree/cli.py` | DONE | T-code-intel |
| `toolkit/tools/ui_callback_graph/cli.py` | DONE | T-code-intel-more |
| `toolkit/tools/vendor_export/cli.py` | DONE | T-packaging-core |
| `toolkit/tools/web_search/cli.py` | DONE | C6 (seam-completeness: discovery was the last verb outside the seam) |
| `toolkit/tools/workflow_decompose/cli.py` | DONE | T-memory-workflow |
| `toolkit/tools/workflow_templates/cli.py` | DONE | T-memory-workflow |
| `toolkit/tools/workspace_audit/cli.py` | DONE | T-operational-audit |
| `toolkit/tools/write_file/cli.py` | DONE | C1 (the hands) |
