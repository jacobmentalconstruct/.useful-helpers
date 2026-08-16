# 0032 — C1b: Application Absorption Audit

- **Date:** 2026-08-15
- **Status:** **DIAGNOSTIC.** Nothing implemented, nothing refactored, nothing moved.
- **Authority:** `TRANCHE_PLAN.md` §C1b. T6 parked (0031); T7 **not yet declared**.
- **Method:** every equivalence claim below was tested by **invoking the candidate
  tool** against a real 1,506-file target, not inferred from its name or summary.

---

## 1. The question, and the answer

> How much of the useful prototype already exists as canonical tools, and exactly what
> duplicated or private logic must be removed or relocated so those tools behave as one
> bench?

**Answer: very little must move, and T7 is small.**

> `attach`'s 34 top-level functions group into **24 responsibilities**: **12 are
> legitimate front-door logic**, **3 duplicate canonical tools**, **3 belong to shared
> awareness state**, **4 are presentation**, and **2 are retained because no equivalent
> exists**.
>
> **Of the 3 duplications, T7 touches exactly one — and can only discharge it
> partially.**

The prediction I recorded before starting — *"most of the bulk is `keep` and `retain`,
not `replace`"* — held. The duplication story is much narrower than 1,051 lines
suggests.

*Counts corrected during review.* The first draft of this sentence said "34
responsibilities" with a five-way split summing to 34 — it had silently reused the
**function** count as the **responsibility** count and then invented a breakdown to
match, which disagreed with the table directly beneath it. Recounted from the table by
script. The distinction matters: 34 functions, 24 responsibilities.

---

## 2. `attach` — the classification

34 top-level functions, 930 lines of function body, grouped into **24
responsibilities**.

**`T7 touches?` casing is load-bearing.** **`YES`** = T7 needs this responsibility
directly (8 rows). `yes` = T7's output includes it but does not change it (5 rows).
`no` = out of T7's path entirely (11 rows).

| # | Responsibility | Functions | Canonical equivalent? | Verdict | **T7 touches?** |
| --- | --- | --- | --- | --- | --- |
| 1 | target walk / probe | `_probe` (87) | **`file_tree` — partial, tested** | **replace (partial)** | **YES** |
| 2 | newest-mtime capture | inside `_probe` | **none in 94 tools** | **retain** | **YES** |
| 3 | instrument self-exclusion | `_self_paths` (24) | `file_tree.ignore` takes dir names only | retain | yes |
| 4 | subsystem slicing | `_sub_probe`, `_slice_probe`, `_all_dirs` | derived from the walk | keep | no |
| 5 | path-aware glob | `_seg_match` | **`glob` — tested, equivalent semantics** | **replace (costly)** | no |
| 6 | workspace-member resolution | `_resolve_members`, `_workspace_members` | none | keep | no |
| 7 | manifest parsing (YAML/TOML/go.work) | `_parse_yaml_packages`, `_parse_toml_list`, `_parse_go_work` | **`dependency_check` — tested, NOT equivalent** | keep | no |
| 8 | cartridge loading | `_cartridges` | none | keep | no |
| 9 | cartridge scoring | `_score` (28) | none — unique | keep | **YES** |
| 10 | classification | `_classify`, `_compose` (45) | none — unique | keep | **YES** |
| 11 | entry-point detection | `_entry_points` | none | keep | yes |
| 12 | staleness signature | `_signature` | depends on #2 | **move** (shared) | **YES** |
| 13 | workspace identity load | `_load_workspace` | none | move (shared) | yes |
| 14 | evidence density | `_evidence_density`, `_is_nascent` | none | keep | yes |
| 15 | map building + limits | `_build_map` (76) | none | keep | **YES** |
| 16 | workbench mount union | `_build_workbench` (31) | none | keep | no |
| 17 | operator policy overrides | `_overrides_path`, `_load_overrides`, `_merge_policy`, `_apply_overrides` (~80) | none | keep | no |
| 18 | pre-bound policy args | `_policy_args` | none | keep | no |
| 19 | module docstring read | `_module_docstring` | **`report`/`symbol_graph` — tested, neither carries docstrings** | **replace-candidate, unproven** | no |
| 20 | LLM signal gathering | `_gather_signals` (40) | none | presentation | no |
| 21 | synopsis | `_synopsis` | `summarize_shared` (already shared) | presentation | no |
| 22 | next-step generation | `_next_steps` (62) | none | presentation | **YES** |
| 23 | scope narrowing | `_apply_scope` (36) | none | presentation | yes |
| 24 | profile/map persistence | `_workbench` + `run` | none | **move** (shared) | **YES** |

### The three duplications, measured

**#1 tree probe — `file_tree`, partial.** Both walked the same target:

| | files | wall | produces |
| --- | --- | --- | --- |
| `file_tree` (through the seam) | 1,508 | 0.24 s | `path`, `kind`, `ext`, `size_bytes` × 1,941 rows |
| `attach._probe` (in-process) | 1,506 | 0.10 s | 12 aggregates incl. `ext_counts`, `top_dirs`, `sub_*`, `shallow_files`, `newest_mtime` |

`ext_counts` and the subsystem tallies **are** derivable from `file_tree`'s rows — I
confirmed by aggregating them (`.py` 798, `.json` 294, `.md` 210). So the listing half
is genuinely duplicated.

Two things stop it being a clean swap, and both are honest:

- **`newest_mtime` has no canonical owner.** I searched all 94 tools: only
  `snapshot_diff` mentions mtime, and it compares two ProjectMapper snapshots by *path
  and content hash*, not modification time. **No tool reports mtime.**
- **The 2-file difference is the point — and it is two different causes, not one.** I
  first wrote that both were instrument self-exclusion. Diffing the two file sets
  instead of assuming:

  ```text
  in file_tree but NOT in _probe:  config/registry.json
                                   .github/workflows/verify.yml
  ```

  `config/registry.json` **is** instrument exclusion — it is in `_self_paths()`, and
  `file_tree.ignore` takes **directory names**, not paths, so it cannot express "the
  registry file I just regenerated."

  `.github/workflows/verify.yml` is **not**. `.github` is absent from `PRUNE`; it is
  pruned by `_probe`'s `not d.startswith(".git")` filter, which was meant for `.git`
  and also swallows **`.github`, `.gitlab`, and any other `.git*` directory**. See §7 —
  this is a real, small blind spot in the map, found by checking a causal claim I had
  already written down as true.

**#5 path-aware glob — `glob`, equivalent.** Tested: `glob {"pattern":"tools/*"}`
returned `tools/bd_knowledge/`, `tools/evidence/`, … — one segment, not crossing `/`,
which is exactly `_seg_match`'s contract, and `tools/**` spans segments as expected.

**But replacing it costs a filesystem walk per pattern.** `_resolve_members` matches
patterns against `_all_dirs(probe)` — directories already known from the single walk
`attach` has already done. Swapping in `glob` trades in-memory matching for N extra
subprocess walks. **Recorded as a real duplication with a real cost, and T7 does not
touch it.** Leave it.

**#19 module docstring — no equivalent found.** `report` returned
`summary: {files: 13, classes: 9, functions: 57}` plus markdown and **no per-module
docstrings** (its `modules` key was absent from the actual output despite appearing in
its declared `output_shape` — noted below). `symbol_graph stats` returned modules,
symbols, imports, refs and honesty — **no docstrings**. Marked *replace-candidate,
unproven*: T7 does not touch it, so C1 rule 1 forbids concluding anything further.

### The two claims I tested and disproved

Both were plausible enough that I would have written them down as duplications if I
had gone by tool summaries.

- **`dependency_check` does not resolve workspace members.** It returned
  `{"python": ["requirements.txt"], "node": []}` — declaration *files*, not pnpm/Cargo/
  uv/go.work member lists. `_workspace_members` is not duplicated. **Keep.**
- **`report` does not carry module purpose.** Counts and markdown only.

---

## 3. `projectmapper` — the atomicity test

> Is this one coherent deterministic operation with a useful independent contract, or
> merely an orchestration of independently useful existing primitives?

**Atomic. Re-home it; do not decompose it.**

337 lines, 11 functions, imports `hashlib`, `json`, `os`, `sqlite3`, `datetime`,
`pathlib` and `tools._toolkit` — **stdlib and the shared toolkit, nothing else.**

| Charter §1.4 smell | Present? |
| --- | --- |
| private backend | **no** |
| private project model | no — the snapshot schema **is** its output contract, and `snapshot_diff` consumes it |
| private state store | no — writes to `output_root()/projectmapper` like any tool |
| private workflow engine | **no** |
| application framework dependency | **no** |

Contract: **target in → deterministic SQLite snapshot out**, with a content checksum
that makes the same tree produce the same artifact. That is one operation, not an
orchestration.

**Composition was considered and rejected on measurement.** Reproducing it as a chain
needs a walk, then **one content read per text file**, then DB assembly. Measured: a
snapshot of `src/` alone captured `text_file_count: 27`; `file_tree` counts 1,508 files
across the whole repository, so a whole-target snapshot is that order of magnitude.
Each read would be a separate subprocess through the seam, to rebuild one artifact a
single tool produces in one pass — and `playbook.py` has no fan-out to express it with
anyway (C1a.4). **Splitting this would be exactly the ceremony the atomicity test
exists to prevent.**

The artifact is real and deterministic: `outputs` = `snapshot_db`, `sha256`,
`manifest`, with `content_checksum: 614af4e0…`. That checksum **is** the independent
contract.

### Dependents

| Consumer | Kind |
| --- | --- |
| `src/ui/mapper_view.py`, `src/ui/app_ui.py` | GUI — a **projection**, which is a legitimate layer |
| `run.bat map` → `src/app.py map` | entrance verb |
| `tests/test_smoke.py` (4 tests) | verification |
| `snapshot_diff` | consumes its artifact format |
| `src/core/payload.py` | names `_projectmapper` as regenerable output |
| **playbooks** | **none** |

**Nothing depends on it being an *application*.** Only the GUI is application-shaped,
and a GUI over a registered tool is a projection, not an application layer.

---

## 4. Retirement order, and what "retirement" means here

1. **`projectmapper` → `tools/projectmapper/`.** A move plus a registry refresh. The
   GUI keeps calling the same tool id through the same seam; `run.bat map` is
   unchanged; the four smoke tests reference the id, not the path.
2. **`apps/` becomes empty** and the directory, its README and the `apps/*` registry
   scan path retire with it.
3. `docs/ARCHITECTURE.md` §2/§7 drop the transitional note.

**Not scheduled here.** This is the audit's recommendation, not a work order. Under
C1a it needs an operator decision, and under the STOP assertion it is **not urgent**:
re-homing satisfies the architecture, and semantics — not folder purity — is the test.

---

## 5. Can T7 complete with no live app? **Yes.**

`attach` does not call `projectmapper`. No playbook does. The T7 contributor set
(`attach`, `report.summary`, `import_graph` hotspots, `dead_code.summary`,
`sqlite_inspect`) contains no `apps/` member. **T7 has no application dependency to
remove, and the re-home can happen before, during or after it without affecting it.**

---

## 6. What this means for T7's size

Eight responsibilities are marked **`YES`**, and they account for exactly eight:

| verdict | rows | what T7 does with them |
| --- | --- | --- |
| keep | #9 scoring, #10 classification, #15 map+limits | **consumes unchanged** — unique front-door logic, no canonical equivalent |
| move | #12 staleness signature, #24 persistence | **extends** the existing workbench-persistence path into awareness revision identity |
| presentation | #22 next-steps | renders the new envelope |
| replace | #1 tree probe | the **only** duplication T7 discharges, and only *partially* |
| retain | #2 newest-mtime | no canonical owner exists; it stays where it is |

**So T7 is: compose five existing tool outputs into one persisted envelope, key it to
the instance UUID, and project it two ways.** Three of its eight touch points it does
not modify at all. The reduction pass inside it is **one** responsibility, not a
rewrite.

---

## 7. Findings recorded, not acted on

- **`attach` cannot see `.github/`, `.gitlab/`, or any `.git*` directory.**
  `_probe` prunes with `not d.startswith(".git")`, which was written for `.git` and
  catches every sibling. `.github` is **not** in `PRUNE`, so this is an unintended
  consequence of a prefix match, not a decision. For a product whose job is to
  understand a target, CI configuration is exactly the sort of thing the map should
  see — and `command_profile` looking for build/test commands cannot find workflow
  files either. **Small, real, and cheap to fix** (`d == ".git"` plus explicit entries
  in `PRUNE` for anything else genuinely unwanted). Not fixed here: C1b implements
  nothing, and T7 touches `_probe`, so it is the natural place. **Backlog.**
- **`report`'s declared `output_shape` lists `modules`; the actual output omits it.**
  A manifest promising a field the tool does not return. Backlog, not T7.
- **No tool reports file modification time.** If T7's freshness field needs it and
  composition cannot supply it, that is the first genuine primitive gap this project
  has found — but **C1 rule 1 requires an end-to-end attempt to demonstrate it before
  any tool is proposed.** Not concluded here.
- `_seg_match` duplicates `glob` at the cost of a re-walk. Left alone; T7 does not
  touch it.
- `_module_docstring` has no equivalent; unproven either way.

---

## 8. Next

**Declare T7 from this evidence.** Its gate is written at declaration, before
implementation, and it stops at the awareness envelope — no target mutation, no
`attach` rewrite, and no `replace` verdict discharged beyond the tree probe.
