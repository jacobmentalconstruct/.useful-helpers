# External Review: T7 Domain Truth (Classification Repair Candidate, `0049`)

Date: 2026-09-02T13:49:14Z
Reviewer: The Reviewer
Reviewed commit: `1c94cf5` (`Submit T7 classification repair for approval`); repair commit `cf4de91`
Reviewed evidence: `.builder/journal/0049-t7-classification-repair-awaiting-approval.md`;
prior review `20260902T120434Z-external-review.md` and its operator-ruling addendum;
T7 receipt `20260902T131756Z-95787587` and cumulative receipts named by `0049`;
`product/core/substrate.py`, `product/core/awareness.py`, `tests/test_t7_domain_truth.py`,
`.builder/gates/t7_domain_truth.py`; Plan, Current State, Architecture, README;
independent re-run of all eight gates and canonical pytest on a clean off-repository copy
at `1c94cf5`; live probes on installed instances.

## Disposition

RETURN TO VERIFYING — narrow. Two bounded items in T7's own surfaces. Everything
returned last time is fixed and verified; D1–D3 are applied as ruled and recorded in
construction history; provenance and gate discrimination are now genuinely sound.

## Executive Finding

Both prior defects are gone and I confirmed it on real targets: this repository as a
target now reads `software` with 494 resources instead of `mixed` with 2,307 (80% `.git`);
`product/` alone, a Python project with a README, and a Node project all read `software`;
`.git`, `node_modules`, and their nested occurrences are recorded as single metadata-only
directory resources with an explicit untraversed limitation and nothing beneath them is
read. D1 took the repair path with the T3 gate untouched and passing: an unchanged
refresh now adds zero versions and zero evidence; a touch, a content change, and a
deletion each behave as they should. D2 emits `shown/total` and a limitation line per
truncated bound, persisting through `awareness current`. D3 wording is present. The T7
gate now executes its known-answer targets and its mutations against the live module
rather than grepping its own keywords, and `working_tree_provenance` makes a dirty
authoritative receipt impossible to cite silently. The receipts cited are the first
Linux receipts in the record and their `head_commit` contains the measured source.

What remains is the mirror image of the defect just fixed, plus one gate
self-consistency bug, both small.

## Findings — T7 Candidate

- [RETURN] Plain-text documents are ancillary regardless of proportion, so a notes
  collection with a helper script is classified `software`.
  `_is_ancillary_document` returns true for every `.md`, `.rst`, and `.txt`, and
  `_profile_decision` excludes ancillary documents from the count-ratio test
  unconditionally. Measured: 60 `.md` notes plus 3 `.py` scripts → `software`,
  `ancillary_document_count: 60`; 40 `.txt` letters plus 1 `.py` → `software`. The
  count is disclosed, so this is not dishonest, but the headline profile is wrong for a
  target class P7 names (documents), and it is exactly the third declared risk in
  `0044`: "accidentally treating software as the default target shape." The previous
  defect let documents always win; this one lets software always win over text
  documents. The ratio machinery already exists and simply is not applied here.
  Evidence: `product/core/substrate.py::_is_ancillary_document`, `::_profile_decision`
  (`ancillary_documents` excluded from `strong`); probes A and A2 below.
  Required action: treat text documents as ancillary only when README-stem-named or
  when they do not outnumber software signals (or an equivalent bounded rule), so
  `strong` includes text documents that dominate; add a third known-answer target to
  `_known_answer_profiles` (notes-heavy with a few scripts → `records_documents` or
  `mixed`) and an executed mutation that disables the rule.

- [RETURN] The T7 gate is not self-consistent: launched as plain `python`, it creates
  `product/core/__pycache__` through its own in-process import and then fails its own
  hygiene check.
  `_import_substrate` inserts `product/` on `sys.path` and imports `core.substrate` in
  the gate process; `_run` sets `PYTHONDONTWRITEBYTECODE` for subprocesses only, and
  the gate process itself never sets `sys.dont_write_bytecode`. Measured on a clean
  copy: `python .builder/gates/t7_domain_truth.py` → FAIL 14/15, `repository_hygiene:
  generated debris remains: ['product/core/__pycache__']`; `python -B ...` → PASS
  15/15. This is the mechanism behind the hygiene-only FAIL receipts that `0042`,
  `0047`, and `0048` each recorded and worked around by hand, and it will recur in
  T8's cumulative run.
  Evidence: `.builder/gates/t7_domain_truth.py::_import_substrate`, `::_run`; two
  gate runs on a clean copy recorded below.
  Required action: set `sys.dont_write_bytecode = True` at the top of the gate (or
  import via `importlib` with bytecode disabled), and note in `0050` that prior
  hygiene-only FAIL receipts had this cause.

- [ADVISORY] `vendor`, `build`, and `dist` are treated as generated on every target,
  including records/document targets where they are ordinary folder names.
  Measured: a records target with `vendor/` (5 contract PDFs), `build/` (5 site-plan
  PDFs), and `invoices/` (3 CSVs) → `records_documents` from the CSVs alone; both
  document folders untraversed. The limitation is stated explicitly, so unobserved is
  unknown rather than absent, and the honesty invariant holds. But the heuristic is
  software-shaped, on a tranche whose declared risk is exactly that. Recommend
  applying the `vendor`/`build`/`dist` rule only when a software marker is present at
  or above that level, leaving VCS and cache names unconditional.
  Required action: none for T7 closure; record as an accepted limitation or fold in
  with the first item, at the operator's choice.

- [ADVISORY] Observations and relations still accrue on every refresh.
  D1 was scoped to evidence and versions and that scope is met. Measured: a 20-file
  unchanged target adds ~41 observations and ~160 relations per refresh; this
  repository would add ~4,000 relation rows per refresh. `0049` records this as
  discovered-not-absorbed, which is the correct handling. Noted so T8's repeated
  refreshes on a substantial target are not a surprise.

## Findings — Construction Record and Pre-T8 Readiness

- [RETURN — pre-T8, not T7] Line-ending normalization now blocks Windows evidence.
  On the operator's Windows checkout every tracked file — product source, tests,
  gates, journal, Plan — shows as modified from CRLF alone (`git diff
  --ignore-cr-at-eol` is empty). The new `working_tree_provenance` check, correctly,
  fails on any tracked difference. Consequence: **no authoritative or cumulative
  receipt can be produced on Windows until line endings are pinned**, and P8 requires
  Windows. Carried finding H1 (`.gitattributes`) has therefore moved from hygiene to a
  hard T8 prerequisite. `0049` states honestly that no Windows receipts exist for this
  candidate.
  Required action: add `.gitattributes` (`* text=auto eol=lf`, or at minimum
  `*.py *.md *.json *.toml text eol=lf`) and renormalize in one commit before T8
  declares; then produce one Windows T7 receipt so the platform claim is not
  Linux-only going into release.

- [RETURN — pre-T8, not T7] Carried findings C1–C5 and H2–H3 remain unruled.
  `0049` says so plainly ("pre-T8 record items for the operator, not T7 surfaces").
  Still no Plan section, no journal ruling. C4 is visible in this very submission: the
  cited T0 receipt has no `working_tree` field. The Plan-prose gate idiom (C1) is
  unchanged in the T2/T3/T5 gates and the T0 allowlist.
  Required action: one journal entry ruling on each (decline is a legitimate ruling),
  pointed to from the Plan, before T8 declares.

- [NOTE] Provenance discipline is now correct. T7 receipt at `cf4de91`, empty tree;
  cumulative receipts at `0fafd18`, differing only by untracked receipts of earlier
  gates in the same run. This is what the two prior reviews asked for.

- [NOTE] Gate discrimination is now real. `_executed_mutations` monkeypatches the live
  module (`_GENERATED_PARTS`, `_VENDOR_PARTS`, `_RECORD_SUFFIXES`,
  `_ANCILLARY_DOCUMENT_SUFFIXES`, `_profile_decision`) and re-runs the known-answer
  classification; `consumer_entrance_known_answer` goes through `factory attach` and the
  installed `sidecar.py`. This is the model the earlier advisories asked for and it
  should be the pattern for T8.

## Independent Measurement

Clean copy at `1c94cf5`, Linux 6.8 / CPython 3.13.15 / pytest 8.4.2 / Ruff 0.15.22,
launched with `python -B`:

- `pytest -q`: 69 passed. Ruff: passed. `git diff --check`: clean.
- T7 15/15; T6 11/11; T5 13/13; T4 14/14; T3 12/12; T2 13/13; T1 9/9; T0 13/13.
- T7 launched without `-B`: FAIL 14/15 (`repository_hygiene`, `product/core/__pycache__`
  created by the gate process).

Probes (installed instances):

| Probe | Target | Result |
|---|---|---|
| H | this repository (minus `.sidecar`, `tests`) | `software`; 494 resources (was 2,307); 0.21 s; projection `100 of 4810` handles disclosed |
| D | nested `libs/dep/.git` and `libs/dep/node_modules` | neither descended; 5 resources |
| C | `.git` as a file (worktree form) | recorded `path:.git`, not hashed |
| G | directory symlink to outside the target | recorded `path:link`, not followed, nothing outside appears |
| E | 20 files: unchanged / touch / edit / delete refreshes | versions 20→20→21→22→22; evidence 41→41→42→43→44 (D1 met) |
| F | 150 files | `projection.source_handles {shown:100,total:2105}`, `resource_handles {20,150}`; limitation lines present; identical in `awareness current` (D2 met) |
| I1/I2/I3 | 10py+3csv / 2py+10csv / 10py+1csv | `mixed` / `mixed` / `software` with subordinate 1 |
| **A** | **60 `.md` + 3 `.py`** | **`software`, ancillary 60** |
| **A2** | **40 `.txt` + 1 `.py`** | **`software`, ancillary 40** |
| B | records target with `vendor/`, `build/` PDFs + CSVs | `records_documents`; both folders untraversed with explicit limitation |

## Requirement Matrix (delta from the previous review)

Items 1, 2, 4–11 and A1, A2, A4: PASS, unchanged. Item 3 (substantial software →
`software`): now **PASS** on the realistic fixture, on this repository, and on every
software target probed. A3 (generated/vendor material must not dominate or derail):
now **PASS** — subtrees are recorded once, untraversed, and disclosed. New: the
declaration's own risk statement about software as the default shape is now the open
item, on documents-heavy targets.

Prior discrimination-plan items are all rejected by fixtures or executed gate
mutations. New plausible wrong implementation, present in the candidate: "count every
text document as ancillary whenever a single software file exists."

## Closure Review Pass

Closer than any prior T7 candidate. Ownership, honesty, provenance, and discrimination
are all in order, and the substantial-software case that P7 names is now proven on a
real repository rather than a four-file fixture. It is not yet strong enough to justify
PARKED and P7 credit because the documents-heavy case — the other target class P7
names — is misclassified by a rule that exempts text documents from the ratio test, and
because the tranche's own gate fails unless launched with a flag it does not set for
itself. Both are a few lines. With those repaired and a `0050` submission, I would expect
to recommend APPROVE CANDIDATE.

For T8: the two pre-T8 items above are now blocking in practice, not in principle — one
because Windows receipts are mechanically impossible until line endings are pinned, the
other because sealing a release over unruled construction findings is the silence the
operator has said to exclude.

## Recommendation

Return T7 for a narrow repair inside T7's surfaces:

1. Apply the ratio to text documents (ancillary only when README-stem-named or not
   outnumbering software signals); add a notes-heavy known-answer target and an
   executed mutation.
2. `sys.dont_write_bytecode = True` in the T7 gate; note the cause of earlier
   hygiene-only FAIL receipts in `0050`.
3. Optionally, at the operator's choice, condition `vendor`/`build`/`dist` on a
   software marker; otherwise record it as an accepted limitation in `0050`.

Before T8 is declared, independent of T7:

4. `.gitattributes` and renormalization in one commit; one Windows T7 receipt.
5. A journal ruling on C1–C5 and H2–H3, pointed to from the Plan.

This review is evidence, not a ruling. The operator grants approval, PARKED status, and
P7 credit; T0–T6 remain parked and are not reopened by anything here.
