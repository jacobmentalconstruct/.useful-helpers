# 0018 — Full Project Audit

- **Date:** 2026-08-09
- **Tranche:** none — review requested before T5a implementation
- **Method:** discovery pass over a fresh clone, no environment variables. Census,
  differential, and the project's own code-intel tools. Everything below was
  **measured**; where it was not, it says so.

---

## 0. First, the fix

`gates/run.py` globbed `t[0-9][0-9]_*.py`, which cannot match
`t05a_observe_select.py`. Widened to `t[0-9][0-9]*_*.py`; protocol §3.1 now
specifies `t<NN>[<variant>]_<slug>.py`. Verified:

```
discovered: t00_foundation t01_ship_manifest t02_ledger_presence
            t03_live_channel t04_cancellation t05a_observe_select
```

---

## 1. SEVERE — findings that make a green result untrue

### 1.1 The harness's cleanliness check is calibrated to a different project

```python
_harness/harness.py:48
LINEAGE = ["mindshard", "parts-bin", "uimapper", "appfoundry",
           "bdneural", "legacy-helpers"]
```

This project's predecessors are `_ProjectMAPPER`, `_TokenizingPATCHER`,
`_MicroserviceLIBRARY`, `_NoStringsPDF`, `_TempServerMAKER`, `_UiMAPPER`,
`_BDHyperNeuronEMITTER`, `_BDHyperNodeSPLITTER`. **Five of the six terms cannot
match anything here.** `CLEANLINESS PASS (0 lineage hits)` is a false negative
produced by searching for another project's vocabulary.

I quoted that pass as evidence in **0014 §3**. It was worth nothing.

Scanning the **actual 280-file payload** for this project's real lineage:

| Term | Files | Where |
| --- | --- | --- |
| `_harness` | 5 | `.gitignore`, `ruff.toml`, `.github/workflows/verify.yml`, `tests/test_smoke.py` |
| `.bcc` | 4 | `ruff.toml`, `.gitignore`, `templates/…tmpl`, `payload.py` |
| `toolkit/` | 3 | `.gitignore`, `tests/test_smoke.py`, `payload.py` |
| `AppJOURNAL` | 3 | `templates/…tmpl`, `tools/_toolkit.py`, `payload.py` |
| `plans-and-parts` | 2 | `ruff.toml`, `payload.py` |
| `SUITE_TEST_TMP` | 2 | `.github/workflows/verify.yml`, `tests/test_smoke.py` |
| `_ProjectMAPPER` | 2 | `apps/projectmapper/cli.py`, `tests/test_smoke.py` |
| `_UsefulHelperSCRIPTS`, `_NoStringsPDF` | 1 each | `.gitignore` |

**E11 — "vends fully blank" — is not met.** The scoreboard says **MET, gated**.
Some of these are legitimate (`payload.py` must name what it excludes, and it ships
because a vended sidecar can vend itself). Most are not.

**Fix:** derive `LINEAGE` from `payload.NEVER_SHIP` and `FOREIGN` rather than
hardcoding it, so the check cannot drift from the project it is checking.

### 1.2 The contract already ships — and the shipped copy has diverged

`templates/BUILDER-CONSTRAINT-CONTRACT.md.tmpl` **exists, ships today, and carries
the four `{{BCC_*}}` placeholders.** Journal 0002 recorded it: *"The BCC now ships
inert."* `gates/t00_foundation.py:167` asserts its presence.

So there are **two contracts**, and after yesterday's amendments they no longer
agree:

```
.bcc/BUILDER-CONSTRAINT-CONTRACT.md   42,294 bytes   17-step loop, operator approval: YES
templates/…md.tmpl                    37,052 bytes   17-step loop, operator approval: NO
```

**The sidecar currently ships a contract one day out of date**, and nothing detects
it. Two consequences:

- **0016 was partly wrong, again.** I designed `GOVERNANCE_CARTRIDGE` around
  `.bcc/BUILDER-CONSTRAINT-CONTRACT.md` — *the resolved copy that must never ship* —
  while the blank template that solves the same problem already existed and already
  shipped. The cartridge should name the **template**.
- The template is **inert in the strongest sense**: nothing reads it. No tool
  resolves its placeholders. It ships as a file the target can only apply by hand.

### 1.3 The shipped CI workflow runs a stripped directory

`.github/` ships. `verify.yml` runs `python gates/run.py` in two jobs — and `gates`
is in `PAYLOAD_EXCLUDE`. A vended sidecar carries a workflow that cannot pass.

It lands at `<target>/.useful-helpers/.github/`, which GitHub does not read, so it
is **dead weight and lineage rather than breakage**. It should not ship.

---

## 2. HIGH — structural

### 2.1 E9 does not do what it says

> E9 — *"The parts bin can be deleted and everything still passes."*

```
.plans-and-parts_FOR-REFERENCE-ONLY   530 tracked files    8.4 MB
_harness/targets/_UsefulHelperSCRIPTS 639 tracked files   11.0 MB   <- 7 of the same apps
```

Deleting the parts bin leaves a **larger duplicate** of seven of its applications
committed under `_harness/targets/`. E9 will pass and the repository will still
carry the predecessors. The condition needs restating, or the harness needs to
scaffold its targets rather than store them.

### 2.2 Nothing keeps the two contracts in sync

No gate compares them; §1.2 is the result, within one day. Any fix to §1.2 that does
not add an assertion will simply recur.

### 2.3 `tests/test_smoke.py` — 3,289 lines, **one class, 89 methods**

`setUpClass` monkeypatches `tempfile.tempdir` and `tempfile.mkdtemp` **globally for
all 89 tests**. That is precisely what produced 0014's three-test failure. One
fixture decision, no isolation, and a shared-state blast radius covering the entire
suite.

### 2.4 Our own bar, unmet in our own gates

| File | Lines | Note |
| --- | --- | --- |
| `tools/attach/cli.py` | 1,017 | largest tool |
| `tools/bd_graph_shared.py` | 851 | |
| `gates/t00_foundation.py::check` | 230 | one function |
| `gates/t01_ship_manifest.py::check` | 195 | |
| `gates/t02_ledger_presence.py::check` | 171 | |

**Good news, measured:** `src/` is clean. Worst complexity score is
`invoke._dispatch` at 56, then `app.main` at 53. No god objects in the control
plane.

---

## 3. MEDIUM — staleness

- **`.gitignore`** (which ships) still describes the pre-collapse layout: lines 5–8
  explain a `toolkit/.gitignore` that no longer exists; line 51 ignores
  `toolkit/config/registry.json` — dead, with the live rule duplicated at line 176;
  line 58 says *"The harness copies toolkit/ into…"*.
- **`docs/` vocabulary.** `toolkit` appears 51× in `TOOLS.md`, 11× in
  `ARCHITECTURE.md`, 8× each in `OPERATIONS.md` and `AGENTS.md`. **Not all stale** —
  "toolkit" is legitimate as the authority/`writes:` vocabulary and as a common noun.
  This needs a pass separating the concept from the removed directory, not a
  find-and-replace.
- `apps/` contains one tool (`projectmapper`) and one README; T8 retires it. It
  ships today.
- `tools/stamp` emits `"TODO: describe {tool_id}"` into generated tools — template
  debris that can reach a target.
- **17 unpushed commits, 14 modified files.** CI has still never run, so the Windows
  half of verification remains hypothetical — and it is now the only path that
  exercises the default configuration.

---

## 4. The largest finding: the sidecar does not use itself

The project owns tools built for exactly the review just performed:

```
complexity_score  dead_code  module_decomp_plan  import_graph  symbol_graph
domain_boundary_audit  blocking_call_scan  secret_audit
tkinter_widget_tree  ui_callback_graph  workspace_audit  file_tree
```

**Every one of them is referenced only by `tests/test_smoke.py`** — as a subject to
be smoke-tested, never as an instrument applied to this project. I wrote an ad-hoc
AST script for §2.4 while `complexity_score` sat in the registry. Same failure as
ignoring `_harness/` for four tranches.

**And at defaults they are useless here.** Every one reports `files: 500` — a cap
consumed by the parts bin and `_harness/targets`:

```
complexity_score   top 25 hotspots: all foreign
dead_code          2,221 candidates: all foreign
blocking_call_scan 231 informational: all foreign
```

Scoped with `{"root": "src"}` the same tool returns 26 files, 164 symbols, and the
clean result in §2.4. **`payload.FOREIGN` exists and nothing wires it into tool
defaults.**

### Opportunities that bear directly on T5a

**`config/domain-boundary/` ships containing only a README.** The profile directory
is empty, so `domain_boundary_audit` reports `verdict: "none (no policy supplied)"`
and `available_policy_profiles: []`. There is no `.uh-policy.json`.

This project has a *declared* four-layer architecture and a seam every call must
cross — and no machine-readable statement of it. T5a's **Hazard 2** is currently
asserted as `"threading.Thread" not in body`, a string search over one file. A
domain policy would enforce *"no `src/ui` module imports `src.core.invoke`
directly"* mechanically, permanently, for every module written after T5a — not just
the one the gate happens to name.

**`tkinter_widget_tree`** and **`ui_callback_graph`** extract Tk widget structure and
map every `command=`/`bind()` handler. Both are stronger forms of assertions already
written into `gates/t05a_observe_select.py` by hand.

**`blocking_call_scan`** finds calls that stall a thread. Today it only *reports*
sync-context calls as informational; taught about the Tk main thread it would catch
the classic frozen-UI defect that T5a's controller exists to prevent.

---

## 5. Minor

- `ruff.toml` excludes all of `_harness`, while `payload.FOREIGN`'s comment states
  `_harness` is *"ours and should meet our bar"*. A contradiction between two policy
  statements. Harness code is clean today — verified by running ruff with only
  `_harness/targets` excluded — but by luck, not by rule.
- Four `except Exception:` handlers in `src/` (`event_log.py:188,217`,
  `policy.py:34`, `invoke.py:139`). Three carry explicit reasons; `policy.py:34`
  does not.
- The four UI views share only 11 identical non-trivial lines — the duplication is
  structural, not textual, so a copy-paste detector will not find it. Extracting the
  controller (T5a step 1) is still right; the justification is shape, not text.
- `developer_cert.pfx` sits at
  `_harness/targets/_UsefulHelperSCRIPTS/_UsefulHelperScriptsMENU/` and is **not
  tracked**. Lower severity than the backlog implies; still on disk.

---

## 6. Recommended disposition

**Before T5a implementation** — because each changes what T5a should build:

1. Write `config/domain-boundary/` policy for this project's layers. Converts T5a
   Hazard 2 from a string search into an enforced rule.
2. Point `GOVERNANCE_CARTRIDGE` at `templates/…tmpl`, resync it from `.bcc/`, and
   add a gate assertion that the two agree.
3. Derive the harness `LINEAGE` list from `payload.py`.

**Its own tranche — "The sidecar uses itself"** (before or after T5b):

4. Wire `FOREIGN` into code-intel tool defaults; add a `self_audit` playbook
   running complexity, dead code, boundary, secret and blocking-call scans over
   `src/`, `tools/` and `gates/`, as a gate assertion.

**T9:** stop shipping `.github/`; clean `.gitignore` of pre-collapse rules; the
cartridge toggle (E13).

**Restate or reschedule:** E9 (the duplicate under `_harness/targets/`), E11 (not
met — the scoreboard is wrong today).

**Backlog:** split `test_smoke.py`; decompose the three long gate `check()`
functions; `docs/` vocabulary pass.

---

## 7. Reclassification (added by T5, 2026-08-09)

The audit above was written before the ownership model existed, so it graded
everything on one axis. **Ownership and defect type are different questions** — the
same artifact can be correct in the source repository and a leak in the payload — so
each finding now carries a **domain** (Charter §5) and a **disposition**, plus an
**authority role** where it clarifies.

Domains: `source/factory` · `setup-distribution` · `installable-payload` ·
`installed-instance` · `target-owned` · `external-corpus`
Dispositions: `valid` · `stale` · `development-lineage residue` ·
`distribution leak` · `target-boundary violation` · `nonconformity` · `superseded`

| # | Finding | Domain | Disposition | Role |
| --- | --- | --- | --- | --- |
| 1.1 | `_harness` `LINEAGE` searches another project's vocabulary | source/factory | **nonconformity** — a verifier that cannot detect what it claims to | verifier |
| 1.1b | `t01` `PREDECESSOR_NAMES` has the *same* wrong list | source/factory | **nonconformity** — same defect, second site | verifier |
| 1.1c | `_ProjectMAPPER`, `_UsefulHelperSCRIPTS`, `_NoStringsPDF` in payload | installable-payload | **development-lineage residue** | — |
| 1.1d | `"jacob"` in `tests/test_smoke.py` | installable-payload | **development-lineage residue** (builder identity) | — |
| 1.1e | `_harness`, `.bcc`, `toolkit/` named in `.gitignore`/`ruff.toml`/`payload.py` | installed-instance | **valid** — self-knowledge, §5.5. `toolkit/` separately **stale** | consumer |
| 1.2 | Two hand-maintained contracts, diverged | source/factory | **nonconformity** — `BCC-ONE-AUTHORITY` | normative ×2 |
| 1.2b | `templates/…tmpl` inert: nothing resolves its placeholders | installable-payload | **nonconformity** — owed a renderer | generated |
| 1.3 | `.github/` present in the repository | source/factory | **valid** — §5.2, presence in source is not evidence of installability | — |
| 1.3b | `.github/` present in the payload, running stripped `gates/run.py` | installable-payload | **distribution leak** | — |
| 2.1 | `_harness/targets/` — 639 files duplicating 7 parts-bin apps | external-corpus | **nonconformity** — right need, wrong ownership domain (§5.7) | — |
| 2.2 | Nothing keeps the two contracts in sync | source/factory | **nonconformity** | — |
| 2.3 | `test_smoke.py` — 3,289 lines, one class, global `tempfile` patch | source/factory | **nonconformity** (structure) | verifier |
| 2.4 | `attach/cli.py` 1,017 lines; three gate `check()` over 170 | source/factory | **nonconformity** (structure) | — |
| 3.a | `.gitignore` describes the pre-collapse `toolkit/` layout | source/factory | **stale** | — |
| 3.b | `toolkit` vocabulary across `docs/` | installable-payload | **stale** — needs concept/path separation, not find-and-replace | — |
| 3.c | `apps/` ships with one tool | installable-payload | **nonconformity** — one extension shape, not two | — |
| 3.d | `tools/stamp` emits `TODO: describe {tool_id}` | installable-payload | **nonconformity** (template debris) | — |
| 3.e | 17 unpushed commits; CI never run | source/factory | **nonconformity** (process) | — |
| 4.a | Twelve code-intel tools used only as smoke-test subjects | source/factory | **nonconformity** — the sidecar does not use itself | consumer |
| 4.b | `FOREIGN` not wired into tool defaults; every scan saturates at 500 files | source/factory | **nonconformity** | consumer |
| 4.c | `config/domain-boundary/` ships empty; no `.uh-policy.json` | installable-payload | **nonconformity** — a policy engine with no policy | — |
| 5.a | `ruff.toml` excludes all `_harness` while `FOREIGN` calls it ours | source/factory | **nonconformity** (contradiction) | normative ×2 |
| 5.b | `policy.py:34` bare `except Exception` with no reason | source/factory | **nonconformity** (minor) | — |
| 5.c | `developer_cert.pfx` on disk, untracked | external-corpus | **valid** — untracked; still worth removing | — |
| **New** | `packaging/installer/install.py` writes no `.suite_sidecar` | setup-distribution | **nonconformity — severe.** The product's install entrance produces an instance that cannot resolve its target | normative |
| **New** | `tools/sidecar_install` is registered runtime capability | installed-instance | **nonconformity** — §5.5, an instance does not vend instances | — |
| **New** | `installer_view` offers `host_agents` / `gitignore` the tool rejects | installed-instance | **nonconformity** + **stale** — dead precept-violating options | consumer |
| **New** | `_harness` reimplements installation semantics | source/factory | **nonconformity** — §5.3, one installation core | consumer |
| **New** | T1 self-hosting proof | installable-payload | **superseded** — protocol §5.1, retired from active proof | — |

**Every finding fits a domain.** The stop condition in 0019 §6 — a finding that fits
none, meaning the six domains are wrong — was not triggered.

**Four findings changed severity under the model.** 1.1e drops from *violation* to
*valid self-knowledge*; 1.3 splits into a valid source-repo fact and a real payload
leak; 2.1 stops being *bloat* and becomes *correct need, wrong ownership domain*;
5.c drops on measurement (it is untracked, not committed).

---

## 8. Note

Three of the four severe findings are **false greens** — a check that passed while
proving nothing. None came from the gate suite; all came from census and
differential. Recorded as further evidence for protocol §3.4.
