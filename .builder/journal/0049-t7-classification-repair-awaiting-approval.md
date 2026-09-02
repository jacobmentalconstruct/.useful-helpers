# 0049 - T7 Classification Repair Awaiting Approval

Entry type: operator return, verification repair, and review submission
Tranche: T7 Domain Truth
Status: AWAITING_APPROVAL
Date: 2026-09-02

## Operator Return

The operator returned T7 to VERIFYING on 2026-09-02 after Reviewer evidence at
`.builder/evidence/reviews/T7/20260902T120434Z-external-review.md` found two
approval-relevant defects in the `0048` candidate, both rooted in the classifier never
having been run against a real software target:

1. Every realistic software target was classified `mixed` because `.md`, `.txt`, and
   `.json` sat in the records/documents classes and `package.json` was both a software
   and a records marker; only the hand-written four-file fixture yielded `software`.
2. `.git` and other universal generated subtrees were neither flagged nor limited; on a
   real repository 80% of the substrate was fully hashed `.git` objects, which the `0045`
   amendment names as material that must not become the center of domain truth.

The same review's addendum records the operator's ruling on three design decisions
(D1-D3), adopted in conversation and carried into this entry below.

This entry preserves `0047` and `0048` as historical review evidence and supersedes
`0048` only as the current T7 review submission. It does not park T7, grant P7 credit,
begin T8, or reopen T0-T6.

## Repair

`product/core/substrate.py`:

- The profile decision now discriminates instead of detects. `_profile_decision`
  classifies plain-text documentation (`.md`, `.rst`, `.txt`, and suffix-less
  README/LICENSE/CHANGELOG-style files) and configuration/structured-data files
  (`.json`, `.yaml`, `.toml`, `.xml`, `.ini`, `.cfg`) as software ancillary when software
  signals are present. The remaining records/documents (`.csv`, `.tsv`, `.sqlite`, `.db`,
  `.xlsx`, `.pdf`, `.doc`, `.docx`, `.rtf`) only support a second
  `target_profile_records_documents` claim when they are substantive by count: at least
  two and at least one fifth of the software signals. Otherwise the software claim
  records `ancillary_document_count`, `ancillary_config_count`, and
  `subordinate_records_document_count` with a limitation, so the subordinate material is
  explicit rather than dropped. Without software signals any records, documents, or
  config/data files still support the records/documents profile. `.json` is no longer a
  records marker; `setup.cfg`, `Cargo.toml`, `go.mod`, and `Makefile` join the project
  markers.
- Vendor subtrees (`node_modules`, `vendor`, `.venv`, `venv`) and generated subtrees
  (`.git`, `.hg`, `.svn`, `.tox`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`,
  `.idea`, `.vscode`, `__pycache__`, `build`, `dist`) are recorded as one metadata-only
  directory resource each and are not descended. Their domain signal carries a
  `generated` or `vendor_dependency` category, `weak_material = true`, and a limitation
  stating that the contents were not traversed and remain unobserved. The inventory
  observation and evidence record the untraversed subtree handles as limitations, and
  `substrate refresh` returns them.
- D1 took the **repair path**. `observed_at` is removed from the hashed body of
  `resource_version` and `domain_signal` evidence (it remains on observation and version
  rows), so an unchanged resource yields the same digest, the same evidence row, and the
  same version identifier on every refresh; version relations are inserted only when the
  version row is new. `.builder/gates/t3_epistemic_substrate.py` was not edited and passes
  12/12, so under the stop rule this is a repair, not a T3 semantics change. T3's
  changed-file fixture now discriminates versioning from unconditional insertion.
- D3 is applied as wording only, as ruled: the large, binary/media, and vendor
  limitation texts now state that content changes to such material are detected only
  through size and modification time; untraversed subtrees state that changes inside
  them are detected only through the directory's own modification time.

`product/core/awareness.py`:

- D2 is **fixed**. The revision summary carries
  `projection.{source_handles,claim_findings,resource_handles}.{shown,total}` and the
  limitations gain one line per truncated bound ("awareness lists 100 of 4426 source
  handles; the remaining 4326 are omitted ..."). The bounds themselves (100/10/20) are
  unchanged. Inventory limitations from the T3 basis (untraversed subtrees) are surfaced
  in awareness limitations. Awareness still consumes only
  `substrate.current_awareness_basis` and queries no T3 table.

`tests/test_t7_domain_truth.py` (13 cases, was 8):

- The "substantial" software fixture is now a realistic project: `pyproject.toml`,
  README/LICENSE/CHANGELOG, `config.json`, `NOTES.txt`, `settings.yaml`, `src/`,
  `tests/`, `docs/guide.md`, a `.git` directory with an object file, and a
  `node_modules` tree. It asserts `software`, ancillary counts, and no
  records/documents claim.
- A true mixed fixture (two scripts, two CSVs, a PDF, README) asserts `mixed` with
  `decision = mixed_by_count` and README excluded from supporting handles.
- A subordinate fixture (three `.py`, one `docs/spec.pdf`) asserts `software` with the
  subordinate count and limitation.
- A generated/vendor witness patches `Path.read_bytes` to fail on the `.git` object and
  vendor file, proves neither subtree is descended, and proves the refresh, weak-material
  claim, and awareness disclose the untraversed subtrees.
- An unchanged-refresh witness proves evidence and version counts are stable across three
  refreshes and grow by exactly one version when a file changes.
- A truncation witness (31 resources) proves the shown/total projection and limitation
  lines and their persistence through `awareness current`.

All six new or replaced cases fail against the `32bae24` product source and pass against
the repaired source.

`.builder/gates/t7_domain_truth.py` (15 checks, was 12):

- `known_answer_domain_profiles` executes the substrate's own traversal and profile
  decision against a realistic software target and a true mixed target and requires
  `software` and `mixed` respectively, no descent into `.git`/`node_modules`, and no
  content hash on weak material.
- `consumer_entrance_known_answer` proves the same through `factory attach` and the
  installed `sidecar.py`: profile `software`, stable `resource_versions` and
  `epistemic_evidence` across an unchanged refresh, a disclosed projection, untraversed
  subtree limitations in awareness, and `path:.git/` with no content hash.
- `working_tree_provenance` FAILS when tracked files differ from `head_commit`
  (untracked evidence receipts are the only allowed difference). It failed on the
  pre-commit dry run and passes on the committed tree, so a dirty authoritative receipt
  can no longer be cited without the discrepancy appearing in the check list.
- `discrimination_witness` adds four executed mutations on the live module (generated
  traversal re-enabled, vendor traversal re-enabled, `.json` as records, README-style
  docs as records evidence, and a detect-only profile function) and requires the
  known-answer check to reject each. The source-term checks additionally reject an
  `observed_at` field inside content-addressed evidence bodies.

## Independent Measurement

Probes on installed instances after the repair, matching the Reviewer's table:

| Probe | Before (`32bae24`) | After (`cf4de91`) |
|---|---|---|
| copy of `product/` | `mixed` | `software`, 44 resources |
| `pyproject.toml` + two `src/*.py` + README | `mixed` | `software` |
| `package.json` + two `.js` | `mixed` | `software` |
| Python project with `git init` | 48 resources, 45 under `.git/`, all hashed | 7 resources, `path:.git/` metadata-only, `software` |
| this repository as target | 2,307 resources, 1,840 under `.git/` | 452 resources, `software`, 0.49 s |
| 3,000 files under `node_modules` + 2 real files | 3,104 resources, 0.71 s | 3 resources, 0.32 s, `software` |
| 50 unchanged files, three refreshes | versions 50/100/150 (Reviewer P5) | versions 50/50/50, evidence 101/101/101 |
| 2 scripts + 2 CSV + PDF + README | - | `mixed` (`mixed_by_count`) |
| JSON export + CSV, no software | - | `records_documents` |
| 3 `.py` + one `docs/spec.pdf` | - | `software`, subordinate count 1 |

Observations and their relations still accrue per refresh by T3 design; D1 was scoped to
evidence and versions and that scope is met.

## Evidence

All receipts below were produced on Linux 6.8 / CPython 3.13.15 / pytest 8.4.2 /
Ruff 0.15.22 from committed trees; they are the first Linux receipts in the construction
record. Windows receipts for this candidate have not been produced in this entry.

Repair commit: `cf4de91` (`Repair T7 domain classification and generated subtrees`).

- Authoritative T7 gate run `20260902T131756Z-95787587` passed 15/15 at `head_commit`
  `cf4de91` with an empty working tree, SHA-256
  `9DB674E33879732B2FD15A6AE6E1555DDD3383CC02F2404278C4CED2B4B07A0A`.
- Focused T7 pytest passed 13/13. Canonical pytest passed 69/69. Ruff passed.
  `git diff --check` passed with no warnings on the Linux checkout.

Cumulative gate evidence, run at `head_commit` `0fafd18` (which contains `cf4de91` and
the T7 receipt), each with a working tree that differs from HEAD only by the untracked
receipts of the gates that ran before it:

- T6 `20260902T132410Z-6fb3b4e7`: 11/11 PASS,
  SHA-256 `C2FC62F1343BDF8F80AC3270F73382317629C537A7247CC0FA5CDE8D541F2F8C`.
- T5 `20260902T132333Z-980e8fc4`: 13/13 PASS,
  SHA-256 `3D240BD999FA9072EEDE70AA8B234DB1091284F87EB90EEC7D95288CCDCB0AAD`.
- T4 `20260902T132456Z-8fea98cd`: 14/14 PASS,
  SHA-256 `6C07E84210A56082668E9F16FE2AB2FABFEE45A88220A56FCF1EEC05CC779C0B`.
- T3 `20260902T132541Z-99ab07c0`: 12/12 PASS with the T3 gate file unchanged,
  SHA-256 `3FDA90D3AF2C14545A58807223AE14136FBFF0C2D3B54132000037FD8C887E6E`.
- T2 `20260902T132621Z-b7e9e68f`: 13/13 PASS,
  SHA-256 `51B48B1555B1913C17AE350CD1FA0B16756889834E173D665ECE69975B0845C1`.
- T1 `20260902T132632Z-d6d89b28`: 9/9 PASS,
  SHA-256 `C8CF1CDC4348E622A29F56B8182026196873F079B146869FD414802DE15826CC`.
- T0 `20260902T132704Z-26259de4`: 13/13 PASS,
  SHA-256 `7D7F3B8448D673E57D896CEEFA75F56D416126B64DF24331B15068008F024F6D`.
  This receipt still records no `working_tree` field (carried finding C4, unruled).

Receipt commits: `0fafd18` (T7 receipt), `2749e33` (cumulative receipts). A first
attempt to run the cumulative gates as one detached job was killed by the session shell
after T5 had started; it wrote no receipt and its fixture debris was removed before the
foreground runs above. No FAIL receipt was produced during this repair.

## Operator Rulings Carried Into Construction History

- **D1** (unconditional per-refresh substrate growth): the repair path was taken;
  `observed_at` no longer enters content-addressed evidence, unchanged refreshes yield
  no new evidence or versions, and the T3 gate passed untouched.
- **D2** (silent awareness truncation): fixed; shown/total counts and per-bound
  limitation lines are emitted whenever truncation occurs.
- **D3** (metadata-only freshness by size and mtime): accepted as a prototype
  limitation; only the limitation wording changed.

## Discoveries Recorded, Not Absorbed

- Observations and their relations still grow on every refresh (T3 design); not in
  scope of D1.
- The weak-material claim still embeds every supporting handle in `data_json`
  (Reviewer advisory); with subtrees no longer traversed the counts are small, and it is
  left unchanged.
- The T0 receipt lacks `working_tree`/`source_digest` (carried finding C4), no
  `.gitattributes` exists for evidence JSON (H1), and the carried findings C1-C5/H1-H3
  from the T6 review remain unruled. These are pre-T8 record items for the operator, not
  T7 surfaces, and were not touched.

## Current Review Position

T7 is submitted at AWAITING_APPROVAL for operator review after the bounded
classification and generated-subtree repair and the D1-D3 rulings. P7 remains UNSCORED
until operator approval grants T7 PARKED status and P7 credit. T8 has not begun.
