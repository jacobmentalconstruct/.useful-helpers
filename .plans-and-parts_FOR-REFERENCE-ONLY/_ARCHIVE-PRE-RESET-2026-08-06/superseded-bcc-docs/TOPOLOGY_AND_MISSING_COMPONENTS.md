# Project Topology and Missing Components

Date: 2026-08-05. Produced on operator instruction: *"See how the project uses
the toolkit. Report on any missing components."*

Verification: executed against the real tree in a Linux sandbox with the project
folder mounted. Findings are `[VERIFIED]` unless marked otherwise.

---

## 1. How the Project Uses the Toolkit

The earlier reading of this repository was wrong, and the correction matters.

This root is **not** a workbench-to-be with a toolkit bolted on. It is the
toolkit's **factory**. The toolkit is its product, nested inside it.

Evidence, from `_harness/harness.py` `[VERIFIED]`:

```python
FACTORY = HERE.parent          # the repository root
TOOLKIT = FACTORY / "toolkit"  # the product under test
SIDECAR_NAME = ".useful-helpers"
```

and from `_harness/README.md`:

> **Factory, not product.** This never ships. It exists to point the sidecar at
> a real target and record, mechanically, what happened.

### 1.1 The four zones and their actual relationship

| Zone | Role | Relationship to the toolkit |
| --- | --- | --- |
| `_design/` | Charter, plan, capability gaps, completion plan, dirty ledger, scrub audit | The toolkit's **design authority**. Defines the precept and the acceptance questions. |
| `_harness/` | Proving ground | **Tests** the toolkit. Copies `toolkit/` into `<target>/.useful-helpers/` fresh per run, exercises every mounted Observe tool, takes sha256 manifests before and after, scores against `CHARTER.md §8`. |
| `toolkit/` | The product | 95 tools, `VERSION 1.1.0`, one governed `invoke()` seam. |
| `.plans-and-parts_FOR-REFERENCE-ONLY/` | Parts bin | The operator's **live daily-driver tools** plus conversion plans. To be deleted once the sidecar replaces them. |

`.bcc/` and `_docs/` are builder control added by this engagement. Neither is
runtime.

**The toolkit correctly stays nested.** It depends on the factory for its
verification, and the factory never ships. Promoting the toolkit to the root
would have destroyed that distinction. The instruction to keep it nested was
right and the earlier proposal to promote it is withdrawn.

### 1.2 The factory already solved a problem this engagement re-discovered

Journal 0002 recorded that the precept guard is *detection, not prevention* — a
violating write lands and is then reported.

The factory already knew, and already built the other half. `_harness/ro_mount.py`
plus `harness.py mount` seals the target **read-only** so the OS refuses the
write and the violation cannot occur at all. `_design/CAPABILITY_GAPS.md` records
this as tier **D3**, delivered 2026-07-20.

Strategies are measured rather than assumed: `bind` on privileged Linux,
`userns-tmpfs` unprivileged, and an honest `UNAVAILABLE` with a reason on
Windows and macOS. The README is explicit that a skipped dimension must never
read as a pass.

This is a mature engineering culture and the workbench should inherit its
posture rather than reinvent it.

### 1.3 The factory's own gap list is closed

`_design/CAPABILITY_GAPS.md` is marked **RESOLVED** as of 2026-07-20. Tiers
C1–C8, D1–D2 and D3 all landed: the "hands" (`read_file`, `write_file`, `glob`,
`fs_op`, `edit`, `diff`, `sqlite_exec`, `dep_install`, `web_search`), governed
execution, the `delegate` local-model loop, the symbol graph, and read-only
mount.

Its thesis is worth carrying forward verbatim: *every time an agent reaches past
the sidecar for its own hands, the sidecar has a gap* — because governance is
only as complete as the seam is used.

---

## 2. Missing Components

### 2.1 The finding that matters: five daily drivers with no plan and no contract

`_harness/targets/_UsefulHelperSCRIPTS/` is the operator's real tool collection,
adopted as a harness target. It contains **12** app folders. The parts bin
contains **12** apps. They are not the same twelve. `[VERIFIED]`

Present in both — covered by a plan and a contract (7):
`_GitPUSHER`, `_LineNUMBERIZER`, `_MonacoVIEWER`, `_ProjectMAPPER`,
`_TextTOUCHER`, `_TokenizingPATCHER`, `_UiMAPPER`.

**Daily drivers with no plan, no contract, and no tranche (5):**

| App | Toolkit coverage `[VERIFIED]` | Verdict |
| --- | --- | --- |
| `_UsefulHelperScriptsMENU` | search for menu/launcher tools returns **NONE** | **This is the single surface itself.** The launcher that fronts all the others. Nothing in the toolkit or the plans covers it. It is the product being asked for, and it is unspecified. |
| `_LoRA_TRAIN` | nothing trains. `prompt_eval`, `constraint_build/query`, `prompt_rubric_judge`, `model_benchmark` are evaluation and benchmarking, not fine-tuning | **Total gap.** No plan, no tool, no tranche. Also the heaviest possible dependency, against the rule that deterministic startup carries no local-model requirement. |
| `_MicroserviceLIBRARY` (AppFoundry) | `app_factory`, `scaffold_project`, `stamp`, `test_scaffold` | **Partial.** Stamping and scaffolding are covered. The layered library, catalog builder, query layer, Tk librarian UI, pipeline runner and manifest validator are not. |
| `_TempServerMAKER` | `tempserver` | **Partial.** Serving a directory is covered. The interactive web UI — collapsible file tree, tabbed viewer, in-browser AST, multi-format export — is not. Note the heavy functional overlap with Project Mapper's projections and `codebase_bundle`. |
| `_NoStringsPDF` | 8 tools: `pdf_compress`, `pdf_extract`, `pdf_info`, `pdf_interleave`, `pdf_merge`, `pdf_rotate`, `pdf_split`, `pdf_thumbnails` | **Backend largely covered.** The viewing and navigation surface — PyMuPDF rendering, zoom, thumbnail grid — is not. |

### 2.2 A priority inversion in the governing blueprint

Five parts-bin apps are **not** daily drivers: `_ChatWindowKERNAL`,
`_TheDISMANTLER`, `_WasmInferenceWRAPPER`, `_manifold-mcp`, `_theCELL`.
`[VERIFIED]`

Their own contracts describe them as *prior art* — the manifold-mcp contract
says its "primary value is agent-transport prior art"; TheDISMANTLER's says
"primary value is GUI-side dispatch prior art"; the WASM wrapper's says the
reference "is not true WASM".

Yet the blueprint allocates **Tranches 12, 13 and 14** to them, while the five
apps the operator actually uses every day receive **no tranche at all.**

Their architectural lesson has already been extracted — it is the single-dispatch
rule, now recorded in `ARCHITECTURE.md` §6. Once extracted, the prior art has
paid out. Building the apps themselves is a separate and much weaker
justification.

`_MonacoVIEWER` is the exception: it is a genuine daily driver, so Tranche 11
stands on its own merits.

### 2.3 The harness has never been run against reality

`_harness/runs/` holds **58** recorded runs. `[VERIFIED]`

Every one targets a synthetic scaffold — `s-python-app`, `s-data-curation`,
`s-composite`, `s-records-research`, `s-workspace` — or the `seam` dimension.

**Zero runs target `_UsefulHelperSCRIPTS`.**

The harness's own stated purpose includes: *"Do the tools work on a target
nobody tuned them for?"* The one real, untuned, adopted target has never been
exercised. The scaffolds carry planted false-positive bait and are therefore
tuned by construction.

This is the cheapest high-value action available right now: one
`harness.py run _UsefulHelperSCRIPTS` would measure the toolkit against the
actual work, and would do it before any workbench code is written.

### 2.4 Operational and hygiene gaps

| Finding | Status |
| --- | --- |
| No version control | **Fixed.** Baseline commit `d0eb14c`, 3,382 files, zero secrets or virtualenvs staged. |
| Code-signing certificate in the tree — `_UsefulHelperScriptsMENU/developer_cert.pfx`, may carry a private key | **Contained.** Ignore rules extended to `*.pfx *.p12 *.pem *.key *.jks id_rsa* .env`; verified ignored before the first commit. **Should still be moved out of the tree entirely.** |
| `toolkit/_state/` holds ~1.1 MB of prior-engagement memory: 1 MB `event_log.sqlite3` with a stale journal, `journal.sqlite3` (20 Jul), `llm_usage.jsonl` (28 Jul) | Ignored, not cleared. Operator decision. |
| SQLite over the mounted filesystem raises `disk I/O error` | Confirms state belongs in a platform user-data location, not in the project. |
| The factory's own README notes it "is not a git repo, so a workflow file could not be run or verified here" | That blocker is now removed; the `precept.yml` CI job it describes becomes possible. |

### 2.5 A constraint on how I can work in this folder

`[VERIFIED]` The mount is FUSE with unlink denied:

| Operation | Result |
| --- | --- |
| create / write / overwrite | **OK** |
| rename / move (`mv`) | **OK** |
| delete (`rm`) | **BLOCKED** — `Operation not permitted` |

Consequences:

- A reorganization is still fully possible, because `mv` works. Deletion is not.
- Anything needing removal goes to `_trash/` and the operator empties it.
- Every git **write** leaves stale `.git/*.lock` files that cannot be unlinked,
  which wedges the next write. Moving them aside restores it. Read-only git
  commands create no locks and are safe.
- **Recommendation: run git from Windows, not from the sandbox.**

`_trash/` currently holds five swept files and one empty probe commit
(`b3c9631`) sits on top of the baseline. Both are cosmetic and safe to clear
from Windows.

---

## 3. What This Changes

1. **The toolkit stays nested.** Confirmed by the factory's own structure. The
   proposal to promote it to the root is withdrawn.
2. **The product being asked for is `_UsefulHelperScriptsMENU`, done properly** —
   one surface fronting the tools, replacing a `MENU.bat` launcher and eleven
   separate Tk applications. Today the toolkit has four *separate* UI views
   (`registry_view`, `mapper_view`, `planner_view`, `installer_view`) reached by
   four separate commands. Unifying those is the nearest real milestone.
3. **Five daily drivers need contracts before they need code.** They currently
   have neither, and three of them overlap the toolkit only partially.
4. **Three blueprint tranches point at apps that are not in daily use** and
   whose architectural value has already been extracted.
5. **Measure before building.** Running the harness against
   `_UsefulHelperSCRIPTS` costs one command and would ground every ownership
   decision in the capability matrix against the real target.

---

## 4. Recommended Next Tranche

Not the blueprint's Tranche 2 scaffold.

**Tranche 2 (revised) — Ground Truth Against the Real Target.**

1. Run `harness.py run _UsefulHelperSCRIPTS` and record the result.
2. From that evidence, write contracts for the five uncontracted daily drivers,
   in the same shape as the existing twelve.
3. Re-price the capability matrix against measured behavior rather than manifest
   inspection.
4. Decide the fate of the five non-daily-driver parts-bin apps explicitly:
   prior art extracted, apps not built.

Completion: every daily-driver app has a contract and a measured toolkit
coverage figure; the reorganization and the UI work then proceed against
evidence rather than assumption.

This defers the runtime scaffold by one tranche and removes most of the guessing
from everything after it.
