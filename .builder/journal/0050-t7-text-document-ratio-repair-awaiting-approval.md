# 0050 - T7 Text-Document Ratio Repair Awaiting Approval

Entry type: operator return, verification repair, and review submission
Tranche: T7 Domain Truth
Status: AWAITING_APPROVAL
Date: 2026-09-02

## Operator Return

The operator returned T7 to VERIFYING on 2026-09-02 with the direction to follow the
recommendations of Reviewer evidence at
`.builder/evidence/reviews/T7/20260902T134914Z-external-review.md`, a narrow return
against the `0049` candidate. The review confirmed that both `0048` defects were fixed
on real targets, that D1-D3 were applied as ruled, and that provenance and gate
discrimination were sound, and found two bounded items in T7's own surfaces plus one
advisory it left to the operator's choice:

1. Plain-text documents were ancillary regardless of proportion, so a notes collection
   with a helper script classified `software` (60 `.md` + 3 `.py` -> `software`).
2. The T7 gate imported the product owner in-process without disabling bytecode, so a
   plain `python` launch created `product/core/__pycache__` and failed its own
   hygiene check.
3. (Advisory) `vendor`, `build`, and `dist` were untraversed on every target, including
   records/document targets where they are ordinary folder names.

This entry preserves `0047`, `0048`, and `0049` as historical review evidence and
supersedes `0049` only as the current T7 review submission. It does not park T7, grant
P7 credit, begin T8, or reopen T0-T6.

## Repair

`product/core/substrate.py`:

- Plain-text documents (`.md`, `.rst`, `.txt`) beside software signals are ancillary
  only while they do not outnumber the software signals by more than the dominance
  ratio (2:1, `_TEXT_DOMINANCE_RATIO`). Once they do, they enter the count-ratio test
  as records/document material and the resulting claim records
  `decision = mixed_text_documents_dominate`. README/LICENSE/CHANGELOG-style named
  files remain ancillary regardless of count. The 2:1 margin, rather than strict
  outnumbering, was chosen because strict outnumbering classified this repository
  itself as `mixed` (74 `.md`/`.txt` construction entries against 44 software files),
  which the Reviewer's own probe H had just established as a correct `software`
  answer; the Reviewer's wording allowed "an equivalent bounded rule".
- `vendor`, `build`, and `dist` (`_SOFTWARE_CONDITIONAL_PARTS`) are untraversed only
  when a software marker file exists in that directory or an ancestor; VCS, cache,
  `node_modules`, `.venv`, and `venv` names stay unconditional. The traversal tracks a
  per-directory software context so nested cases resolve the same way.

`.builder/gates/t7_domain_truth.py`:

- `sys.dont_write_bytecode = True` at module import, so the gate's own in-process
  import writes no bytecode. Launched as plain `python` with neither `-B` nor
  `PYTHONDONTWRITEBYTECODE`, the gate now produces no `__pycache__` and passes
  15/15.
- Two more known-answer targets in `_known_answer_profiles`: a notes-heavy target
  (24 `.md` + 2 `.py`) must read `mixed`, and a records target with ordinary
  `vendor/` and `build/` PDF folders must read `records_documents` with those folders
  traversed.
- Two more executed mutations: `_text_documents_dominate` forced to `False` (text
  always ancillary) and `_SOFTWARE_CONDITIONAL_PARTS` emptied (vendor/build/dist
  untraversed on every target); both are rejected by the known-answer check.
- The metadata-only boundary check now anchors on `record["domain"] = _domain_signal(`
  so the software-context argument does not defeat a literal match.

`tests/test_t7_domain_truth.py` (16 cases, was 13): a notes collection with helper
scripts asserts `mixed` and `mixed_text_documents_dominate`; documentation that does
not dominate (6 `.py`, 8 `.md`) asserts `software` with `ancillary_document_count = 8`;
ordinary `vendor/`/`build/` folders on a records target assert traversal and
`records_documents`, and the same folders under a `pyproject.toml` project assert
untraversed roots only. The three new cases fail against the `1c94cf5` product source
(two on classification, one on the untraversed roots) and pass against the repaired
source.

## Note on Earlier Hygiene-Only FAIL Receipts

The Reviewer attributes the hygiene-only FAIL receipts recorded by `0042`, `0047`, and
`0048` to the gate's in-process import. That import was introduced in `cf4de91`
(the `0049` repair) and did not exist when those receipts were produced, so it cannot
have been their cause. The most plausible cause of those Windows receipts is a manual
`pytest` or Ruff invocation without bytecode suppression between gate runs; that cause
is procedural and is not closed by this entry. The gate fix does close the mechanism
the Reviewer measured on `1c94cf5`, so from this candidate forward the T7 gate cannot
fail its own hygiene check by its own import.

## Independent Measurement

Probes on installed instances after the repair:

| Probe | `1c94cf5` | `59c4ab5` |
|---|---|---|
| 60 `.md` + 3 `.py` (Reviewer A) | `software`, ancillary 60 | `mixed`, `mixed_text_documents_dominate` |
| 40 `.txt` + 1 `.py` (Reviewer A2) | `software`, ancillary 40 | `mixed` |
| 12 `.py` + 10 `.md` | `software` | `software` |
| records target with `vendor/`, `build/` PDFs + CSVs (Reviewer B) | `records_documents`, both folders untraversed | `records_documents`, 16 resources, both folders traversed, no untraversed limitation |
| `pyproject.toml` + `app.py` with `vendor/lib/dep.py`, `build/out.js` | untraversed | untraversed (`path:vendor/`, `path:build/` only) |
| this repository as target (Reviewer H) | `software`, 494 resources | `software`, 470 resources |
| realistic software fixture | `software` | `software` |

## Evidence

All receipts were produced on Linux 6.8 / CPython 3.13.15 / pytest 8.4.2 /
Ruff 0.15.22 from committed trees. No Windows receipts exist for this candidate; the
Reviewer's pre-T8 finding that Windows receipts are blocked until line endings are
pinned (carried finding H1) is unchanged and outside T7's surfaces.

Repair commit: `59c4ab5` (`Repair T7 text-document ratio and gate self-consistency`).

- Authoritative T7 gate run `20260902T140854Z-09771121` passed 15/15 at `head_commit`
  `59c4ab5` with an empty working tree, launched as plain `python` without bytecode
  suppression, SHA-256
  `FB37C03ABC0BECBB1AAB435A59D2F67628FC234A193CB30AA25D2056BD8ECB02`.
- Focused T7 pytest passed 16/16. Canonical pytest passed 72/72. Ruff passed.
  `git diff --check` passed with no warnings.

Cumulative gate evidence at `head_commit` `0ccb5f3` (which contains `59c4ab5` and the
T7 receipt), each working tree differing from HEAD only by the untracked receipts of
the gates that ran before it:

- T6 `20260902T140938Z-675dd781`: 11/11 PASS,
  SHA-256 `CC5C7623A92700CD156BFB884E5413057AE3C96B05C95D7452DD678AB99A90C6`.
- T5 `20260902T141016Z-a5874aa7`: 13/13 PASS,
  SHA-256 `9D06E79ADD499D0953650E229D2F3B857D7A427106B50F532F8DC61EACBF5F86`.
- T4 `20260902T141059Z-7238a7f1`: 14/14 PASS,
  SHA-256 `646647511E9E7BC71C18C7DD45BAC67B530BE49D7FC82EF87694CA29E5545FA1`.
- T3 `20260902T141139Z-3165b501`: 12/12 PASS with the T3 gate file unchanged,
  SHA-256 `D9999DFD8EA27D1AB0F7ECD8A2A9A23C27F6FF66441924F90CFE3D0215E38F6B`.
- T2 `20260902T141218Z-47ff381a`: 13/13 PASS,
  SHA-256 `4BA372D6CCA659C8BBCC523A4FC179B65043094575B7BB59A8DE52BF991B976B`.
- T1 `20260902T141224Z-51e6043d`: 9/9 PASS,
  SHA-256 `175A0B3FC967F145B41D63980D23A50CE419C0C194FC23FD023FC4764DF15A22`.
- T0 `20260902T141258Z-5bb1cbcb`: 13/13 PASS,
  SHA-256 `17A95E5BFE548A50A82462D0E3A9AAB0AA566F0F455190F8EEF46185A1C7B7CB`.
  This receipt still records no `working_tree` field (carried finding C4, unruled).

Receipt commits: `0ccb5f3` (T7 receipt), `ad72599` (cumulative receipts). No FAIL
receipt was produced during this repair.

## Discoveries Recorded, Not Absorbed

- Observations and their relations still accrue on every refresh (T3 design; Reviewer
  advisory, previously recorded in `0049`).
- The pre-T8 items are unchanged and are the operator's: `.gitattributes` with
  renormalization and one Windows T7 receipt (H1, now blocking Windows evidence in
  practice because `working_tree_provenance` correctly fails on CRLF-only
  modifications), and a journal ruling on carried findings C1-C5 and H2-H3 pointed to
  from the Plan. The builder notes for that ruling that receipt SHA-256 values cited in
  journals up to `0048` were computed on Windows working-tree bytes (CRLF), while those
  cited from `0049` onward were computed on Linux (LF); pinning line endings will
  change which of the two families reproduces from a fresh checkout, and the ruling
  should say which bytes are canonical.

## Current Review Position

T7 is submitted at AWAITING_APPROVAL for operator review after the bounded
text-document ratio, ordinary-folder, and gate self-consistency repair. P7 remains
UNSCORED until operator approval grants T7 PARKED status and P7 credit. T8 has not
begun.
