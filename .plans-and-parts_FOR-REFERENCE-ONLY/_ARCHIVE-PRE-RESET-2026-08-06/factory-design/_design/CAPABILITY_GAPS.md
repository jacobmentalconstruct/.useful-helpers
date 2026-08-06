# Capability Gaps — what the sidecar needs to be an agent's *only* toolset

**Date:** 2026-07-18 · **Status (2026-07-20): RESOLVED.** Every tier landed via
`COMPLETION_PLAN.md` — C1-C8 (the hands, exec, mutation, data, deps, web, delegate; seam 18/18)
D1-D2 (governed inference seam, policy overrides, symbol graph G6, node summaries G5), and D3 (read-only mount: the precept enforced by PREVENTION, not just detection).
Kept as the record of WHY each capability exists. Companion to `CHARTER.md` and `PLAN.md`.

---

## 1. The thesis

Through six phases I built this toolkit almost entirely with my **own** inherited tools — `Read`,
`Write`, `Edit`, `Bash`, `Grep`, `Glob` — not with the sidecar. That is the measurement: **every
time an agent reaches past the sidecar for its own hands, the sidecar has a gap.** And it matters
for two concrete reasons, not just tidiness:

1. **Governance is only as complete as the seam is used.** My hundreds of `Bash` edits and file
   writes bypassed the precept guard, the authority ceiling, and the audit log entirely. On a real
   target, a direct `Bash` write could have violated the precept and **nothing would have caught
   it** — the guard only sees calls that go through `invoke()`. "100% through the sidecar" is the
   *only* state in which the precept and audit trail are actually true.
2. **Compute.** An expensive agent doing mechanical work by hand is the waste. The sidecar already
   saves compute by **distilling** (attach/report/import_graph/bd_query hand me structure instead
   of me reading 20 files) and can **delegate** cognition to a local model (ollama_gov, Gf
   summaries). What it cannot yet do is **offload the mechanical doing** — because it lacks the
   action verbs. So all the doing still routes through me (expensive) and outside the seam.

**Goal:** an agent binds to the sidecar's MCP surface and needs nothing else — read, search, edit,
write, run, orient, remember — every action audit-logged, precept-guarded, reproducible.

## 2. How this session was actually built (tool-by-tool)

| What I did, constantly | My tool | Sidecar equivalent |
|---|---|---|
| Read file contents / line ranges | `Read` | **none** (report/repo_search/sqlite_inspect are partial views, not raw read) |
| Create new files (tools, cartridges, docs, memory) | `Write` | **none** (stamp/app_factory scaffold *skeletons* only) |
| Exact-string edits | `Edit` | `edit` (regex) / `patch` (blocks) — **coarser, riskier** |
| Run python one-liners, pytest, ruff, du/ls/cp/rm/mkdir, sqlite, heredocs | `Bash` | **none for ad-hoc** (`project_run` runs *detected* commands only) |
| Content search | `Grep` | `repo_search` ✓ (I still used my own for speed/integration) |
| Find files by pattern | `Glob` | `file_tree` (partial — filters, not glob patterns) |
| Decisions | `AskUserQuestion` | out of scope (agent's channel) |
| Persist memory | `Write` to memory dir | `journal`/`evidence` ✓ (but I used my own for the factory's `_design`) |

The pattern: **understanding verbs are well covered; the mechanical read/write/run verbs are almost
entirely absent**, so they defaulted to me. This is the field report's Part B thesis, now measured
against a full build.

## 3. The gap list

Legend — **Tier 1**: core "hands," blocks 100%-through-seam. **Tier 2**: important. **Tier 3**:
leverage/ergonomics. **U**: upgrade an existing tool, not a new one.

### Tier 1 — the missing hands (replace Read/Write/Bash/Glob/Edit)

| # | Proposed tool | Replaces | Why it's necessary | Authority / writes |
|---|---|---|---|---|
| 1 | `read_file` | `Read` | Raw file content by path with offset/limit/line-range. The single most-used verb I have; the sidecar has no way to hand an agent a file's contents. | Observe / none |
| 2 | `write_file` | `Write` | Create/overwrite a file with given content, confirm-gated, **precept-aware** (declares `writes: target` and the guard governs it). Today an agent *must* leave the seam to create a file. | Apply / target |
| 3 | `run` (governed exec) | `Bash` | Execute an arbitrary command, confirm-gated, with output captured as `evidence`, precept-guarded, audit-logged. The biggest gap: most of what I did was ad-hoc shell/python. `project_run` only runs *pre-detected* commands. | Apply / target |
| 4 | `fs_op` | `Bash` mkdir/cp/mv/rm/touch | Governed filesystem mutation (make dir, copy, move, delete, touch), confirm-gated, precept-aware. `artifact_cleaner` is allowlisted-delete-only. | Apply / target |
| 5 | `edit` **U** | `Edit` | Add `literal: true` + `expected_replacements` guard (refuse unless the dry-run count matches) + before/after context. Field report New F1: a greedy regex once ate a larger block than intended. | Apply / target |
| 6 | `glob` (or `file_tree` **U**) | `Glob` | Match paths by glob pattern (`**/*.py`), not just ext/kind filters. | Observe / none |

### Tier 2 — data mutation, diffing, dependencies

| # | Proposed tool | Replaces | Why | Authority / writes |
|---|---|---|---|---|
| 7 | `sqlite_exec` | `Bash` python sqlite3 | Parameterized INSERT/UPDATE/DELETE/DDL, confirm-gated. `sqlite_inspect` is read-only (field report B6). Needed for data-curation targets and for scrubbing/migrating state. | Apply / target |
| 8 | `diff` | `Bash` diff | General unified text/file diff. Today only `schema_diff` (sqlite) and `snapshot_diff` (projectmapper) exist. Needed to review a change before/after and to ground evidence. | Observe / none |
| 9 | `dep_install` | `Bash` pip/venv | Governed dependency install behind an HITL **batch** gate (decision made — see §5). Without it, "revive a real project" always leaves the seam. | Apply / target |
| 10 | `patch` **U** | — | Document the nested hunk schema (`search_block`/`replace_block`) + one atomic multi-hunk example in `tool.json` (field report New F2). | Apply / target |
| 11 | `web_search` | agent's web channel | **In scope (decided 2026-07-18):** governed, confirm-gated web search so discovery is audit-logged and reproducible like everything else. Results captured for `evidence`. | Apply / toolkit |

### Tier 3 — leverage (the compute-saving engine)

| # | Proposed tool | Why | Authority |
|---|---|---|---|
| 11 | `delegate` | Hand a **bounded task** to a local model (via `ollama_gov`) that uses the sidecar's *own* Tier-1 verbs as its hands, and return a distilled result. This is the mechanism by which the sidecar performs work *for* the expensive agent — the actual compute-saving payoff, not just distillation. | Apply |
| 12 | `run` health/classify **U** | `project_run`/`dev_server_manager`: distinguish `process_created` from bound-and-healthy; classify failures (policy vs missing-dep vs project) (field report New F3/F5). | Apply |
| 13 | per-node summaries (G5) / symbol graph (G6) | **DONE 2026-07-20 (D2):** `symbol_graph` + resolved-edge `dead_code`/`domain_boundary_audit`; CAS-cached module summaries. | — |

## 4. What is already covered (so we don't rebuild)

Search (`repo_search`), structure (`report`, `import_graph`, `complexity_score`, `file_tree`),
semantic retrieval (`bd_query`/`bd_why` + real embeddings), orientation (`attach`), memory
(`journal`/`evidence`/`session_record`), git (`git`/`git_inspect`), HTTP (`fetch`/`http_probe`),
process/port (`process_port_inspector`/`host_probe`), local inference (`ollama_gov`), sqlite
**reads** (`sqlite_inspect`), tests (`smoke_runner` + `project_run`), packaging/export, pdf, the
prompt-eval family. Coverage of *understand / remember / package* is strong.

## 5. Scope boundaries (deliberately NOT the sidecar's job)

- **User interaction** (`AskUserQuestion`): the agent owns the human channel.
- **The reasoning/judgment itself**: that is the agent; the sidecar is its instrument.
- **Web search — DECIDED (2026-07-18): in scope** as a governed `web_search` tool (Tier-2 #11),
  so discovery is audit-logged and reproducible. Browser *drive* remains the agent's channel.
- **`dep_install` (#9) — DECIDED (2026-07-18): in scope, behind an HITL batch gate.** The sidecar
  is headless, so its HITL gate *is* the preview-first/confirm pattern: `dry_run` resolves and
  returns the **complete** dependency set (every package, its source/version, the target env);
  the agent shows that one list to the operator; one `apply: true` installs the **whole batch**.
  Never one prompt per dep. Remaining implementation sub-question (settle at build time, not now):
  **which environment** — install the target's own deps into the *target's* venv (`writes: target`
  — genuinely revives the project, guarded + approved), or into a sidecar-isolated env
  (`writes: toolkit` — keeps the target pristine but may not let its entrypoints run). Reviving a
  real app points to the target venv; the batch-approval + precept guard make that safe and visible.

### The batch-consent convention (generalizes beyond dep_install)
Any tool that acts on **multiple items** must present them as **one plan for one approval**, not a
prompt per item. This is the universal `apply: true` convention (F1) with a rule attached: the
`dry_run` response lists the full set it would act on; a single confirm executes all of it. It
keeps the human-in-the-loop *informed in one glance* and the agent's round-trips bounded. Applies
to `dep_install`, batch `fs_op`, multi-file `write_file`/`edit`, etc.

## 6. Sketch of a completion plan (to be worked out together)

The natural build order mirrors the earlier phases: smallest, highest-leverage, each proven by the
harness before the next, each a governed tool with an `operates_on`/`writes` declaration so the
precept guard covers it.

1. **T1a — the read/write/glob core** (`read_file`, `write_file`, `glob`): pure, fast, low-risk;
   immediately lets an agent stay in the seam for file I/O.
2. **T1b — governed `run`**: the keystone. Confirm-gated arbitrary execution, output→evidence,
   precept-guarded. Retire the largest reason to leave the seam.
3. **T1c — `fs_op` + `edit` upgrade**: complete the mutation verbs safely.
4. **T2 — `sqlite_exec`, `diff`, `patch` docs**: data + review verbs.
5. **T3 — `delegate`**: the compute-saving loop, once the hands exist for a local model to use.
6. **Decisions first**: `dep_install` scope, web-search scope (§5) — settle before building either.

**Acceptance for "100%":** re-run a real engagement (like this build) and measure — via the
event log — that **zero** actions needed a tool outside the sidecar. That is the harness dimension
to add: *seam-completeness*.
