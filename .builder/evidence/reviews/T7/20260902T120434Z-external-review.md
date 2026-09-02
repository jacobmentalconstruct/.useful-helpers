# External Review: T7 Domain Truth (Repaired Candidate) and Pre-T8 Closure Pass

Date: 2026-09-02T12:04:34Z
Reviewer: The Reviewer
Reviewed commit: `32bae24` (`Repair T7 weak material boundary`), branch `codex/t1-mechanical-host`
Reviewed evidence: `.builder/journal/0044`-`0048`; `.builder/journal/0042`, `0043`;
prior T7 reviews `20260901T115016Z`, `20260901T124501Z`, `20260901T135332Z`; prior T6
reviews `20260829T123032Z`, `20260830T125528Z` and the carried-findings draft
`20260829T162641Z`; T7 receipt `20260902T112455Z-7fce770c` and the seven cumulative
receipts named by `0048`; `product/core/substrate.py`, `product/core/awareness.py`,
`tests/test_t7_domain_truth.py`, `.builder/gates/t7_domain_truth.py`,
`.builder/gates/t0_bootstrap.py`; independent re-run of all eight gates and canonical
pytest on a clean off-repository copy; live probes against installed instances on real
and synthetic targets.

The operator asked for a thorough inspection with the explicit bar that the project be
right before T8 is declared. This review therefore has two parts: the T7 candidate
review, and a closure-readiness pass over everything T8 will inherit.

## Disposition

RETURN TO VERIFYING

## Executive Finding

The T7 implementation is well-shaped. Domain facts live in the T3 substrate as
observations, evidence, claims, and relations; awareness projects them through the T3
basis without scanning or querying tables; unobserved and observed-empty are kept apart;
historical shape does not leak after replacement; observe/orient creates no receipts,
journal, mutation, or MCP state; and the weak-material repair from the previous return is
real — a large file is classified before any read and is never hashed. All eight gates
reproduce PASS on Linux at `32bae24` from a clean tree, and the T6 repairs hold under
re-probe.

Two approval-relevant defects remain, and both come from the same root: **the T7
classifier has never been run against a real software target.** Every fixture is three to
five hand-written files. When pointed at real targets the candidate reports the wrong
profile on the common case and lets the single most universal generated subtree become
the center of the substrate. Both are named as wrong implementations in the declaration
that T7 is being reviewed against.

Separately, the carried construction findings from the T6 review have no recorded
disposition anywhere in the Plan or journal, and the gate-provenance pattern flagged in
that review has recurred. Neither blocks T7, but both are exactly the kind of silence the
operator's "right before T8" bar is meant to exclude.

## Findings — T7 Candidate

- [RETURN] Every realistic software target is classified `mixed`; only the tidy fixture
  yields `software`.
  `_RECORD_SUFFIXES` contains `.json`; `_DOCUMENT_SUFFIXES` contains `.md` and `.txt`;
  `package.json` is simultaneously a software marker and a records marker. So any target
  with a README, a `.json` config, or a `.txt` file produces a
  `target_profile_records_documents` claim alongside `target_profile_software`, and
  `awareness._domain_profile` then reports `mixed`. Measured on installed instances:
  the product's own `product/` tree (Python plus five `manifest.json`) → `mixed`; a
  three-file Python project with a README → `mixed`; a three-file Node project
  (`package.json`, two `.js`) → `mixed`; this repository as a target → `mixed`. The only
  input that yields `software` is the fixture, which was written with no README, no
  `.json`, and no `.txt` — add any one of those and its
  `assertEqual(domain_profile, "software")` fails. Entry `0044`'s discrimination plan
  names this exact wrong implementation: "passing with one generic non-empty fixture
  while failing to distinguish software, mixed records/documents, and empty/nascent
  targets." Entry `0044`'s third declared risk was "accidentally treating software as
  the default target shape"; the candidate has the inverse defect, but the fixture set
  cannot see either.
  Evidence: `product/core/substrate.py` `_SOFTWARE_FILES`, `_RECORD_SUFFIXES`,
  `_DOCUMENT_SUFFIXES`, `_domain_signal`; `product/core/awareness.py::_domain_profile`;
  `tests/test_t7_domain_truth.py:73-99` (fixture contents); probe results P1, P2, P2b,
  and "this repository as target" recorded below.
  Required action: make the profile decision discriminate rather than merely detect —
  for example weight or ratio the signal classes, treat documentation-adjacent files
  (`README*`, `LICENSE*`, `CHANGELOG*`, `*.md` beside software markers) as software
  ancillary rather than records evidence, and drop `package.json`/`pyproject.toml` from
  the records class. Then add a known-answer fixture that is a realistic software
  project (README, config JSON, a `.txt`, a `.git` directory) and asserts `software`,
  and a genuine mixed fixture that asserts `mixed` for the right reason.

- [RETURN] `.git` and other universal generated subtrees are not recognized as weak or
  generated material; on a real software target they dominate the substrate and are
  fully content-hashed.
  `_VENDOR_PARTS` is `{node_modules, vendor, .venv, venv, __pycache__}`. `.git`, `.hg`,
  `.svn`, `build`, `dist`, `target`, `.tox`, `.mypy_cache`, `.pytest_cache`, `.idea`,
  `.vscode` are absent, and `_resource_records` excludes only `.sidecar`. Git object
  files have no suffix and are typically under 1 MB, so they are classified as neither
  vendor, binary, nor large: every one is read and SHA-256 hashed, each gets a resource,
  a version, two observations, two evidence rows, and roughly ten relations, and none
  contributes a limitation. Measured with this repository as the target: 2,307 resources,
  of which 1,840 (80%) are under `.git/`; in a small repo, 27 of 27 `.git` files were
  hashed; `weak_material_count` was 1. The amended declaration (`0045`) requires that
  "vendor/dependency-like or generated-looking subtrees … contribute metadata and
  limitations without becoming the center of domain truth" and that such material "does
  not exhaustively dominate or derail the refresh/orientation path." `.git` is the
  archetype of a generated subtree, it is present in essentially every software target
  P7 names, and here it *is* the center. The previous review accepted whole-target
  traversal "if honestly bounded"; on a real repository the bound is not honest, because
  the material that dominates is not flagged at all.
  Evidence: `product/core/substrate.py` `_VENDOR_PARTS`, `_resource_records`,
  `_describe_resource`; probe P3 and "this repository as target" below.
  Required action: treat VCS internals and the common build/cache directories as
  generated weak material (metadata-only, limitation recorded, hashing skipped) — or
  exclude them from traversal with an explicit recorded limitation that they were not
  observed. Either is honest; silently hashing them is neither. Add the fixture from the
  previous item so a target with a `.git` directory is exercised.

- [ADVISORY] Awareness silently truncates handles and findings.
  `awareness.refresh` takes `source_handles[:100]`, `_findings_from_substrate` takes
  `claims[:10]` and `resources[:20]`. With the 3,000-file vendor probe the revision named
  100 of 3,104 handles with no statement that 3,004 were omitted. The existing
  limitation ("a compact projection … not a complete target scan") is generic. Charter
  invariant 9 and P4 both require unknown to be explicit. This is a T4 design that T4's
  own fixtures never exceeded; T7 is the first tranche to make it observable.
  Required action: none for T7 closure. Recommend an explicit limitation line or a
  `shown/total` count whenever truncation occurs, before T8's acceptance walk on a
  substantial target.

- [ADVISORY] The weak-material claim embeds every supporting handle in its `data_json`.
  On the vendor probe `target_has_weak_material.data.supporting_handles` held 3,101
  entries in one row. The claim is correct; the representation will not scale.
  Required action: none for T7 closure; consider counts plus a bounded sample.

- [ADVISORY] Freshness for metadata-only resources is size and mtime only.
  Because weak material is no longer hashed, `_resource_signature` for such a resource
  depends on `size_bytes` and `mtime_ns` alone. Measured: overwriting a 1.1 MB file's
  contents while preserving size and mtime left `awareness current` reporting
  `current`. This is a direct and correct consequence of the previous return and is an
  acceptable prototype limitation, but the recorded limitation text ("represented
  without content-heavy inspection") does not say that content change is undetectable
  under those conditions, and T5 stale-refusal inherits the same blind spot.
  Required action: none for T7 closure. State it in the limitation text.

- [INFORMATIONAL] Substrate grows unconditionally on every refresh.
  `_insert_evidence` hashes a body that includes `observed_at`, so every refresh creates
  a new evidence row and a new resource version for every file, changed or not.
  Measured on a 50-file target refreshed three times unchanged: versions 50→100→150,
  observations 101→202→303, relations 501→1002→1503. Combined with the vendor and `.git`
  numbers above this is the multiplier that turns "substantial" into "derailed". It is a
  T3 design, not a T7 change; I raise it because it also makes T3's changed-file
  fixture non-discriminating — a new version appears whether or not the file changed,
  so the fixture cannot distinguish versioning from unconditional insertion.
  Required action: none for T7. Operator decision: accept as prototype behavior with a
  recorded statement, or bind to T8 alongside the substantial-target walk.

- [INFORMATIONAL] The declaration's word "substantial" is not met by the fixture.
  `0044` item 3 and `docs/ARCHITECTURE.md` both say a *substantial* software fixture;
  the fixture is four files totaling under 200 bytes. Every real-target result in this
  review came from targets the fixture set does not resemble.

## Findings — Construction Record and Pre-T8 Readiness

- [RETURN — record] The carried construction findings from the T6 review have no
  recorded disposition.
  `.builder/evidence/reviews/T6/20260829T162641Z-carried-findings-draft.md` proposed
  dispositions for C1 (gate exemptions keyed to Plan prose), C2 (no governed-loop route
  over MCP), C4 (T0 gate records no `working_tree`/`source_digest`), C5 (parked-gate
  discrimination unaudited), and H1–H3. The Plan has no carried-findings section, T7's
  precondition cell does not name C1, and no journal entry rules on any of them. C2 is
  the only one with a trace, as a sentence in `0043`. C1 is now measurably wider than
  reported: the `"<tranche> | PROVISIONAL" not in plan` idiom appears in
  `t2_runtime_receipts_work_memory.py`, `t3_epistemic_substrate.py`, and
  `t5_governed_mutation.py`, and `t0_bootstrap.py::_provisional_status` carries a
  hand-extended allowlist of Architecture status strings that must be edited every
  tranche (four lines were added for T7 in `4313dd7`). C4 is unchanged: the T0 receipt
  cited by `0048` has no `working_tree` field. H1 is unchanged: no `.gitattributes`,
  and `0047`/`0048` now record `git diff --check` as passing "with line-ending warnings
  only".
  Evidence: `grep -n "_has_started\|TRANCHE_PLAN" .builder/gates/*.py`;
  `grep -rn carried .builder/` returns nothing; `.builder/TRANCHE_PLAN.md` T7 row.
  Required action: an operator ruling on each carried finding, recorded in a journal
  entry and pointed to from the Plan, before T8 declares. A finding may be declined —
  but declined on the record, not by omission.

- [ADVISORY — recurring] Authoritative receipts are again taken from a dirty tree at a
  commit that does not contain the measured code.
  T7 receipt `20260902T112455Z-7fce770c` and the cumulative T6/T5/T4/T3/T2/T1 receipts
  all record `head_commit 8e4f28a` with `working_tree` listing
  `M .builder/gates/t7_domain_truth.py`, `M product/core/substrate.py`,
  `M tests/test_t7_domain_truth.py` — the weak-material repair itself, uncommitted,
  committed afterwards as `32bae24`. The receipts' `head_commit` therefore names source
  that does not contain the repair they measured. I confirmed the results reproduce from
  clean `32bae24`, so the outcome is sound; the provenance is not. This is the same
  pattern the first T6 review flagged, and its recommended remedy (re-run from a clean
  tree and cite those receipts) was not adopted as practice. For T8 this stops being
  advisory: release evidence must be bound to the exact sealed commit.
  Required action: before T8, either commit before the authoritative run as a rule, or
  make each gate report a `clean_working_tree` assertion as PASS/FAIL so a dirty
  authoritative receipt cannot be cited without the discrepancy being visible in the
  check list.

- [ADVISORY — recurring] T7 gate discrimination remains self-referential.
  All nine mutations in `_discrimination_witness` edit source text in memory and assert
  that a substring or index predicate over that text complains; none executes anything.
  `_weak_material_metadata_only_boundary` is a `str.index` comparison. The genuinely
  behavioral witness in this tranche is in the test suite
  (`test_large_weak_material_is_not_fully_read_or_hashed` patches `Path.read_bytes`),
  which is the right shape and should be the model for the gate. The T6 advisory on this
  point was not carried into T7.
  Required action: none for T7 closure; see C5 above.

- [INFORMATIONAL] Linux evidence exists only in review files.
  Every receipt in `.builder/evidence/` was produced on Windows. This review and the two
  prior reviews by this reviewer reproduced every gate on Linux/CPython 3.13.15, but
  review evidence is not closure evidence. P8 requires clean Windows and Linux
  acceptance; T8 will need to produce Linux receipts through the gate mechanism itself.

- [INFORMATIONAL] Recurring hygiene-only gate failures are procedural noise.
  `0042`, `0047`, and `0048` each record an authoritative-run attempt that failed only
  `repository_hygiene` on generated `__pycache__`, was cleaned by hand, and re-run. On
  Linux, pytest, all eight gates, and the fixtures produced no bytecode. The cause is on
  the Windows side of the procedure (parallel runs or an invocation without
  `PYTHONDONTWRITEBYTECODE`); each occurrence adds a FAIL receipt to the permanent
  record. Worth fixing at the source rather than by repetition.

## Boundary Checks

- Confirmed: domain signals, evidence, claims, and relations are created only in
  `product/core/substrate.py::refresh`; `product/core/awareness.py` reads
  `substrate.current_awareness_basis` and contains no query against T3 tables (regex
  check in gate plus source read).
- Confirmed: awareness does not scan the target for domain findings; its only direct
  target access remains the ephemeral freshness signature established in T4.
- Confirmed: unobserved → `unknown_unobserved` / `domain_profile: unknown` with no
  findings; observed-empty → `observed_empty` / `empty_or_nascent` with a `target_empty`
  claim traceable to the inventory observation.
- Confirmed: replacement fixture — a prior software shape does not leak into a later
  records/documents basis.
- Confirmed: observe/orient created no receipts, artifacts, App Journal entries, mutation
  records, or `mcp.sqlite3` on any probe target.
- Confirmed: CLI and MCP return the same `awareness_id` and `domain_profile` for the same
  instance; MCP owns nothing new.
- Confirmed: mechanical tools import none of substrate, awareness, mcp, mutation,
  receipts, or journal (AST scan); `product/**` imports nothing from `factory`, `tests`,
  or `.builder` (31 modules).
- Confirmed: no AI, embedding, vector, OCR, parser graph, cartridge, rollback, workflow,
  GUI, MCP-expansion, or mutation-expansion surface in the T7 diff.
- Confirmed: T6 repairs hold under re-probe — `notifications/initialized` draws no
  response; manifest `inputSchema` is projected unmodified with `additionalProperties:
  false`; the old in-arguments `_authority` hatch now yields `authority_denied`; the
  envelope `authority: apply` performs a governed, receipted write; `sidecar mcp` after
  adapter removal returns a JSON `mcp_unavailable` envelope.
- Confirmed: T0–T6 remain PARKED, P1–P6 credited, P7–P8 UNSCORED, T8 undeclared.

## Independent Measurement

Clean off-repository copy at `32bae24` (CRLF churn in `.builder/evidence` reverted to
committed bytes; `git status` empty), Linux 6.8 / CPython 3.13.15 / pytest 8.4.2 /
Ruff 0.15.22:

- `python -m pytest -q`: 64 passed. Ruff: passed. `git diff --check`: clean.
- T7 gate PASS 12/12; T6 11/11; T5 13/13; T4 14/14; T3 12/12; T2 13/13; T1 9/9;
  T0 13/13. No `__pycache__` produced by any run.

Probes (installed instances, `factory attach`, then `substrate refresh` /
`awareness refresh`):

| Probe | Target | Result |
|---|---|---|
| P1 | copy of `product/` (Python + 5 `manifest.json`) | `domain_profile: mixed` |
| P2 | `pyproject.toml`, `src/app.py`, `src/util.py`, `README.md` | `mixed` |
| P2b | `package.json`, `index.js`, `lib.js` | `mixed` |
| P3 | 2-file Python project with `git init && commit` | 48 resources, 45 under `.git/`, 27/27 `.git` files hashed; `software` (no README) |
| P3b | this repository (minus `.sidecar`, `tests`) | 2,307 resources, 1,840 under `.git/`, 0.52 s, 9.0 MB db, `mixed`, `weak_material_count: 1` |
| P4 | 3,000 files under `node_modules` + 2 real files | 3,104 resources, 6,208 observations, 30,835 relations, 17.3 MB db, 0.71 s; awareness 5 findings / 100 of 3,104 handles / 7.2 KB; weak claim lists 3,101 handles; `mixed` |
| P5 | 50 unchanged files, three refreshes | versions 50/100/150; relations 501/1002/1503 |
| P6 | 1.1 MB file overwritten, size and mtime preserved | `awareness current` → `current` |

## Requirement Matrix

Against `0044` completion evidence 1–11 and `0045` amended evidence A1–A4:

1. Unobserved → unknown, no richness — PASS (fixture + probe).
2. Observed-empty → thin truthful records — PASS.
3. Substantial software fixture → traceable software claim and findings — PASS on the
   four-file fixture; **FAIL on every real software target probed** (profile `mixed`).
   "Substantial" is not met.
4. Mixed records/document fixture with honest limitations — PASS.
5. Domain claims trace to observations/evidence/resources — PASS (trace fixture; spot
   check of claim → `derived_from` → observation → `supported_by` → evidence → `concerns`
   → resource).
6. Awareness consumes T3 handles via APIs, no table ownership, no scanning — PASS.
7. No receipts/journal/mutation/MCP state from observe/orient — PASS (fixture + probes).
8. CLI and MCP read the same world — PASS.
9. Lower layers do not import upward — PASS (AST).
10. No out-of-scope surfaces — PASS.
11. Canonical pytest, Ruff, diff check, T7 gate, cumulative gates — PASS, reproduced on a
    second platform; provenance qualified by the dirty-tree advisory.
A1. Weak material represented metadata-only with limitations — PASS for large, binary,
    vendor-listed, and unparsed-document material; **FAIL for VCS internals**, which are
    neither flagged nor limited.
A2. No unsupported content-understanding claims — PASS.
A3. Large/vendor material does not dominate or derail refresh/orientation — **PARTIAL**:
    orientation stays compact; the refresh path records every vendor and `.git` file
    exhaustively and hashes the latter. On a real repository 80% of the substrate is
    `.git`.
A4. Weak-material limitations exposed through T3 handles — PASS.

Against the `0044`/`0045` discrimination plans: "passing with one generic non-empty
fixture while failing to distinguish software, mixed, and empty" — **present in the
candidate**. "Traversing or summarizing vendor/dependency-like trees in a way that
overwhelms the compact prototype orientation" — orientation is not overwhelmed; the
substrate is, and the amendment's own wording covers "the refresh/orientation path".
The remaining named wrong implementations (unobserved-as-empty, awareness scanning,
unsupported claims, extension overclaim, historical leakage, automatic memory, upward
imports) are rejected by the fixtures.

## Closure Review Pass

The live repository is not yet strong enough to justify PARKED disposition or P7 credit.
The ownership and honesty invariants are sound. What is missing is that the tranche whose
declared outcome is truthful breadth *across a substantial software target* has not been
exercised on one, and the two results that appear when it is — misclassification and
generated-subtree dominance — are both listed in the declaration as implementations the
gate must reject. Both are bounded repairs inside T7's surfaces.

For the operator's stated bar — right before T8 — the record findings matter as much as
the code findings. T8 is the release-and-STOP tranche; it will seal evidence, and it
will run the acceptance walk on exactly the target classes probed here. Going into it
with unruled carried findings, receipts whose `head_commit` does not contain the measured
code, and no Linux evidence in the construction record would carry every one of those
gaps into the sealed artifact's provenance.

## Recommendation

Return T7 to VERIFYING for a bounded repair within T7's declared surfaces:

1. Make the domain-profile decision discriminate (records/documents signals beside
   software markers should not by themselves produce `mixed`); remove config-JSON and
   project markers from the records class.
2. Recognize VCS internals and common generated/build/cache directories as generated
   weak material — metadata-only, limitation recorded, no hashing — or exclude them with
   an explicit recorded limitation.
3. Replace the four-file "substantial" fixture with a realistic software known-answer
   fixture (README, config JSON, a `.txt`, a `.git` directory, a small vendor tree) that
   asserts `software`, and keep a true mixed fixture that asserts `mixed`.
4. Commit before the authoritative gate run and cite receipts whose `head_commit`
   contains the measured source.

Before T8 is declared, independent of T7:

5. Rule on carried findings C1–C5 and H1–H3 in a journal entry the Plan points to.
   Declining is a legitimate ruling; silence is not.
6. Decide whether unconditional per-refresh substrate growth and awareness truncation
   are accepted prototype limitations (recorded as such) or T8 preconditions.
   *Ruled — see the Operator Ruling addendum at the end of this file.*
7. Add `.gitattributes` for `.builder/evidence/**/*.json` so evidence bytes stop being
   rewritten by checkout.

Items marked ADVISORY and INFORMATIONAL do not block T7 approval. This review is
evidence, not a ruling. The operator grants approval, PARKED status, and P7 credit;
T0–T6 remain parked and are not reopened by anything here.

---

## Addendum: Operator Ruling on the Three Decisions

Recorded: 2026-09-02T12:24:36Z
Ruling: APPROVED by the Operator, in conversation, adopting the Reviewer's recommendations
as stated below. This addendum records the ruling as review evidence; the Builder carries
it into the T7 resubmission entry (expected `0049`) as three explicit sentences so the
disposition lives in construction history and not only here.

All three land inside the T7 return, in files T7 already modifies, and none may require
narrowing a parked gate.

**D1 — Unconditional per-refresh substrate growth: FIX NOW, with a stop rule.**
`_insert_evidence` hashes a body that contains `observed_at`, so evidence is addressing a
timestamp rather than content; unchanged files receive new evidence and a new version on
every refresh. Repair: remove `observed_at` from the hashed evidence body (it remains on
the observation and version rows), so an unchanged file yields the same digest, the
`INSERT OR IGNORE` dedupes it, and `_version_id(handle, evidence_id, mtime)` is stable.
Changed files still produce new evidence and a new version, so T3's changed-file fixture
continues to pass and begins to discriminate. **Stop rule:** if the repair cannot be made
to pass without editing `.builder/gates/t3_epistemic_substrate.py`, that is the signal
that T3 semantics are being changed rather than repaired; in that case fall back to
accept-and-record as a prototype limitation and bind a fix to after Product STOP. The
T3 gate must pass untouched for this to count as a repair.

**D2 — Silent awareness truncation: FIX NOW.** `source_handles[:100]`, `resources[:20]`,
`claims[:10]` with no disclosure. Repair: add shown/total counts to the revision summary
and one limitation line whenever truncation occurs. T7 already modifies
`_observed_limitations` and the summary dict; T4's gate is term-based on `awareness.py`
and is not expected to require change. Accept-and-record was considered and rejected
because the T8 acceptance walk on a substantial target would surface it immediately and
Charter invariant 9 / P4 require unknown to be explicit.

**D3 — Metadata-only freshness (size + mtime): ACCEPT; fix the limitation wording only.**
Not hashing weak material is the correct consequence of the previous return; partial
hashing would either reintroduce the read or remain gameable. The same-size, same-mtime
overwrite requires deliberate mtime preservation and is accepted as a prototype
limitation. Repair: the limitation text emitted by `_domain_signal` for large,
binary/media, and vendor material must state that content changes to such material are
detected only through size and mtime. T5 stale-refusal inherits the blind spot; T5's
changed-path measurement reads bytes independently and is unaffected.

Resubmission expectations following this ruling: the T7 gate, T3 gate, and full
cumulative set must pass from a committed tree whose `head_commit` contains the measured
source (see the recurring provenance advisory above), and the `0049` entry must state
D1–D3 and their outcomes explicitly, including whether D1 took the repair path or the
stop-rule path.
