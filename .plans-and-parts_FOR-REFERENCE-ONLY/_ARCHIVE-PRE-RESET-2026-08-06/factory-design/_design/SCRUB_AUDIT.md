# Scrub Audit — 2026-07-16

What was removed from the disembodied copy to produce `toolkit/`, what remains, and the
structural findings that scrubbing surfaced. Companion to `CHARTER.md`.

**Source:** `.dirty-helpers-must-be-cleaned-and-transplanted-before-use/` (untouched; still on
disk for reference until triage completes).
**Product:** `toolkit/`.

---

## 1. Bulk removal — 821 files → 221

| Removed | Count | Why |
|---|---|---|
| `_artifacts/**` | ~522 | Prior test-run residue (`test_tmp/`, `bd_graph/cold_anatomy.sqlite3`, ...) |
| `__pycache__/`, `*.pyc` | ~70 | Bytecode |
| `logs/suite.log` | 1 (1,011 lines) | Another project's runtime history → quarantined |
| `config/registry.json` | 1 | Derived; regenerate via `cli registry-refresh` |
| `config/domain-boundary/forge.json` | 1 | Forge's layer map — pure host config → quarantined |
| `_docs/INTEGRATION_FIELD_REPORT.md` | 1 | Design input → quarantined (§4) |
| `_docs/_AppJOURNAL/` | dir | Prior project narrative + journal DBs → quarantined |
| `.gitignore` | 1 | The **host's** gitignore, dragged along → quarantined (§3) |
| `_exports/` | dir | Prior export residue |

**~70% of the file count was runtime residue.** The real toolkit is ~221 files.

## 2. Lineage scrub

- **72 `tool.json` provenance blocks stripped.** Every `donor:` pointed into `.parts-bin/`
  (`_MindSHARD`, `mindshard`, `_UiMAPPER`, `AppFoundry`, `BDNeuralTranslationSUITE`,
  `_MonacoVIEWER`, `_GitPUSHER`, `_LineNUMBERIZER`, `_TokenizingPATCHER`,
  `_MicroserviceLIBRARY`, `_ProjectMAPPER`, `_TempServerMAKER`, `legacy-helpers`).
  `src/core/registry.py` defaults `provenance` to `{}`, so removal is schema-safe.
  6 blocks kept — the newer tools (`fetch`, `http_probe`, `project_run`, `git_inspect`,
  `event_log`, `sidecar_install`, `vendor_export`) carry clean `NEW` provenance.
- **~40 `NOTES:` header fields rewritten** — donor citations dropped, genuine design insight
  kept, and several upgraded to point at `CHARTER.md §4/§5` where the note describes a known
  limitation (e.g. `blocking_call_scan` can't see async context; `domain_boundary_audit` needs
  a project-supplied policy).
- **Dangling doc pointers removed.** Many files cited `_docs/SOURCE_PROVENANCE.md` — **that
  file does not exist.** Same for `_docs/TARGET_STATE.md` and `_docs/DONOR_DEPLETION_AUDIT.md`.
- **`.parts-bin` removed from hardcoded ignore-lists** in `file_tree`, `bd_graph_shared`,
  `projectmapper`, `repo_search`, `report`, `secret_audit`, `ruff.toml`, and others.

Verification: `ast.parse` clean across every `.py`. Zero prose lineage remains outside `_docs/`.

## 3. The precept violation was *enforced by the test suite*

The most important finding of the scrub. `tests/test_smoke.py:1308`:

```python
self.assertTrue(os.path.exists(os.path.join(target, "AGENTS.md")))  # host pointer
```

Paired with `tools/sidecar_install/tool.json` defaults `write_agents: true` and
`gitignore: true`, the toolkit did not merely *happen* to brand the host — **it had a passing
test that would fail if you stopped.** Anyone fixing the installer would see red and revert.

> This explains why the entanglement kept coming back across attempts. It was load-bearing.

The quarantined `host-gitignore.txt` carries the mirror-image evidence: a section titled
*"Suite Control Plane (this project)"* listing sidecar internals (`logs/`,
`config/registry.json`, `_artifacts/...`) inside the **host's** ignore file.

**Both directions must be cut.** See `CHARTER.md §1`.

## 4. Quarantined (design inputs — `_design/prior-life/`, never ships)

| File | Value |
|---|---|
| `INTEGRATION_FIELD_REPORT.md` | **The most valuable artifact recovered.** An outside agent's field report from using the sidecar on a real unrelated app. Its Part G independently specs the `attach()` front door. Drives the triage. |
| `PRIOR_JOURNAL.md` + `_journalDB/` | Prior project narrative; mine for requirements only |
| `forge-domain-boundary.json` | Worked example of a real layer policy — useful as a **profile** reference |
| `prior-suite.log` | Evidence of real tool usage patterns |
| `host-gitignore.txt` | Evidence of the entanglement (§3) |

## 5. Outstanding — structural, needs triage (NOT scrubbed)

These are behavior/schema changes, deliberately left for the triage pass.

### 5a. The donor-reservoir concept leaked into the product
`.parts-bin` was the old project's read-only reservoir of legacy code to mine. That is a
**factory** concern (`CHARTER.md §7`); the shipped product should have no notion of it. It
survives as:

| Location | Surface |
|---|---|
| `tools/workspace_audit/cli.py:55,77` | scans `root/.parts-bin`; emits `"…is a donor reservoir…"` |
| `tools/workspace_audit/cli.py:21` | `_SURFACES` includes `_BCC` (dead build folder) |
| `tools/workspace_audit` output schema | **`donor_children` output field** |
| `tools/code_intel_shared.py:37,94` | `.parts-bin` in `DEFAULT_SKIP_DIRS`; `include_donors` param |
| `tools/smoke_runner/cli.py:35` | `include_donors` param |
| `tools/vendor_export/cli.py:32,35` | strips `_BCC` + three docs that no longer exist |
| `tests/test_smoke.py:207-208` | asserts `donor_children` contains `legacy-helpers` |

**Recommendation:** delete the concept from the product entirely.

### 5b. Memory stores live in the docs folder
`tools/evidence/cli.py` stores at `_docs/_AppJOURNAL/_journalDB/evidence.sqlite3`; `journal`
mirrors to `_docs/_AppJOURNAL/JOURNAL.md`. A database under `_docs/` is a category error, and
the quarantine (§1) deleted that path — **journal/evidence will recreate it on first use.**
Decide the real home for durable memory before it accretes again.

### 5c. Docs describe a world that no longer exists
`_docs/ARCHITECTURE.md`, `TOOLS.md`, `HUMAN_ONBOARDING.html`, `apps/README.md` document
`.parts-bin/`, `_BCC/`, `SOURCE_PROVENANCE.md`, and a "vendorable suite" framing. Left intact
deliberately: `CHARTER.md` supersedes their architecture, so they should be **regenerated**
after triage, not patched now.

### 5d. No `.gitignore`
Deleted with the host's. The product needs its own, written from scratch, ignoring **only its
own** runtime state — and never mentioning, or asking the host to mention, anything (§3).

### 5e. Dead-doc references
`requirements.txt:1`, `src/core/event_log.py:12`, `tools/README.md:5` cite `TARGET_STATE`
decisions. Harmless prose, but they point at a document that does not exist.

---

## 6. State

**Clean:** all prose lineage, provenance blocks, prior runtime state, host config, residue.
**Verified:** `ast.parse` clean; nothing outside `_docs/` names a prior project.
**Not yet run:** `smoke_test.py` — expected to fail (registry.json is gone by design; the
`AGENTS.md` host-pointer assertion in §3 *should* fail once the precept is enforced).
**Next:** triage (`CHARTER.md §4` policies-over-verdicts), then the `attach` front door (§3 L4).
