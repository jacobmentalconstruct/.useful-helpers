# `attach` — walking skeleton results

**Date:** 2026-07-16 · **Status:** proven end-to-end against the toolkit itself.
Implements `CHARTER.md §3 Layer 4`. Companion to `SCRUB_AUDIT.md`.

---

## What was built

| Piece | Path | Role |
|---|---|---|
| The front door | `tools/attach/` | one verb, two paths (map / re-engage) |
| Domain knowledge | `config/cartridges/*.json` | 5 cartridges: python-app, web-app, data-curation, records-research, generic |
| Engagement state | `<state_root>/workbench/{profile,map}.json` | written by `attach`; never touches the target |
| The visible door | `AGENTS.md` | rewritten to lead with `attach`, not a catalog |

Registered as tool **78**, category `orientation`, authority `Observe`. Smoke suite: **59/60**,
unchanged from before (the one failure is `test_git_inspect` — environmental, the sandbox has no
`.git`).

## Verified behavior

```
1. MAP       -> mode=mapped     domain=python-app  files=229   (scored 8.076 vs data-curation 3.903)
2. RE-ENGAGE -> mode=reengaged  stale=False                     (stable, repeatable)
3. RE-ENGAGE -> mode=reengaged  stale=False
4. touch a source file
   RE-ENGAGE -> stale=True   229 -> 230   next[0] = attach{refresh:true}
5. domain override -> records-research, 14 tools mounted
   bad domain     -> ok=false, "unknown domain 'nonsense'"
```

The target-mismatch guard also fired correctly and unprompted: attaching with no `target` while
the workbench was bound to a different folder returned a refusal naming both paths rather than
silently re-mapping.

## What the skeleton was for — two real bugs it caught

Building the thinnest end-to-end version first was worth it. Both of these would have been
baked into a fuller implementation and much harder to see later.

### 1. The instrument observed its own exhaust
The first re-engage reported `stale: True` on an **unchanged** target — 233 files where 231 were
mapped. The two extra files were `workbench/profile.json` and `workbench/map.json`: the map
`attach` had just written. **Mapping the target changed the target.**

This is the field report's A1 finding ("the instrument drowned the project view") reappearing in
a new place. `toolkit_home_names()` prunes the sidecar *by name* when walking past it as a child
— but that prune cannot fire when the target **is** the toolkit home, because the walk starts
inside it rather than descending into it.

**Fixed** via `_self_paths()`: the probe never counts anything the instrument writes.

### 2. Every governed call mutates the toolkit
Even after excluding the workbench, staleness stayed `True`. The culprit:
`_docs/_AppJOURNAL/_journalDB/event_log.sqlite3` — the **governance audit log**, written on
every single `invoke()`. So a self-attached target was stale one millisecond after being mapped,
permanently.

This is `SCRUB_AUDIT.md §5b` biting for real, and it is not cosmetic.

## The finding that matters: there is no STATE ROOT

`tools/_toolkit.py` documents a roots contract with **three** roots — work target, toolkit home,
output root. The field report called this the single highest-leverage fix, and it shipped.

**It is missing a fourth: where durable state lives.** Because no root declares it, state has
scattered:

| State | Current home |
|---|---|
| journal + evidence + event_log DBs | `_docs/_AppJOURNAL/_journalDB/` — *a database inside the docs folder* |
| generated artifacts | `_artifacts/` |
| logs | `logs/` |
| registry (derived) | `config/registry.json` |
| workbench (new) | `workbench/` |

`_self_paths()` currently hardcodes five locations because there is no single one to ask for.
That list is exactly the kind of thing that silently rots when a sixth store appears.

**Recommendation:** add `state_root()` to the roots contract and move durable memory under it.
Then `_self_paths()` collapses to one entry, and "is my target stale?" becomes answerable by
construction rather than by an exclusion list someone has to maintain.

This is now a prerequisite for the graph/RAG work (field report Part G), which will add more
stores — indexes, embeddings, summaries. Doing it before that lands is much cheaper than after.

## Honest limits of the skeleton

Stated in the tool's own output as `map.limits`, deliberately, so no agent over-reads it:

- **Structural only** — it maps SHAPE, not MEANING. No model runs; nothing is read for content.
- **Subsystems are top-level directories by file count**, not identified components.
- **Entry points are filename conventions** from the cartridge, not verified entrypoints.
- Staleness is `(file_count, newest_mtime)` — cheap, and blind to a same-size in-place edit
  that preserves mtime.
- The charter's acceptance bar — *"a fresh agent calls `attach()` and can state the target's
  purpose, architecture, entry points, and subsystems without reading a file"* — is **not met**.
  Shape is not purpose. Meeting it needs the field report's Ga→Gb→Ge tranche (real embeddings,
  line-range provenance, journal/evidence as knowledge nodes).

## First contact with a real target — 2026-07-16

Target: `_UsefulHelperSCRIPTS` — the toolkit's own **ancestor**. A 12-app monorepo
(`_GitPUSHER`, `_MonacoVIEWER`, `_ProjectMAPPER`, `_UiMAPPER`, `_TokenizingPATCHER`,
`_MicroserviceLIBRARY`, …) — the same donor names scrubbed out of the provenance blocks that
morning. 3,212 real files / 316 MB / 396 source `.py`. Not a git repo.

**It misclassified a 396-file Python monorepo as `data-curation`** and mounted the wrong
workbench — 12 data tools instead of 17 Python ones, so `import_graph`, `complexity_score`,
`dead_code` and `module_decomp_plan` never ran at all.

### Root cause: two compounding scoring bugs

| Signal | Score | Reality |
|---|---|---|
| `.py` × 396 → python-app | 3.598 | the actual project |
| `.db` × 2 + `.jsonl` × 4 → data-curation | **5.806** | 0.7% of the tree |

1. **Log damping flattened mass.** `1 + log10(n)` compresses 1→396 into 1.0→3.6, so the raw
   per-extension weight dominated and a *single* file scored nearly full credit. Six files beat
   396.
2. **Markers were root-only.** Every sub-app carries a `requirements.txt`; the monorepo root
   carries none. python-app's decisive weight-5 marker never fired.

Neither is visible on a scaffold — the demo has a clean root with `pyproject.toml`, so markers
win before scoring ever matters. **Only a real, messy target could surface this.**

### Fix
- **Extensions score as a SHARE of the target** (`weight × n/total × 10`), not a damped count.
  Mass is proportional; 0.7% of a tree now reads as the noise it is.
- **Markers are found to depth 2**, counted once at their shallowest occurrence, at half weight
  when nested — a monorepo of Python apps *is* a Python project, just less decisively than a
  root `pyproject.toml`. Counted once, so 12 sub-apps don't score 12×.
- `MIN_CONFIDENT_SCORE` — below 1.0, fall back to `generic` rather than guess.

| | before | after |
|---|---|---|
| python-app | 3.598 | **7.057** |
| data-curation | **5.806** (wrong winner) | 0.138 |

A 1.6× inversion became a 51× separation. Regression-checked: all three scaffold kinds still
classify correctly. Smoke 59/60 (unchanged).

### What this run also confirmed
- **Precept PASS** on a real 3,212-file target — install and runtime deltas both 0.
- **Pruning is correct.** attach saw 396 `.py`, not the 2,443 on disk; the difference is
  `.venv` (5,020) and `site-packages` (2,041), correctly excluded. The naive count was the
  wrong one.
- **Tool health 9/10** — only `git_inspect` failed, because the target has no `.git`. That is
  the tool being right.
- **Cleanliness FAIL, 9 lineage hits** — the §5a donor debt, independently rediscovered.

### The open question this makes urgent
`subsystems` reported `_MicroserviceLIBRARY(558), _NoStringsPDF(55), _TextTOUCHER(44), …` —
correctly identifying 12 independent apps. But **one cartridge was mounted for all of them.**
`_MonacoVIEWER` is a JS/Electron viewer; `_NoStringsPDF` is a PDF tool. They want different
workbenches. Composition (open question 3) is no longer theoretical — the first real target is a
monorepo, and monorepos are normal.

## Resolved — state root + composition (2026-07-16)

### `state_root()` — the fourth root

The roots contract named work-target, toolkit-home, and output-root. It was missing **where
durable memory lives**, so five consumers each hardcoded `_docs/_AppJOURNAL/_journalDB/`
independently, and `_self_paths()` had to enumerate six locations to answer "did the target
change, or was that just me breathing?"

`state_root()` is now in the contract (`tools/_toolkit.py`), mirrored as `Paths.state` for the
seam, overridable via `SUITE_STATE_ROOT`.

**Why it is separate from `output_root()`, not merged:** opposite lifecycles. Artifacts are
regenerable exhaust that `artifact_cleaner` may delete freely. State is the memory that makes
the next agent's session continuous — an update-in-place must preserve it, a clean must never
touch it. `sidecar_install --update` already depended on that distinction but had no way to
express it.

```
_state/journal.sqlite3      _state/evidence.sqlite3
_state/event_log.sqlite3    _state/workbench/{profile,map}.json
```

`_self_paths()` collapsed from six hardcoded paths to four contract calls, and **a new store
added under `state_root()` is excluded automatically — the list cannot rot.**

Verified: after `journal`, `evidence` and `event_log` all write, `attach` still reports
`stale=False`. Previously any one of those writes made a self-attached target permanently stale.
`_docs/_AppJOURNAL/` is gone. Smoke 59/60, ruff clean.

### Composition — a target is often not one thing

`_compose()` classifies every top-level subsystem in its own right, using the same `_score()`
machinery over a narrower slice, gathered on the same single walk. Markers are measured from the
**subsystem's** root, so `backend/pyproject.toml` is a depth-0 marker for `backend` (full
weight) while remaining depth-1 — merely suggestive — for the target as a whole. Subsystems
under `MIN_SUBSYSTEM_FILES` are reported but not classified: too small to judge honestly.

`workbench.mounted` becomes the union of the primary and every subsystem's tools —
**roughly a third of the catalog on the composite target — still selection, not surrender.**
(Since the C-series, every workbench also unions a universal `BASE_MOUNT` of hands.)
`by_subsystem` is the
authoritative view, because a tool's policy is only meaningful against a specific domain
(`import_graph` is trustworthy on the Python subsystem and mute on the JS one). When composite,
`map.limits` says so in the tool's own output.

### What the real target taught us — twice

The 13-app monorepo came back **`composite: False`**, and that is **correct**. Two assumptions
of mine were wrong and the classifier was right both times:

- `_NoStringsPDF` is a **Python app** (16 `.py` + 24 `.png`) that manipulates PDFs — not a body
  of PDFs to research. `python-app` is right.
- `_MonacoVIEWER` is a **Python wrapper** around the Monaco editor; its JS lives in
  `node_modules`, correctly pruned.

It really is 13 Python apps. Which meant composition was still **unproven** — the machinery ran
but never had to fire. Hence `scaffold --kind composite`: a backend/frontend/archive target
whose three subsystems *must* classify as three domains. That is the proof:

```
COMPOSITION  composite=True (expected True) -> True  subsystems 3/3 placed
  frontend   8 files  web-app           24.62
  backend    7 files  python-app        20.71
  archive    5 files  records-research   9.00
```

**A composite target has no meaningful whole-target `domain`** — whichever subsystem carries a
few more files wins, which is noise. The scaffold's ground truth asserts no `expected_domain`
for that reason; asserting one would score the instrument against a category error. The harness
now scores composition as its own dimension.

### Full sweep

| target | precept | domain | composition | tools |
|---|---|---|---|---|
| python-app | PASS | correct | — | 9/10 |
| web-app | PASS | correct | — | 5/6 |
| data-curation | PASS | correct | — | 3/4 |
| records-research | PASS | correct | — | 3/5 |
| composite | PASS | n/a | **3/3 placed** | 9/12 |
| `_UsefulHelperSCRIPTS` (real) | PASS | python-app | correct (not composite) | 9/10 |

## Open questions

1. ~~**State root**~~ — RESOLVED above.
2. **One workbench per sidecar, or many?** Currently singular: one sidecar : one target, and
   attaching elsewhere refuses. Fine for the sidecar model; wrong if one instrument should serve
   several targets.
3. ~~**Should cartridges compose?**~~ — RESOLVED above (per-subsystem classification + union
   mount + `by_subsystem`). What remains is the *narrowing* half: an agent working inside
   `frontend/` still reads `by_subsystem` by hand. An `attach {"scope": "frontend"}` that
   returns only that subsystem's workbench is the obvious next step, deliberately deferred
   until something needs it.
4. **Who writes target overrides?** The profile is generated and overwritten on refresh, so a
   hand-tuned policy would be lost. Overrides likely need their own file. Now more pressing:
   `by_subsystem` policy is generated too, and a real engagement will want to correct a
   subsystem's domain by hand and have it stick.
5. **The union's policy is the primary's.** `workbench.policy` reflects the primary cartridge
   only; per-subsystem policy lives in `by_subsystem`. An agent that reads the top-level policy
   and works in a subsystem gets the wrong confidences. `by_subsystem` being authoritative is
   stated in `map.limits`, but stating it is weaker than making it structural.
