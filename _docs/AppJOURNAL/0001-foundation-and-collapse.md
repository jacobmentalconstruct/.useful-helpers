# 0001 — Foundation, Reset, and the Collapse of the Nesting

- **Date:** 2026-08-06
- **Tranche:** T0 — Foundation and Reset
- **Status:** Parked pending gate
- **Journal:** entry 0001 of this project. Predecessor journals are archived and
  are not this project's history.

---

## 1. Tranche Declaration

**Outcome.** One authority, one numbering, no inherited memory — and one
sidecar rather than a sidecar nested inside a sidecar.

**Non-goals.** No GUI work. No chains. No new capability.

---

## 2. What Changed

### 2.1 Authority

The governing blueprint was retired: it specified a *second* application built
alongside the toolkit, which is not the product. Live authority is now
`CHARTER.md`, `TRANCHE_PROTOCOL.md`, `TRANCHE_PLAN.md`, and the BCC.

Seven superseded control documents, journal entries 0001–0002 of the pre-reset
effort, the factory's `_design/`, and a complete competing plan set (Tranches
0–8, its own CURRENT_STATE, a superseded BCC) were archived under
`_ARCHIVE-PRE-RESET-2026-08-06/`.

### 2.2 Numbering

140 source files carried `TRANCHE:` headers from the toolkit's own build
chronology — 64 distinct identifiers — and 134 claimed `STATUS: DONE`.

Stripped: 141 `TRANCHE:` lines and 134 `STATUS: DONE` lines. **Kept:** the seven
`SCAFFOLD` / `SKELETON` markers. The principle applied was *remove claims of
completion, keep warnings of incompleteness* — a completion claim under a retired
governance regime misleads; a warning protects. Provenance for all 140 files was
captured to the archive before stripping.

### 2.3 Memory

Cleared: toolkit state (event log, journal, LLM usage records), logs, artifacts,
58 harness runs, six regenerable scaffold targets, caches, and the pre-reset git
history. A summary of what the 58 runs established was archived first.

Preserved deliberately: `.bcc/evidence/` holds the 2026-07-18 measurement of the
sidecar against the real daily-driver tree — 143 events, 124 ok / 19 failed, 79
distinct tools. It is the only measurement against real tools.

### 2.4 The nesting collapsed

The repository held a sidecar (`toolkit/`) inside a sidecar
(`.useful-helpers-workbench/`), with two of everything: two READMEs, two
ignore files, two VERSIONs, two test trees.

The objection to collapsing it had been that `toolkit/` was the unit of copy.
That was wrong: **an install manifest already existed** — `EXCLUDE_DIRS`,
`EXCLUDE_SUFFIXES` and `CLEAN_APP_STRIP` in `tools/vendor_export/cli.py`, which
`sidecar_install` already imports. The ship boundary was already a declared list,
not a folder. The folder was redundant with a mechanism the toolkit already had.

`src/`, `tools/`, `apps/`, `config/`, `playbooks/`, `tests/`, `packaging/` and
the root files moved up. `toolkit/_docs` became `docs/` — product-facing
documentation, which the charter already reserved that name for. `_docs/`
remains the sidecar's operational record.

No import changes were needed: `toolkit` was never a Python package, and
`resolve_paths` derives its home from `Path(__file__).parents[2]`, which
resolves correctly from the new location.

### 2.5 Root resolution rewritten

Collapsing the nesting exposed the defect live: with `toolkit/` gone, the
sidecar resolved its work target to `/sessions/.../mnt` — the parent staging
folder — purely because the repository's folder name begins with a dot.

Rewritten to resolve by evidence only, four cases, no fallthrough:

| Situation | Evidence | Target |
| --- | --- | --- |
| Vended into a project | `.suite_sidecar` marker | its parent |
| Explicit root, valid | env names a real directory | that directory |
| Explicit root, invalid | env names nothing | **hard error** |
| In development | neither | **none** — refuse |

The folder-name heuristic is gone. A name is not evidence of installation.

Parent binding was **kept** for genuinely vended sidecars: an installed
sidecar's parent really is its whole reality. The earlier proposal to remove
parent inference entirely was wrong and was corrected before implementation.

`NoTargetBound` is raised for an invalid explicit root and reported as a clean
error, not a traceback. `invoke()` refuses when no target is bound.

### 2.6 Recursion guard

With the sidecar being the root, and harness targets living *under* the root at
`_harness/targets/`, a copy of the root into a target would copy the target into
itself. `_PAYLOAD_EXCLUDE` now excludes `_harness` explicitly as a recursion
guard, alongside the development scaffolding and the parts bin.

The harness's copy-mode install now writes the `.suite_sidecar` marker. It
deliberately skips the installer *tool*, but must still produce a faithfully
installed sidecar — without the marker every call would correctly refuse.

---

## 3. Verification

Executed, not inspected.

| Check | Result |
| --- | --- |
| All 140 stripped files compile | PASS — `compileall` clean |
| Sidecar registers its tools from the new root | PASS — 95 |
| `resolve_paths` finds the sidecar root | PASS |
| Unbound sidecar refuses a call | PASS — `ok: false`, clear reason |
| Invalid explicit root | PASS — clean error, no traceback, no fallback |
| Valid explicit root binds | PASS |
| Marker binds a vended sidecar to its parent | PASS |
| Vend leaks no scaffolding | PASS — 18 product items, none of `_harness`, `gates`, `.bcc`, `_docs`, `_trash`, parts bin |
| Vend does not recurse | PASS — no nested `.useful-helpers` |
| End-to-end: vend, bind, read the target | PASS — bound to the target, listed its real files |
| Precept: target left clean | PASS — target holds only its own files plus the sidecar folder |

---

## 4. Unresolved

- **The vended payload carries the development `.gitignore`.** It should carry a
  minimal one covering its own `_state`, `_artifacts` and `logs`. The original
  toolkit ignore file was discarded in the collapse. Backlog for T1.
- **Two manifests describe what ships** — `_PAYLOAD_EXCLUDE` in the harness and
  `CLEAN_APP_STRIP` in `vendor_export`. They must converge into one.
- **`packaging/` is currently excluded from the vend** by `CLEAN_APP_STRIP`, but
  the installer is now deliverable #1. Its packaging needs revisiting.
- **Windows behavior remains wholly unverified.**
- **`_trash/` is emptied by the host mid-session**, so moves there are permanent
  deletions rather than reversible staging. One unintended loss: a zip *of* the
  parts bin, which still exists on disk.

---

## 5. Park Point

**Completed.** Authority unified, numbering cleaned, memory cleared, nesting
collapsed, root resolution fixed and verified end to end.

**Next.** Run `gates/run.py` and confirm T0 closes. Then T1 — converge the two
vend manifests, ship a minimal payload ignore file, and gate E11 (vends blank).

**Note for the next agent.** The BCC ships as an inert template with placeholders
unfilled, activated by a distinct tool that writes the live contract into the
sidecar's own root, never the target's. The placeholder is the isolation: the
BCC's own bootstrap rule declares an unfilled contract a seed rather than an
authority.
