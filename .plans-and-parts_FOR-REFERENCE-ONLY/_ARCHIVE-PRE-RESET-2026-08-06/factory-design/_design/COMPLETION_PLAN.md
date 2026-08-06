# Completion Plan — seam-completeness (the sidecar as an agent's only toolset)

**Date:** 2026-07-18 · **Status:** the plan; build against it, one phase at a time.
Follows `CAPABILITY_GAPS.md` (the analysis) and continues `PLAN.md` (phases 1–6, done).

---

> **STATUS (2026-07-20): COMPLETE.** C0-C8 (seam-completeness 18/18, scenario 15/15), D1 (one governed inference seam + usage accounting; refresh-proof policy overrides), D2 (resolved symbol graph G6; CAS-cached node summaries G5), D3 (M1 read-only mount = precept by PREVENTION; B1 dangling-citation sweep). **Nothing planned remains.** Final: 90 tools, smoke 75+1 env, ruff clean, truthfulness 0 FP / 0 missed, six-kind sweep green with precept delta 0, M1 MOUNT PASS on Linux.

## The goal, stated as an acceptance

An agent binds to the sidecar's MCP surface and needs **nothing else** to work a target: read,
search, edit, write, run, install, orient, remember, discover — every action audit-logged,
precept-guarded, reproducible. The proof is a number, not an opinion:

> **Seam-completeness:** a scripted canonical engagement (read → search → edit → create → run →
> test → inspect-data → dep-install(dry) → commit) completes using **only sidecar tools**, and a
> capability-coverage checklist reads 100%. Measured by the harness (see C0).

Two decisions already settled (`CAPABILITY_GAPS.md §5`):
- **`dep_install`**: in scope, HITL **batch** gate (dry-run lists the whole set → one `apply`).
- **`web_search`**: in scope, governed + audit-logged. Browser *drive* stays the agent's channel.
- **Batch-consent convention**: any multi-item tool shows one plan for one approval.

Working rule (unchanged): **no phase is done until the harness says so** — a scored dimension
moves. Each tool declares `operates_on`/`writes` so the precept guard covers it by construction.

---

## C0 — Measure first (seam-completeness instrumentation) ✅ DONE 2026-07-18

**Build the ruler before the tools**, so every later phase moves a real number.

**Built:** `python _harness/harness.py seam` — a new harness subcommand with two measures, run
against a throwaway `_seam` scaffold (python files + a sqlite db + git-init), auto-cleaned.
**Baseline today: capability coverage 8/18 (44%); self-hosting scenario 6 ok / 8 blocked / 0
failed.** Blocking tools (the burn-down list): `read_file, glob, write_file, run, sqlite_exec,
diff, dep_install, web_search` (+ `fs_op`, `delegate` in coverage). Recorded to
`_harness/runs/<ts>-seam/seam.json`. Idempotent; existing `run`/sweep unaffected.

- **Capability-coverage checklist** (`_harness`): a static map of required capability classes →
  tool id (read, write, glob, exec, fs-mutate, edit-exact, grep, diff, sqlite-read, sqlite-write,
  dep-install, web-search, git, http, orient, remember). Scored: *N of M present*. It will read
  low today and climb as phases land — a visible burn-down.
- **Self-hosting scenario** (`_harness`): a scripted engagement that performs a canonical
  multi-step task **only through the seam** and asserts it completes. Steps unavailable today are
  marked `blocked: <missing tool>` — so the scenario itself enumerates the gap and turns green as
  tools arrive.
- **Acceptance:** both dimensions exist and report the current (incomplete) state honestly.

## C1 — The hands: file I/O + glob  (replaces Read / Write / Glob) ✅ DONE 2026-07-18

**Built:** `read_file` (Observe/none — content by path, 1-based line range, byte-capped),
`write_file` (Apply/**target** — preview-first, create/overwrite, create-only guard), `glob`
(Observe/none — `**` patterns, prunes noise + toolkit home). Shared `resolve_within_roots` in
`_toolkit.py` blocks path escapes outside work-target/toolkit-home (all hands use it).
`attach` now unions a **BASE_MOUNT** (read_file, glob, repo_search, write_file, journal, evidence)
into every workbench, so the hands are discoverable via the front door and future hands land in
one place. **Result: seam coverage 8/18 → 11/18; scenario 6 → 9 ok.** Front-door mount 17 → 20.

**Two bugs caught while proving it:**
- `_default_args` fed `path: "."` (a directory) to `read_file`, a false tool-health failure. Fixed:
  the harness feeds a real `sample_file` to path-taking tools; skips if none.
- The sample-file filter checked `SIDECAR_NAME` against **absolute** path parts — and our sandbox
  root is literally `.useful-helpers`, so it excluded everything. Fixed to check the path relative
  to the target (invisible in a normal deployment, wrong regardless).

Smoke 66 pass (bar env git; new `test_c1_hands`), ruff clean, harness sweep green.

- `read_file` (Observe/none): content by path, `offset`/`limit`/line-range, size-capped, refuses
  outside the work target unless pointed at the toolkit.
- `write_file` (Apply/**target**): create/overwrite, preview-first, **precept-guarded** — the
  guard already governs Observe writes; here the tool *declares* `writes: target` so an Apply
  write is the sanctioned, audited path (not a Bash end-run).
- `glob` (Observe/none): path patterns (`**/*.py`), or fold into `file_tree`.
- **Acceptance:** self-hosting scenario reads a file, globs the tree, and creates a file entirely
  through the seam; coverage checklist gains read/write/glob.

## C2 — Governed execution  (replaces Bash — the keystone) ✅ DONE 2026-07-18

**Finding while building:** `exec` was not actually missing — `project_run` already runs arbitrary
`command` strings (shell, preview-first, output capture, evidence). The baseline showed it "missing"
only because the checklist mapped `exec` to a nonexistent id `run`. Per the cross-cutting rule
(*prefer upgrading an existing tool*), C2 = **upgrade `project_run` into THE governed executor**,
not a redundant new tool.

**Upgraded:** cwd is now confined to the roots via `resolve_within_roots` (a command may run in a
target subdir, never an arbitrary host dir — the governance win); added a failure `classification`
(ok / nonzero_exit / command_not_found / not_executable / timeout, F5); declared `writes: target`;
broadened the summary/framing to "the audited replacement for ad-hoc shell". Added to `BASE_MOUNT`
so every workbench has execution. Remapped the checklist `exec -> project_run`.

**Bug caught:** `if dry_run or not confirmed(args)` — `dry_run` defaults true, so a *direct*
`apply:true` call (not through the seam's `_normalize_apply`) short-circuited to preview and never
ran. Fixed to `if not confirmed(args) or args.get("dry_run") is True` — robust via seam OR direct.

**Result: coverage 11/18 → 12/18; scenario 10 ok / 4 blocked.** The existing `test_project_run`
was updated (its old `cwd=tempfile.mkdtemp()` is now correctly refused as an out-of-roots escape;
added a classification + escape assertion). Smoke 66 pass (bar env git), ruff clean, sweep green.

- `run` (Apply/**target**): execute one arbitrary command, preview-first (show argv + cwd + env
  scope), capture stdout/stderr/exit as an `evidence` item, precept-aware (declares `writes:
  target` because commands legitimately produce build/test artifacts), bounded timeout, classify
  failure (policy / missing-dep / temp-ACL / project — field report New F5).
- **Upgrade** `project_run`/`dev_server_manager`: distinguish `process_created` from bound-healthy;
  bounded startup grace (New F3).
- **Acceptance:** scenario runs the target's test + lint through the seam; output captured as
  evidence; a command that touches the target is logged, not hidden. This closes the largest
  governance hole (most of what I did this build was ad-hoc shell).

## C3 — Mutation verbs, made safe  (replaces Bash fs + hardens Edit) ✅ DONE 2026-07-18

**Built `fs_op`** (Apply/target): a BATCH of mkdir/touch/copy/move/delete in one plan → one apply
(batch-consent), every path confined to the roots, delete recursive for dirs (the batch approval
is the gate). **Upgraded `edit`:** `literal:true` (exact-string, no regex) + `expected_replacements`
(refuses the write unless the match count matches — the safety belt for New F1's "greedy match ate
a bigger block"), and its path is now roots-confined. Both added to `BASE_MOUNT`. 84 tools.

**Proven:** `edit` with `expected_replacements=1` on 3 matches REFUSES and leaves the file
untouched; `=3` applies. `fs_op` batch (mkdir+copy+move) previews then applies all; escapes refused.
**Result: coverage 12/18 → 13/18; scenario 11 ok / 4 blocked.**

Two existing tests used out-of-roots temp paths (`edit`/`test_seam_universal_apply`) now correctly
refused by the roots boundary — updated to write inside `_artifacts`. New `test_c3_mutation`. Smoke
67 pass (bar env git), ruff clean, sweep green.

- `fs_op` (Apply/target): mkdir / copy / move / delete / touch, **batch-consent** (one plan →
  one apply), precept-guarded.
- `edit` **upgrade** (Apply/target): `literal: true` + `expected_replacements` (refuse unless the
  dry-run count matches) + bounded before/after context (field report New F1 — a greedy regex once
  ate more than intended).
- `patch` **upgrade**: document the `search_block`/`replace_block` schema + a multi-hunk example
  (New F2).
- **Acceptance:** scenario moves/deletes files via one batch approval; `edit` refuses on a count
  mismatch; scenario performs an exact edit that Bash-`Edit` would have.

## C4 — Data + review  (replaces Bash sqlite/diff) ✅ DONE 2026-07-18

**Built `sqlite_exec`** (Apply/target): one parameterized write (INSERT/UPDATE/DELETE/DDL), DB
confined to the roots, **preview via transaction ROLLBACK** — so the dry-run reports the exact
affected-row count without persisting; apply commits. SELECT refused (points to sqlite_inspect).
Mounted in the data-curation cartridge. **Built `diff`** (Observe/none): unified text/file diff
(paths within roots or inline text) + added/removed counts; added to `BASE_MOUNT`. 86 tools.

**Proven:** `sqlite_exec` preview says `would_affect=2` while 0 rows actually change (rollback);
apply commits 2; SELECT refused. `diff` yields a correct unified diff. **Result: coverage
13/18 → 15/18 (83%); scenario 13 ok / 2 blocked.**

**Harness improvement:** `_default_args` now returns None (skip) for a tool with its own params but
no root/path (e.g. `diff` needs a/b) instead of calling it with `{}` and false-failing it. Fixed a
test that leaked open sqlite connections (Windows file-lock on cleanup). Smoke 68 pass (bar env
git; new `test_c4_data`), ruff clean, sweep green.

- `sqlite_exec` (Apply/target): parameterized INSERT/UPDATE/DELETE/DDL, preview-first (row-count
  estimate), confirm-gated (field report B6). Unblocks data-curation targets and state scrubbing.
- `diff` (Observe/none): unified text/file diff — review a change and ground it as evidence.
- **Acceptance:** scenario writes a row via `sqlite_exec` under confirm and diffs two files
  through the seam.

## Review pass (2026-07-18, after C0–C4) — findings fixed

An audit of the C-series hands. Everything below is fixed, re-proven, and regression-tested.

1. **`fs_op` could delete the work target (CRITICAL).** `resolve_within_roots` permits the root
   itself, so `{op:"delete", path:"."}` resolved to the project root and would have `rmtree`'d the
   **entire target** — likewise `""` and `sub/..`, and the same for the toolkit home. **Fixed:**
   destructive ops (`delete`/`move`) now refuse any path that resolves to a root. Regression test
   asserts all three forms are refused and the target survives.
2. **`glob` escaped the roots.** `glob "../*.py"` returned files *outside* the work target,
   defeating the confinement every other hand enforces (a read/privacy boundary hole). **Fixed:**
   matches are resolved and confined to the root. A follow-on the new test caught: an escaping
   pattern circles back and matched the root itself (`./`) — now excluded.
3. **`sqlite_exec` previews had a side effect.** `sqlite3.connect()` *creates* the file, so a
   dry-run against a non-existent DB wrote an empty database. **Fixed:** a preview on a missing DB
   returns a plan without connecting. Also hardened with `isolation_level=None` so the
   rollback-preview's BEGIN/COMMIT/ROLLBACK is explicit and version-independent.
4. **`write_file` preview under-reported.** The "path is a directory" refusal only fired on apply,
   so a preview claimed it would write. **Fixed:** checked before the plan.
5. **`BASE_MOUNT` advertised phantoms.** Its comment claimed only existing tools are surfaced, but
   the code didn't filter — a missing base tool would appear in the workbench and fail on call.
   **Fixed:** filtered by manifest existence, making the claim true.

**Doc staleness cleaned:** `AGENTS.md` hardcoded "not all 78" (now count-agnostic) and — more
importantly — **never told agents they have hands**; it now carries a "You have hands — use them
instead of your own" table with the seam's rationale (audit-logged, reproducible, visible to the
next agent). `ARCHITECTURE.md` §2 notes the base mount. `ATTACH_SKELETON.md`'s "29 of 78" live
claim made count-agnostic. `TOOLS.md` regenerated (86 tools). Counts inside dated ✅DONE entries
are left as historical record.

Smoke 68 pass (bar env `git_inspect`), ruff clean, seam 15/18, sweep green.

## C5 — Dependencies (HITL batch)  (replaces Bash pip/venv) ✅ DONE 2026-07-18

**Sub-decision resolved — install into the TARGET's venv.** The codebase had already answered it:
*both* precept measures (the harness snapshot's `SNAPSHOT_SKIP` and the seam guard's `_GUARD_SKIP`)
already skip-list `.venv`/`venv`. A virtualenv is regenerable **environment**, not project content
— so installing there genuinely revives the project (its own entrypoints find their deps) without
tripping the precept. Rails: **never the system/global interpreter** (a missing venv is refused
unless `create_venv:true`), venv confined to the roots, explicit `venv` override.

**Built `dep_install`** (Apply/target): resolves the COMPLETE set from explicit `packages` +
`requirements.txt` + `pyproject [project].dependencies`, **deduped, each with its source**, and
reports it as ONE list with the target venv; a single `apply` installs the **whole batch** in one
pip command. Never one prompt per dep. Mounted in the python-app cartridge. 87 tools.

**Proven:** preview produced one deduped 5-package list across three sources with provenance; the
no-venv rail refused; and a real end-to-end apply created the venv, installed the batch, and the
package imported **from the target's venv**. **Result: coverage 15/18 → 16/18 (88%); scenario
14 ok / 1 blocked** (only `web_search` left).

Also ASCII-fixed two user-facing error strings (`dep_install`, `edit`) per the shipped-strings
convention. New `test_c5_dep_install_batch` (preview-only: no network). Smoke 69 pass (bar env
git), ruff clean, sweep green.

## C5 (original plan text)

- `dep_install` (Apply/**target**): `dry_run` resolves the **complete** set (packages, sources,
  versions, target env) and returns it as one list; one `apply: true` installs the **batch**.
  Never a prompt per dep.
- **Build-time sub-decision:** install into the *target's* venv (`writes: target` — revives the
  project; guarded + approved) vs a sidecar-isolated env (`writes: toolkit` — target pristine).
  Reviving a real app favors the target venv; the batch gate + guard make it safe. Decide with the
  code in front of us.
- **Acceptance:** dry-run returns the full dependency list; apply installs the batch; the guard
  and event log both record it.

## Tranche review + cleanup (2026-07-18, after C5)

### Bug fixed — the batch gate was telling a half-truth
`dep_install`'s requirements parser skipped every line starting with `-`, so a **`-r base.txt`
include silently dropped its packages** from the list. The operator would approve a list that
wasn't the truth — which defeats the entire point of the batch gate. (Worse, a code comment
claimed the skipped directives were "reported as a note below"; no such note existed.)

**Fixed:** `-r`/`--requirement` includes are now expanded **recursively** (depth-bounded,
cycle-guarded, each nested path roots-confined), and anything genuinely unexpandable (`-e .`,
`--index-url`) is surfaced as `unresolved` + an explicit note that the list may be incomplete.
Nothing is dropped silently. Proven: a 2-level nested include produced the complete 4-package list
with correct per-file provenance; an `a→b→a` cycle terminated; `-r ../outside.txt` was refused and
flagged. Regression-tested (completeness is the promise, so it is now pinned).

### Cleanup — the toolkit had grown its own residue
The smoke suite's `_tmp_path` created a uuid dir per call under `_artifacts/test_tmp` and **never
cleaned up: 822 dirs / 20 MB had accumulated** — the exact generated-residue rot this project was
founded to eliminate (the original dirty folder was 70% the same thing), sitting in the product's
own tree. Fixed at the source (`addCleanup` per test + a class-teardown sweep for dirs whose
sqlite handle was still held on Windows). **A full smoke run now leaves zero residue.**

The existing residue was cleared by **dogfooding the toolkit's own `artifact_cleaner`** rather
than reaching for `rm` — the governed tool exists for exactly this. **Toolkit 23 MB → 2.6 MB**,
87 tools intact. Harness run history pruned 97 → 12.

### Tranche state (C0–C5 complete)
| | |
|---|---|
| Tools | 87 |
| Seam capability coverage | **16/18 (88%)** |
| Self-hosting scenario | **14 ok / 1 blocked** (only `web_search`) |
| Smoke | 69 pass + 1 environmental (`git_inspect`: no `.git` in sandbox) |
| Lint | clean · **Harness sweep** precept + cleanliness green |

Hands delivered: `read_file` `glob` `write_file` `edit`(literal+count-guard) `fs_op`(batch)
`project_run`(governed exec) `diff` `sqlite_exec` `dep_install`(HITL batch). All roots-confined,
preview-first, audit-logged; unioned into every workbench via `BASE_MOUNT` and documented in
`AGENTS.md` ("You have hands").

## C6 — Discovery: governed web_search ✅ DONE 2026-07-19 — **SCENARIO NOW FULLY GREEN**

**Built `web_search`** (Apply/toolkit) behind a thin **provider adapter** (`searxng` | `brave` |
`tavily`, configured by `SUITE_SEARCH_PROVIDER` + `SUITE_SEARCH_URL`/`SUITE_SEARCH_API_KEY`), so
the tool is not welded to one service — adding a provider is one function plus one normaliser.
Results are normalised to uniform `{title, url, snippet}` so callers never branch on provider.

- **Preview-first because a search is an outbound disclosure.** The dry-run reports *which
  provider, which endpoint, and the exact query that would leave the machine* — and contacts
  nothing. Apply performs it. `evidence:true` grounds the results.
- **Honest when unconfigured:** returns `ok:false` with `configure` guidance and **no `results`
  key at all** — it never fabricates, the same stance as the embedding/summary backends.

**Milestone: `seam_complete=True` — the self-hosting scenario is 15 ok / 0 blocked.** The whole
canonical engagement (orient → grep → read → glob → edit → write → fs → exec → sqlite read+write
→ diff → dep-install → search → remember → commit) now runs **entirely through the governed
seam**. Coverage 17/18 — only `delegate` (C7) remains.

**DRY tweak:** `attach_evidence()` moved into `tools/_toolkit.py` and `project_run` refactored to
use it, rather than a second private copy in `web_search`. 88 tools, smoke 70 pass (bar env git),
ruff clean, sweep green (precept + cleanliness + enforcement), zero test residue.

- `web_search` (Apply/toolkit): confirm-gated query, capped results, captured for `evidence`,
  audit-logged. Provider behind a thin adapter so the tool isn't welded to one service.
- **Acceptance:** a query returns results through the seam and is recorded in the event log.

## C7 — `delegate`: the compute-saving engine ✅ DONE 2026-07-19
## C8 — Capstone ✅ MET (coverage 18/18, seam_complete=True)

**Built `delegate`** (Apply/toolkit): a bounded tool-use loop where a **local** Ollama model is
given the task plus an allowlist of the sidecar's verbs, emits one tool call at a time as JSON, and
**every call is executed THROUGH THE GOVERNED SEAM** — so the delegated work is audit-logged like
any other, not a side channel. Returns the distilled answer plus the full trail (`evidence:true`
grounds it).

**Bounded by construction:** `max_steps` (cap 12), per-call timeout, and an allowlist that (a) can
never contain `delegate` itself, and (b) is **Observe-only unless the caller passes
`allow_apply:true`** — a small local model must not silently receive write/exec authority; unknown
tool names read as elevated so nothing slips past. Degrades honestly with no model reachable.

**The payoff, demonstrated:** given *"List every .py file under app/ and say in one line what each
does"*, the local model autonomously ran `glob -> read_file -> read_file` (three governed seam
calls) in **7s** and returned a correct summary — work the expensive agent never had to do itself.

**Default model chosen by measurement, not assumption.** On a "which file defines X" probe,
`qwen2.5-coder:7b` answered *"no file defines it"* against an observation that plainly showed the
match; `qwen2.5:7b` answered correctly in ~6s (14b also correct but 26s). A fast wrong answer is
worse than none — the default is now `qwen2.5:7b`, with the finding recorded in the source.

### Capstone acceptance — MET
```
CAPABILITY COVERAGE  18/18  (100%)
SELF-HOSTING SCENARIO  seam_complete=True  (15 ok / 0 blocked / 0 failed)
```
The canonical engagement — orient, grep, read, glob, edit, write, fs, exec, sqlite read+write,
diff, dep-install, search, remember, commit — runs **entirely through the governed seam**. The
sidecar can now replace an agent's inherited toolset.

### Review + cleanup this tranche
- **`delegate` allowlist frailty (fixed):** a caller could hand a local model `project_run` /
  `write_file` / `fs_op` with no guard. Now refused unless `allow_apply:true`; regression-tested
  (including unknown-tool-reads-as-elevated).
- **Shipped strings normalised to ASCII:** 7 `tool.json` manifests plus `src/core/docs.py` carried
  em-dashes/`§`, so the generated `TOOLS.md` did too — mojibake risk on cp1252 consoles and against
  the convention. **All shipped manifests and TOOLS.md are now 0 non-ASCII bytes.**
- Stale `delegate` schema text (named the pre-measurement default model) corrected.
- Verified: no dangling links in shipped docs; zero test residue per run; toolkit 2.7 MB.

**State:** 89 tools · smoke **71 pass** + 1 environmental (`git_inspect`: no `.git` in sandbox) ·
ruff clean · full sweep green (precept + cleanliness + enforcement across all six target kinds).

Only possible once the hands (C1–C4) exist. Hand a **bounded task** to a local model (via
`ollama_gov`) that uses the sidecar's *own* verbs as its hands, and return a distilled result — so
the expensive agent is invoked for judgment, not grunt work.

- `delegate` (Apply): task spec + allowed-tool allowlist + budget; runs a bounded local-model loop
  over the seam; returns result + the evidence/journal trail of what it did.
- **Acceptance:** a delegated task ("summarize these N files", "find where X is configured")
  completes on a local model, touches only allowlisted seam tools, and returns a correct distilled
  answer — with the expensive agent never reading the files itself. Measure the offload.

## C8 — Capstone: seam-completeness = 100%

- Turn on the full self-hosting scenario end-to-end; capability checklist = 100%.
- **Acceptance:** the canonical engagement completes with **zero** non-sidecar operations, proven
  by the event log covering every step. This is the definition of "the sidecar replaced the
  inherited toolset."

---

## Sequencing rationale

C0 first (measure), then C1→C2 (the hands + execution — closes the governance hole fastest and is
the prerequisite for everything else), then C3→C4 (safe mutation + data), C5→C6 (deps + discovery),
C7 (delegate — needs the hands), C8 (prove 100%). `delegate` is the biggest compute win but is
*downstream* of the hands by necessity, so governance-first and compute-win-first are the same path.

## Cross-cutting (every phase)

- Declare `operates_on` + `writes`; the precept guard governs it; the event log records it.
- Preview-first for every Apply tool; `apply: true` executes; multi-item = batch-consent.
- A smoke test per tool + a harness scenario step; regenerate `TOOLS.md` (`docs-refresh`) so the
  drift test stays green.
- Prefer upgrading an existing tool over adding one (edit, patch, project_run, dev_server_manager).

---

# The D tranches — completing the remaining TODOs
_Planned 2026-07-20. The C-series acceptance (seam-completeness 100%) is already MET; nothing
below is load-bearing. These are ranked by **value per unit of risk**, not by the order they were
first written down. Two items from CAPABILITY_GAPS Tier-3 are already closed and are NOT here:
`patch`'s nested-hunk schema is documented, and `project_run` has failure classification._

## D1 — Close the gaps (small, high-leverage)

### O1 — Route local inference through one governed seam
**The defect.** Four modules open their own Ollama client today: `tools/embed_shared.py`,
`tools/summarize_shared.py`, `tools/delegate/cli.py`, and `tools/ollama_gov/cli.py` — four copies
of `_client()`, four probe/degrade conventions, four un-accounted call paths. Local inference is
the one capability that burns real resources and can silently degrade, and it is the ONE capability
not passing through a chokepoint. That is the same class of gap as `bd_index` claiming a free lunch
while re-embedding everything: not a missing feature, a governance hole.

**The shape.** A new shared substrate `tools/llm_shared.py` becomes the single place a local model
is called — client acquisition, availability probe, tier-bounded chat, embed, and **usage
accounting** (one JSONL line per call in the state root: purpose, model, caps, duration, token
counts when the backend reports them). `ollama_gov` keeps `TIERS` as its public face but sources
them from the substrate; the other three become callers. Global kill-switch `SUITE_LLM_DISABLE=1`;
existing per-family switches (`SUITE_EMBED_DISABLE`, `SUITE_SUMMARY_DISABLE`) still honoured.

**Acceptance:** exactly one `import ollama` in the tree; every local-model call appears in the
usage log with a `purpose`; smoke stays green; offline degradation unchanged (proven by the
existing disable-switch tests).

### P1 — Per-target policy overrides that survive `refresh`
**The defect.** An operator can tune a cartridge's policy for one target, and `attach --refresh`
silently discards it — there is no override handling in `tools/attach/cli.py` at all. Refresh
currently punishes the operator for customising.

**The shape.** A per-target override file in the state root (NOT the workbench, which refresh
rewrites), merged over the cartridge policy on both map and re-engage, with the merge surfaced in
the returned workbench so an agent can see a policy was overridden rather than inheriting it
invisibly.

**Acceptance:** set an override, `attach --refresh`, override still applied and visibly marked.

## D2 — The capability work

### G6 — Symbol graph, then G5 — per-node summaries
G6 first, and the reason is on-thesis: `dead_code` and `domain_boundary` are heuristic today, which
means they can assert things that are not true. A real symbol graph makes them **correct by
construction** — converting two tools from "plausible" to "truthful" is exactly what this project
claims to be for. G5 (per-node summaries feeding `attach`/`expand`/`why`) rides on top and is much
cheaper once O1 exists. Own tranche, harness-scored like C1-C7.

## D3 — Assurance + polish

### M1 — Real read-only mount on Linux CI
Phase 4's remaining 20%. The precept is *measured* today (sha256 manifest diff catches a violation
after it happens); a mount makes it *impossible*. Strict upgrade in kind — prevention over
detection. Honest caveat: cannot run on the Windows dev box, so the value lands only in CI.

### B1 — `BCC` comment sweep
Core modules are annotated; the ~89 tool adapters mostly are not. Pure consistency. Last, and
acceptable to never do.

## Sequencing rationale
D1 is the only tranche where the work *fixes* something rather than *adds* something, and O1 makes
D2 materially cheaper — so governance-first and cost-first are again the same path.

---

## D1 — ✅ DONE 2026-07-20

### O1 — one governed inference seam ✅
Built `tools/llm_shared.py`: client, probe, tier-bounded `chat()`, `embed()`, `list_models()`, and
usage accounting. Converted all four callers. **There is now exactly ONE `import ollama` in the
tree, and a smoke test fails if a second one appears** — the invariant is enforced, not asserted.

- `ollama_gov` now sources `TIERS` from the substrate rather than defining its own. A governor
  that publishes different numbers than it enforces governs nothing; now the tiers it advertises
  are literally the ones every caller is bound by.
- New `ollama_gov {"action":"usage"}` reports totals **grouped by purpose** plus recent records.
  Accounting nobody can read is not governance, so the governor is where you ask what local
  inference cost. Every record carries a `purpose` (`attach.synopsis`, `delegate.step`,
  `ollama_gov.run`, `index`) — a record that cannot say which capability spent the tokens is noise.
- **Accounting shape decision:** chat calls log one line each (few, individually expensive);
  embeds are counted in-process and flushed as ONE rollup line at exit. Measured: a real
  `bd_index` run made 2,392 backend embed calls and produced **one** log line. A per-embed line
  would have been a 2,392-line flood nobody reads.
- Honest counting: the rollup (2,392) is lower than `embedded: 2750` because the in-process text
  cache absorbs duplicates. The log counts ACTUAL BACKEND CALLS — the real cost, not the nominal one.
- New global kill-switch `SUITE_LLM_DISABLE=1` disables all local inference and every caller
  degrades honestly (structural map, lexical retrieval, no delegation); tested.
- Live proof: `ollama_gov run` against qwen2.5:3b returned `OK` in 1999ms with real
  `prompt_tokens: 36 / output_tokens: 2` surfaced — token counts the old code never reported.

### P1 — per-target policy overrides that survive refresh ✅
`<state_root>/policy_overrides.json`, keyed by target path or `*`, layered over the cartridge
policy on BOTH the map and re-engage paths.

- **Placed in the state root, not the workbench** — that is the whole mechanism. Refresh rewrites
  the workbench wholesale; it cannot clobber what it does not own.
- **Layered at READ time, never written back into `profile.json`.** The stored profile stays a
  faithful record of what was DETECTED; the override is a separate, visible record of what the
  operator DECIDED. Verified: after an override + refresh, `profile.json` has no `overridden` key
  while the returned workbench does.
- **Reaches `next`, not just the policy block.** Overrides are folded into the cart that drives
  `_policy_args`, so pre-bound arguments in the suggested calls actually reflect them — otherwise
  the override would be advertised and then not applied, which is the kind of cosmetic lie this
  project exists to eliminate.
- `tool_args` merges KEY-WISE so pinning one argument keeps the cartridge's others (measured:
  operator `root:src` + cartridge `entrypoint_decorators` both present). Other fields replace.
- Overridden entries return `"overridden": true` and `workbench.policy_overrides` names the tools.
- A malformed override file degrades to "no overrides" rather than taking the front door down.

### Cleanup this tranche
- **Shipped docs normalised to ASCII**, extending the C7 convention beyond manifests:
  `OPERATIONS.md` 26 -> 0, `ARCHITECTURE.md` 115 -> 0 (its two box-drawing diagrams converted to
  ASCII art, verified still legible), `ONBOARDING.md` 11 -> 0, `PROJECT_GOVERNANCE.md` 5 -> 0.
- `OPERATIONS.md` gained sec 8 (policy overrides) and sec 9 (reading the usage log).
- `AGENTS.md`: agents are now told to prefer `delegate` for grunt work, to trust an
  `"overridden": true` policy over their own read, and where to ask what inference cost.
- `ARCHITECTURE.md` state-root listing updated with the two new durable files.

**State:** 89 tools · smoke **73 pass** + 1 environmental (`git_inspect`: no `.git` in sandbox) ·
ruff clean · seam 18/18 + `seam_complete=True` (15 ok / 0 blocked) · full six-kind sweep green,
**precept delta 0 on every kind**.

**Next:** D2 (G6 symbol graph -> G5 per-node summaries), then D3 (M1 Linux read-only mount, B1).

---

## D2 — ✅ DONE 2026-07-20 (G6 symbol graph + G5 per-node summaries)

### G6 — the resolved symbol graph ✅
New substrate `tools/symbol_graph_shared.py` + query tool `symbol_graph` (Observe/toolkit).
The contract: **an edge exists only when a reference actually BINDS to its target** through an
import, a local definition, or a lexical scope. Everything weaker lands in one of two honest
side-channels - `fuzzy_attr_uses` (attribute-name evidence, clearly labelled) and `unresolved`
(star imports, getattr, dynamic imports) - so consumers state their limits from ledgers instead
of pretending completeness. 135 files -> graph in 0.37s; rebuilt per call, never stale.

**`dead_code` rebuilt on reachability.** The predecessor counted name coincidence as life: any
file mentioning `run` kept every `run` alive, and two dead functions calling each other read as
referenced. Now: roots (framework decorators, `__all__`, entrypoint/lifecycle names, tests,
dunders, interface overrides) -> BFS over resolved edges -> candidates are the unreachable, with
**two-tier reachability**: strict (resolved edges only) vs assume-dispatch (methods of live
classes count). high = dead under EVERY modelled assumption; medium = alive only if dynamic
dispatch occurs; low = live class + fuzzy name agree. Fixture proof: a mutually-recursive dead
pair and a name-coincidence orphan - all invisible to the old tool BY CONSTRUCTION - found at
high confidence, live chain untouched.

**`domain_boundary_audit` re-grounded.** Real defect fixed: `python_import_names` stripped
relative dots, so `from ..core import x` was attributed to a top-level `core` whether or not
that was the anchor package. Edges now come from the graph with relative imports anchored to the
importing module's real package path.

**Dogfooding moment:** the first whole-toolkit scan found TWO genuinely dead symbols at high
confidence - `NameUseCollector` (orphaned by this very rewrite) and `vectorize` (deprecated
lexical wrapper) - both verified zero-reference and removed. G6's first catch was G6's own
refactor residue.

### Defects found by self-run and fixed during the tranche
1. **Subtree alias regression**: scanning root=src left `src.core.config` imports unresolved
   (the old aliases dict was dropped) -> boundary audit read 0 crossings, dead_code called
   `resolve_paths` dead. Fixed with alias forms; src/ now shows the true 35 crossings.
2. **Nested defs unresolvable** -> lexical `_local_lookup` (enclosing-scope walk).
3. **`foo().bar` chains lost the use of `foo`** -> non-Name chain bases are re-visited.
4. **Confidence cascade**: helpers called only by NodeVisitor `visit_*` methods (dynamically
   dispatched) read as high-dead clusters -> the two-tier reachability fix.
5. **Harness truthfulness regression caught the ABC bait**: `normalize_name` (live via
   interface) scored medium = FALSE_POSITIVE. Fixed BY CONSTRUCTION: base classes are resolved
   onto class symbols; an override of a rooted (abstract) method is itself a root, transitive
   over the base chain. Truthfulness back to 0 FP / 0 missed - and the fix is knowledge, not
   muting.

### G5 — per-node summaries ✅ (rides O1)
`symbol_graph action=summarize`: one-sentence purpose per module via the governed inference seam
(`purpose: node.summary` in the usage log), **CAS-cached by file sha256** - proven: 22 modules
summarized live on src/, second run 0 inference calls. `refs` answers now carry the module's
cached summary, so "who calls this and what is its module FOR" is one call. Degrades honestly:
no backend -> `degraded: true` + the exact missing list, never an invented summary (regression-
tested under SUITE_LLM_DISABLE). `attach` pre-binds the next step for python targets: summarize
once if no cache, stats afterwards.

**State:** 90 tools - smoke **75 pass** + 1 environmental - ruff clean - truthfulness 0 FP / 0
missed - seam 18/18 + seam_complete=True - toolkit self-scan: 0 high candidates (the two real
ones were removed), 39 labelled leads.

**Next:** D3 - M1 (Linux CI read-only mount), then B1 (BCC sweep) if ever.

---

## D3 - DONE 2026-07-20. All planned work is now complete.

### M1 - real read-only mount (PREVENTION, not detection) ✅
New `_harness/ro_mount.py` + `_harness/ro_probe_inner.py` + `harness.py mount <target>`.
Phase 4 shipped detection (snapshot/diff catches a violation after it lands). M1 closes the other
half: the target is mounted read-only, so the OS refuses the write and the violation cannot happen.

**Measured on this machine, not asserted.** Three mount approaches were tried before one was
chosen: plain `bind` + `remount,ro` FAILS inside a user namespace (inherited mounts are locked),
and unprivileged overlayfs FAILS too. What works unprivileged is a tmpfs created *inside* the
namespace, then sealed. So there are two strategies: `bind` (root/CI, mounts the REAL target, no
copy) and `userns-tmpfs` (unprivileged). Proven via WSL:

```
capability: available=True strategy=userns-tmpfs
rig self-test: readable=True write_refused=True
mount sealed:        True  ([Errno 30] Read-only file system)
violation PREVENTED: True  (call_ok=False file_created=False)
sidecar still usable: attach OK / glob OK / repo_search OK / report OK
source target unchanged: delta=0
MOUNT       PASS
```

**The second check is the one that matters.** Prevention that breaks the instrument proves
nothing worth having, so the probe also demands that `attach`/`glob`/`repo_search`/`report` all
still succeed against a target they physically cannot write. Together the two checks are the
roots contract stated mechanically: the sidecar reads the target, writes only its own home, and
the OS - not the author's discipline - enforces it.

**The rig self-tests before it reports.** It writes a file, seals the mount, and demands EROFS.
A probe that assumes its own instrument works is how you ship a green light over a broken rig.

**Honest-skip contract:** on Windows/macOS the command prints `UNAVAILABLE` *with a reason* and
exits 0. A skipped dimension must never read as a pass. Verified on Windows.

**No CI workflow file was committed, deliberately.** This tree is not a git repo, so a workflow
could not be run or verified here; shipping unverified config is the same failure in a different
costume. The ready-to-paste job is in `_harness/README.md`.

**Deployment finding:** a read-only target forces the sidecar OUT of the target directory - the
normal `<target>/.useful-helpers/` layout needs to write its own state. M1 therefore models the
AUDIT posture (external sidecar, `SUITE_PROJECT_ROOT` -> sealed target), which is what CI and
forensic review want. It does not model in-target deployment, and the docs say so.

### B1 - the `BCC` sweep ✅ (and a correction to this plan)
**The earlier entry in this document was wrong.** It described B1 as "core modules are annotated;
the ~89 adapters are not - pure consistency, acceptable to never do." The truth is the opposite:
`BCC` was a "binding contract" document that **no longer exists anywhere in the tree**, and 13
code comments still cited it by section number. Every one told the next reader to go consult
something unfindable. That is not a consistency nit; it is the same defect class as a tool
reporting a confidence it cannot support.

Fixed by stating each principle **inline**, which is what a comment should have done in the first
place - e.g. "never import tool code (BCC sec 2)" became "never import tool code (adapters are
subprocesses, not imports)". 13 citations, 0 remaining.

### ASCII convention completed into source
The convention (manifests -> shipped docs -> now source) is finished: 55 `.py` files swept of
prose typography; every shipped doc, manifest, and source file is ASCII **except two deliberate
keeps**, verified individually:
- `tools/linenumber/cli.py` keeps `U+2502` - it is the gutter the tool EMITS *and* what its strip
  regex MATCHES. A blind sweep would have broken the annotate/strip round-trip. (Round-trip
  re-verified: identical.)
- `src/ui/*_view.py` keep `U+2713` - Tkinter labels, where Unicode renders fine.

The sweep also introduced trailing whitespace where an em-dash ended a line - **caught by the
toolkit's own `test_self_lint_clean`**, which is the suite doing its job on its own codebase.

**FINAL STATE: 90 tools - smoke 75 pass + 1 environmental (`git_inspect`: no `.git` in sandbox) -
ruff clean - truthfulness 0 FP / 0 missed - seam 18/18, `seam_complete=True` - six-kind sweep
green, precept delta 0 - M1 MOUNT PASS on Linux, honest UNAVAILABLE on Windows.**

Nothing planned remains. The C-series acceptance (an agent never leaves the seam) and the
D-series (governed inference, refresh-proof policy, resolved symbol graph, node summaries,
prevention-grade precept) are all met and measured.

---

## E3 - Project Genesis: "Start New" as a first-class entry (2026-07-23)

**The correction being converted:** the sidecar was born attach-existing-centric - it maps a
project that already exists. But an empty workspace with only an intention is an equally valid
entry. E3 makes "Start New" first-class and converges it onto the SAME observe->act loop as
"Attach Existing." The distinction is initial evidence density, not project type.

### What ships
- **`genesis` tool** (Apply / writes: toolkit) - the Start-New front door. Takes an `intent`
  string (required), optional `name`, `authority` hint, and `profile` hint. Records a durable
  **workspace identity** at `<state_root>/workspace.json` (id + name + intent + authority +
  profile_hint + created_at) and **seeds the first journal entry** through the governed seam.
  **No domain/profile is required** - that is the whole point. Preview-first; refuses to clobber
  an existing workspace identity without `overwrite`.
- **`attach` becomes evidence-density aware.** It now:
  - reads `workspace.json` and surfaces `intent` + `workspace` in the PROJECT_MAP;
  - computes `evidence_density` (empty / nascent / sparse / populated);
  - when the workspace is nascent, frames the domain as a **suggestion** (not an identity) and
    returns growth-oriented `next` steps (journal -> scaffold_project -> re-attach) instead of
    code-analysis steps that are pointless with no code yet;
  - handles an empty target gracefully instead of misclassifying it.

### The convergence (why this is one loop, not two)
`genesis {intent}` seeds state -> `attach` reads that state and maps the workspace at whatever
density it has now -> as `scaffold_project` and real work add artifacts, `attach` re-maps and the
same `journal` thread runs unbroken from intent to artifacts. Attach-existing is unchanged: no
`workspace.json` -> today's behavior exactly (no regression).

### Precept
`genesis` writes ONLY sidecar state (`workspace.json` in the state root) + the journal - nothing
into the target's own tree. The workspace's identity/intent is the sidecar's memory of what the
project is trying to become, not an artifact imposed on the project. Scaffolding real files stays
`scaffold_project`'s job (a separate Apply/target step the agent runs next).

### Acceptance (measured)
1. Empty folder + intent -> coherent workspace (identity + intent + authority + first journal
   entry), no domain required.
2. `attach` on that workspace reports evidence density + intent and OFFERS a profile; it does not
   force a type, and does not error on emptiness.
3. Full slice proven end to end: empty -> genesis(intent) -> scaffold a file -> attach re-maps ->
   journal shows one continuous thread.
4. The six-kind cartridge sweep and attach-existing path stay green (profile-as-suggestion does
   not break classification of real projects).
5. `genesis` smoke test; registry/docs refreshed; vend parity re-verified.

### Deliberately deferred (later tranches, keep this slice bounded)
- **E4** - recovery as normal operation: operation IDs, checkpoints, park/wake. (Genesis is where
  interruption-recovery stops being optional, but it is its own tranche.)
- **E5** - formation provenance: record operationally-created relations (artifact exists because
  of this intent -> work order -> sources). The payoff of the New-Project story.
- The interactive planner UI that chains genesis -> scaffold -> install -> journal.

### E3 review pass (2026-07-23) - one fix
- **Reengage consistency bug (fixed):** re-engage recomputed `evidence_density`/`nascent` from the
  current probe but loaded `domain_status` stale from the stored map. A workspace mapped while
  nascent, then grown, briefly reported `nascent:false` with `domain_status:"suggested"` until the
  next full refresh. Now `domain_status` is recomputed alongside density so they can never
  contradict. Guarded by a re-engage assertion in `test_e3_genesis_start_new`.
- Verified: 92 tools, smoke 80 pass + 1 env, ruff clean, six-kind sweep + seam 18/18 green, vend
  parity re-checked, installer package refreshed (ships 92 incl. genesis).

**E3 STATE: DONE + reviewed.** Start-New is first-class; empty->genesis->attach(nascent)->grow->
attach(detected) proven with the intent thread unbroken; attach-existing unchanged.

---

## E4 - Recovery as normal operation (planned 2026-07-23)

**The gap being converted (review sec 17, our weakest area):** the event log is per-invocation
audit only (`tool, authority, ok, exit_code, args_hash, error`) - no operation identity, no
checkpoints, no way to resume a multi-step effort after interruption. Today "recovery" = the next
agent reads the journal. For a project-forming session (exactly what E3 enables), interruption is
normal, not exceptional, and it happens at specific, recoverable points.

### What ships
- **An `operation` record class** in the state root: a durable, append-only ledger of multi-step
  operations. Each operation has: `op_id`, `title`, `intent/goal`, `status`
  (open/paused/done/failed/abandoned), `created_at`, `updated_at`, and an ordered list of
  **steps**, each step carrying its own `status`, `tool`, `args_hash`, `result_ref`, and a
  **failure class** when it failed.
- **Explicit failure classes** (review sec 17): `proposal_rejected`, `capability_unavailable`,
  `timeout`, `no_effect`, `partial_effect`, `effect_ok_observation_failed`,
  `observation_ok_validation_failed`, `stale_witness`, `malformed_output`, `runtime_crash`.
- **A `checkpoint` / park-wake mechanism:** an operation can be PAUSED with a durable "park packet"
  (what was done, what's next, the witness/signature at pause time) and RESUMED - re-observing
  first to detect drift (`stale_witness`) before continuing.
- **Idempotency by op-step:** a step records an idempotency key (op_id + step_no + args_hash) so a
  resumed operation does not re-run a step whose effect already landed.
- **A `recover` tool** (Observe + Apply actions): `list` open/paused operations, `show` an
  operation's steps + failure classes, `resume` a paused operation (re-observe -> continue or
  report drift), `abandon` one with a reason.

### Convergence with what exists
- The seam's `event_log` stays the raw per-call tape; the operation ledger sits ABOVE it,
  correlating calls into a resumable unit (review sec 23 - the activity record the thin event log
  lacks). An operation step references event_log rows by `args_hash`/time, not by duplicating them.
- `genesis` opens the founding operation of a workspace; `journal` narrates it; the operation
  ledger makes it *resumable*. Three record classes, three truth semantics (review sec 9).

### Acceptance (measured)
1. A multi-step operation can be started, advanced step-by-step, and its state is durable across
   process death (simulated crash) - `recover list` shows it paused, not lost.
2. `recover resume` re-observes the target first: if the witness changed since the pause, it
   reports `stale_witness` with the drift rather than blindly continuing.
3. A step whose effect already landed is NOT re-run on resume (idempotency key honored).
4. Each failure maps to an explicit class, not a generic "failed".
5. Operation ledger is separate storage from journal/evidence/event-log (no truth-class collapse);
   smoke test for the full start->pause->crash->resume->finish lifecycle; six-kind sweep + seam
   stay green; vend parity re-verified.

### Deliberately deferred to E5
Formation provenance (operationally-created relations: artifact exists because of intent -> work
order -> sources). E4 makes operations *resumable*; E5 makes their *outputs traceable*.

### E4 - DONE 2026-07-23
**Shipped `operations_shared.py` + `operation` tool** (Apply/toolkit; ledger at
`<state_root>/operations.sqlite3`). Recovery is now normal operation:
- **Durable across crash:** start an operation -> advance steps -> the connection can die at any
  point and `operation list {status:paused}` still shows it, not a lost conversation. Proven by
  dropping the DB connection mid-lifecycle in the smoke test.
- **Resume re-observes first:** `resume` takes a witness (signature of the target's files+sizes) at
  pause time and recomputes it on resume. An external edit while paused -> `resumed:false`,
  `failure_class:"stale_witness"` with the drift, instead of continuing onto a changed world.
- **Idempotency by op-step key:** re-recording a step whose `idempotency_key` already landed
  returns `idempotent_hit:true` and does NOT re-apply it - a resumed operation cannot double-run.
- **Explicit failure taxonomy:** a `status:failed` step REQUIRES a `failure_class` from the closed
  set (proposal_rejected / capability_unavailable / timeout / no_effect / partial_effect /
  effect_ok_observation_failed / observation_ok_validation_failed / stale_witness /
  malformed_output / runtime_crash). A generic "failed" is refused.
- **Separate truth class:** the ledger is its own storage above the event log (which stays the raw
  per-call tape) and separate from journal/evidence - no truth-class collapse.
- **Convergence:** `genesis` now suggests `operation start` as a next step (kept decoupled - the
  agent opens the founding operation; genesis does not auto-couple to it).

**Acceptance MET:** full start->advance->pause->simulated-crash->list-shows-paused->resume-
reobserves->idempotent->explicit-failure-classes lifecycle proven (`test_e4_recovery_lifecycle`),
CLI wired through the seam. 93 tools, smoke 81 pass + 1 env, ruff clean, six-kind sweep + seam
18/18 green, vend parity re-verified, installer refreshed (ships 93).

**E-SERIES STATUS:** E1 scaffold_project, E2 installer/vend, E3 genesis (Start-New), E4 recovery -
all DONE. Remaining: **E5 - formation provenance** (operationally-created relations: artifact
exists because of intent -> work order -> sources; review sec 22). Then the interactive planner UI
that chains genesis -> scaffold -> operation -> install -> journal.

## E5 - Formation provenance: why does this exist? (DONE 2026-07-23)

**The gap converted (review sec 22):** the sidecar recorded DISCOVERED relations (code<->code via
symbol_graph, code<->knowledge via bd_why) but for a project that BEGAN here, the important
relations are CREATED by our work and were invisible - a draft existed with no record of the
intent that motivated it, the sources that supported it, the outline it came from, or who accepted
it. E5 makes formation history durable and traceable.

### Shipped
`provenance_shared.py` + `provenance` tool (Apply/toolkit; ledger at
`<state_root>/provenance.sqlite3`). Entities + typed directed edges.
- **Enforced ORIGIN on every relation** - the closed set `discovered | operational | interpretive`.
  That contract is the point: the system never confuses what it FOUND with what it CREATED with
  what a model GUESSED. The relation vocabulary itself is OPEN (compact recommended set;
  unknown relations warn but are allowed) - review sec 24, do not freeze an ontology early.
- **Higher-order activities** (review sec 23): an activity is a first-class entity whose roles
  (requested_by / used / generated / approved_by / validated_by / ...) are edges to participants,
  so a multi-participant event stays coherent instead of decaying to pairwise edges.
- **`trace`** - the payoff: backward-walk from an artifact to the chain that formed it. When it
  hits an activity it exposes ALL participants (approvals and validations are part of WHY, not just
  inputs) but only recurses on the input roles.
- **Converges with E4:** activities/edges carry the `op_id` from the operation ledger; separate
  storage from journal/evidence/operations - a distinct truth class (review sec 9).

### Acceptance MET
- The review's example chain (question -> motivated -> work_order -> retrieved -> source ->
  supported -> claim -> used_in -> outline -> generated -> draft) is recorded and `trace(draft)`
  reaches the originating question.
- A multi-participant activity is recorded and `trace(final draft)` surfaces generated + used +
  approved_by + validated_by.
- A bad origin is refused; the three origins are distinguished in storage.
- `test_e5_formation_provenance` (module-level + CLI-through-seam, state-isolated). 94 tools, smoke
  82 pass + 1 env, ruff clean, six-kind sweep + seam 18/18 green, vend parity re-verified,
  installer refreshed (ships 94).

### Review pass this tranche (one fix)
- **trace hid approvals/validations:** it recursed on input roles only and thus never listed an
  activity's `approved_by`/`validated_by` participants. Fixed to expose ALL activity participants
  (recursing only on inputs). Guarded by the activity assertion in the smoke test.
- **Test state isolation:** the E4 and E5 CLI-through-seam checks wrote to the REAL `_state`; both
  now set a temp `SUITE_STATE_ROOT` so the suite leaves no operations/provenance residue. Verified.

**E-SERIES COMPLETE:** E1 scaffold_project, E2 installer/vend, E3 genesis (Start-New), E4 recovery,
E5 formation provenance - all DONE. The New-Project substrate is whole: begin from an intention,
grow with structure, survive interruption and resume safely, and trace any output back to why it
exists. Optional remaining: the interactive planner UI that chains genesis -> scaffold -> operation
-> provenance -> install -> journal (an orchestration over tools that now all exist).

## E6 - The planner ENGINE (headless orchestration; "engine before cockpit") - planned 2026-07-23

**Outcome:** one tool takes a human's intent + a proposed project map and drives the whole New-
Project flow - genesis -> scaffold -> provenance -> journal - as a SINGLE resumable operation, so a
human (via an agent) goes from "I have an idea" to "a real, structured, governed, memory-backed,
provenance-tracked project exists" without touching those tools individually. Adds NO new
substrate: it is orchestration, and the first real CONSUMER of E4 (operation) + E5 (provenance),
which validates that they compose.

### Shipped: `plan` tool (Apply/target)
Actions:
- `propose` {intent, name, archetype?}: draft a project map from intent via the local model
  (llm_shared); degrades honestly to an archetype when no model (degraded:true). Optional Brain step.
- `preview` (default / build without apply): validate the map (scaffold_shared) and show the FULL
  plan - genesis record, scaffold tree, provenance edges, journal seed - writing NOTHING.
- `build` {intent, name, map, root?, apply:true}: execute as a resumable operation. Opens an
  operation (E4), then runs each stage THROUGH THE SEAM, recording an idempotent operation step:
    genesis (required) -> scaffold_project create (required) -> provenance note+activity
    (best-effort) -> journal seed (best-effort) -> operation finish.
- `resume` {op_id, apply:true}: continue an interrupted build - already-done steps are skipped via
  their idempotency keys (nothing re-run), remaining steps execute.
- `status` {op_id}: show the build's operation + steps.

### Design guards (do not become a monolith - review sec 5)
- The planner OWNS no logic of the tools it sequences; it CALLS them through the governed seam
  (subprocess), exactly like delegate. Each stage is one seam call + one operation step.
- Preview-first + one apply for the whole batch (batch-consent).
- genesis "already initialized" is treated as a satisfied step (idempotent), so resume is clean.
- genesis + scaffold are REQUIRED (a failure fails the operation with a class); provenance +
  journal are best-effort (recorded, never block the build).
- The agent (or, later, the cockpit's local model) proposes the map; the planner never DECIDES
  what the project should be. Judgment stays outside; the planner is the instrument.

### Acceptance (measured)
1. `build` with an explicit map creates the real tree AND: workspace.json (genesis), an operation
   with recorded steps (E4), a provenance chain where `trace(project)` reaches the intent (E5),
   and a seeded journal entry - all from one call.
2. `resume` after a completed build re-runs NOTHING (idempotency), and a second build into the same
   target does not duplicate work.
3. `propose` degrades honestly with no model (archetype map, degraded:true).
4. `preview` writes nothing.
5. Smoke test (integration, state-isolated); six-kind sweep + seam green; vend parity re-verified.

### Deferred to E7 (the cockpit)
The Tk `planner_view` wizard (intent -> proposed structure -> review -> build), a sibling of
installer_view, launched by `run.bat plan`. Uses this engine + the local model as its Brain.

### E6 - DONE 2026-07-23
Shipped `plan` tool (Apply/target) - the planner ENGINE. Pure orchestration over the seam; adds no
substrate. PROVEN (test_e6_planner_engine + manual):
- `build` from one call created the real tree AND workspace.json (genesis) AND an operation with
  recorded steps (E4) AND a provenance chain where `trace(project)` reaches the intent (E5,
  7-step chain) AND a seeded journal entry. All four stages green in one operation.
- `resume` re-ran NOTHING - every stage skipped via its idempotency key.
- `propose` degraded honestly with no model (archetype map, degraded:true).
- `preview` wrote nothing.
First real consumer of E4 (operation ledger) + E5 (provenance) - validates they compose.
95 tools, smoke 83 pass + 1 env, ruff clean, six-kind sweep + seam 18/18 green, real _state stays
clean (E4/E5/E6 CLI tests state-isolated), vend parity re-verified, installer ships 95.

**ENGINE DONE. Cockpit (E7) is the only remaining piece:** the Tk `planner_view` wizard
(intent -> proposed structure -> review -> build), sibling of installer_view, launched by
`run.bat plan`, driving THIS engine with the local model as its Brain.

## Pre-cockpit review pass (2026-07-23)
A tidy/harden pass before the E7 cockpit goes on top. Dogfooded dead_code (0 high-confidence
dead), scanned for bare excepts (none), unused constants (none), DB close-discipline (all clean),
TODO/FIXME (all intentional boilerplate emitters).

### Streamlined (duplication removed - BCC anti-duplication)
- **`seam_call(tool, args, timeout=)` -> `tools/_toolkit.py`.** delegate, genesis, and plan each
  had their own copy of the "invoke another tool through the governed CLI (subprocess)" helper.
  One owned helper now; three callers reduced to one-liners (~35 lines of duplication gone).
- **`first_json_object(text)` -> `tools/_toolkit.py`.** delegate and plan both parsed "the first
  balanced {...} out of model output". plan's copy was the NAIVE one (broke on braces inside
  strings); both now use the string-aware version. A latent correctness bug in plan's propose
  parsing is gone as a side effect.

### Frailty fixed
- **operations_shared.record_step empty-key collision.** An empty-string idempotency_key is falsy,
  so it skipped the dedup check yet still INSERTed; two such steps would violate UNIQUE(op_id,
  idempotency_key) and raise. Now normalized `idempotency_key = idempotency_key or None` (SQLite
  allows many NULLs, only one ""). Verified: two empty-key steps no longer collide.

### Docs de-staled
- **README.md** hardcoded "90 headless tools" (was 95). De-hardcoded to point at `run.bat list`
  (the clean_app template already did this) so the count can never drift again. Confirmed no other
  hardcoded counts in any shipped doc; TOOLS.md/registry regenerated (95); drift + dangling-link
  tests green.

### State after the pass
95 tools, smoke 83 pass + 1 env (84), ruff clean, six-kind sweep + seam 18/18 green, vend parity
re-verified, installer refreshed. Codebase is tidy and ready for the E7 cockpit.

## E7 - The COCKPIT: planner_view (Tk wizard over the E6 engine) - planned 2026-07-23

**Outcome:** a human opens a window, states an intent, curates a proposed structure, reviews, and
clicks Build - and a real, governed, memory-backed, provenance-tracked project exists. Pure UI over
the proven `plan` engine (E6); adds no new logic. Sibling of installer_view; launched by
`run.bat plan`.

### Shipped
- **`src/ui/planner_view.py`** - single-panel view (mirrors installer_view's dumb-shell + worker-
  thread + queue/poll pattern). Sections: Intent (Text) + Name + Subfolder (created inside the
  current workspace) + optional archetype. Buttons: **Propose** (plan propose -> fills an EDITABLE
  map box; degrades to an archetype with a note when no model), **Preview** (plan preview -> shows
  the whole plan, no writes), **Build** (plan build apply -> progress per stage + a provenance
  trace hint + Open-folder). All calls cross the one governed invoke() seam on a worker thread.
- **`app_ui.run_planner` + `run_planner_probe`** and **app.py `plan` + `plan-probe` modes** and
  **`run.bat plan`** - wired exactly like the installer.

### Design guards
- Dumb shell: no planning/build logic in the view; the `plan` tool owns it (the view only routes).
- The map box is editable JSON - the human curates the proposed structure before anything is built
  (the "translate abstract intent into functional structure" moment, made visual).
- Preview-first: nothing is created until Build; Build shows per-stage progress from the engine's
  trail; honest degradation surfaces (no model -> archetype, with the note shown).
- Precept-clean: creates within the work target (project_root) at the named subfolder - the engine
  and its roots confinement are unchanged.

### Acceptance
- The window builds; the headless PROBE (`plan-probe`, mainloop-free) drives one `plan propose`
  through the real view and exits 0 (the ui-probe pattern this project already uses for CI safety).
- Manual: Propose -> edit -> Preview -> Build produces a project + workspace + operation +
  provenance trace + journal (the E6 acceptance, now through the GUI).
- Smoke test for the probe; six-kind sweep + seam green; vend parity re-verified.

### E7 - DONE 2026-07-23
Shipped `src/ui/planner_view.py` (the cockpit), wired via `app_ui.run_planner`/`run_planner_probe`,
`app.py` `plan`/`plan-probe` modes, and `run.bat plan`. Dumb shell over the E6 `plan` engine - no
planning/build logic in the view. Flow: Intent + name + subfolder + optional archetype ->
1. Propose (fills an EDITABLE JSON map box; archetype fallback w/ note when no model) ->
2. Preview (whole plan, no writes) -> 3. Build (per-stage progress from the engine's trail) ->
Open-folder. All calls cross invoke() on a worker thread (installer_view pattern).
PROVEN: plan-probe (mainloop-free) builds the real window + drives one propose + exits 0
(test_planner_probe_renders_and_proposes); a full headless drive (propose -> build) created a real
project + workspace.json into a temp target. Docs: README/ONBOARDING/ARCHITECTURE/AGENTS entrance
lists + run.bat help now include `run.bat plan`. 95 tools, smoke 84 pass + 1 env (85), ruff clean,
sweep + seam 18/18 green, vend parity re-verified (cockpit + run.bat plan ship), installer refreshed.

## E-SERIES COMPLETE (E1-E7). The New-Project substrate, its headless engine, AND its human cockpit
are all done. A human can now: open `run.bat plan`, state an intention, curate the proposed
structure, and build a real, governed, memory-backed, provenance-tracked, resumable project - or an
agent can drive the same `plan` engine headlessly. Nothing planned remains.
