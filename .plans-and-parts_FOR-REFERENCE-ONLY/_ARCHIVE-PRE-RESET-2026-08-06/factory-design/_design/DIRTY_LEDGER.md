# Dirty Ledger — retiring `.dirty-helpers-must-be-cleaned-and-transplanted-before-use/`

**Goal:** the sandbox stays "dirty" until the old reference material is gone and only the working
sidecar remains. This ledger tracks that to zero.

**Status as of 2026-07-16: fully mined. Safe to delete.** Evidence below.

---

## 1. Nothing of value is only in the dirty folder

Mechanical diff of the real files (excluding `_artifacts/`, `logs/`, `_exports/`, `__pycache__`):

```
dirty (real files) : 229
toolkit            : 322
only in dirty      :   5
```

All five are accounted for — each was quarantined to `_design/prior-life/` and verified
**byte-identical by sha256**, not by inspection:

| Only in dirty | Quarantined as | sha256 |
|---|---|---|
| `.gitignore` | `host-gitignore.txt` | `84a2a778901c` OK |
| `_docs/INTEGRATION_FIELD_REPORT.md` | `INTEGRATION_FIELD_REPORT.md` | `02a487016377` OK |
| `_docs/_AppJOURNAL/JOURNAL.md` | `PRIOR_JOURNAL.md` | `19621b107d17` OK |
| `_docs/_AppJOURNAL/_journalDB/evidence.sqlite3` | `_journalDB/evidence.sqlite3` | `2dac57deefca` OK |
| `config/domain-boundary/forge.json` | `forge-domain-boundary.json` | `defbf6d02bb9` OK |
| `logs/suite.log` *(residue class)* | `prior-suite.log` | `d90526296591` OK |

The other 224 files all exist in `toolkit/`, scrubbed.

## 2. Full archive taken (rollback insurance)

The only remaining reason to keep the folder was the ability to diff against the pre-scrub
original — the scrub was aggressive (72 provenance blocks, ~40 `NOTES:` headers), and the
sandbox is not a git repo, so there is no history to fall back on.

That reason is now removed:

```
_design/prior-life/dirty-source.zip   229 files · 474.9 KB · sha256 93d4e57d57fc0fe0
```

Verified entry-by-entry against the live folder: **229 entries, 0 problems**. Excludes only the
residue classes (`_artifacts/`, `logs/`, `_exports/`, `__pycache__`, `*.pyc`) — the 522 files of
prior test output that were never worth keeping.

## 3. Was it a useful reference after the scrub? No.

| Possible need | Verdict |
|---|---|
| Source of the toolkit's code | No — `toolkit/` **is** it, scrubbed and verified running (59/60 smoke, registry regenerates) |
| The field report | No — quarantined; drives the triage from `_design/prior-life/` |
| Prior journal / decisions | No — quarantined |
| A real layer-policy example | No — quarantined as `forge-domain-boundary.json`; the cartridge work reads it from there |
| Evidence of the entanglement | No — quarantined as `host-gitignore.txt`; the finding is written up in `SCRUB_AUDIT.md §3` |
| Rollback / diff against original | **No longer** — `dirty-source.zip` (§2) |

The toolkit's stale docs (`_docs/ARCHITECTURE.md`, `TOOLS.md`, `HUMAN_ONBOARDING.html`) describe
the dead world, but they live **in `toolkit/`**, unchanged from the original. The dirty folder
adds nothing to rewriting them.

## 4. Recommendation

**Delete `.dirty-helpers-must-be-cleaned-and-transplanted-before-use/`.**

Deletion is irreversible and the sandbox has no git history, so it is gated on operator
confirmation despite the evidence above. After deletion the sandbox is:

```
.useful-helpers/
  _design/     charter · audits · ledger · prior-life/ (quarantine + archive)
  _harness/    the proving ground
  toolkit/     the product — the only live code
```

…which is the stated end state: **only the working sidecar remains.**

## 5. Not blockers, but do not lose them

These are tracked elsewhere and survive the deletion:

- `SCRUB_AUDIT.md §5a` — the donor-reservoir concept still leaks into the product
  (`workspace_audit.donor_children`, `iter_python_files(include_donors=)`, `_BCC`). **The harness
  now measures this** as `CLEANLINESS FAIL — 8 lineage hits`, so it cannot be quietly forgotten.
- `SCRUB_AUDIT.md §5b` / `ATTACH_SKELETON.md` — no declared state root.
- `SCRUB_AUDIT.md §5c` — the stale `_docs/` need regeneration, not patching.
- `SCRUB_AUDIT.md §5d` — the product still has no `.gitignore` of its own.
