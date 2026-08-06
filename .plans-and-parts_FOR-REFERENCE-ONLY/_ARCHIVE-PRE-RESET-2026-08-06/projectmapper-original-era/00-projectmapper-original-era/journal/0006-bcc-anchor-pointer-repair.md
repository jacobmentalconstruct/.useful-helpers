# Journal Entry 0006: BCC Anchor and Pointer Repair

Date: 2026-08-03

## Tranche Declaration

Repair the BCC itself so it can serve as the single authoritative, searchable
workflow and validation contract for future tranches.

## Scope

- Add a BCC spine near the top of the contract.
- Add regex-searchable anchors to the major validation sections.
- Define a default context-entry path for entering agents.
- Collapse `_docs/TRANCHE_WORKFLOW.md` into a pointer-only helper.
- Redirect project docs away from duplicated workflow text and back to BCC
  anchors.

## Non-Goals

- No runtime behavior changes.
- No explorer UI work.
- No rewrite of historical journal entries.
- No broad documentation redesign.

## Changes

- Updated `_docs/BCC.md` with `BCC-SPINE`, `BCC-CONTEXT-ENTRY`, and stable
  `[ANCHOR: BCC-...]` section markers.
- Mirrored the same contract changes to `artifacts/BCC.md`.
- Replaced `_docs/TRANCHE_WORKFLOW.md` with a pointer-only file.
- Updated `_docs/CURRENT_STATE.md`, `_docs/PROJECT_PLAN.md`, and `README.md`
  to point to `_docs/BCC.md` anchor
  `BCC-WORKFLOW-REQUIRED-TRANCHE-LOOP`.

## Review Notes

- The original standalone workflow helper had become duplicate process text.
- Historical journal entries still contain prior workflow text as history; they
  are not operational authority.
- The BCC now carries the process and the searchable map needed to find it.

## Validation

- `python -m pytest -q -p no:cacheprovider`: `8 passed`.
- `python src\app.py`: placeholder launches with `0.1.0-core-foundation` status.
- BCC anchor audit: 24 required anchors, 0 missing, 0 duplicates in both BCC copies.
- BCC mirror audit: `_docs/BCC.md` and `artifacts/BCC.md` SHA256 hashes match.
- Duplicate workflow audit: live docs outside BCC no longer carry the required workflow checklist; historical journal entries remain historical evidence.
- Git diff checks: not available because the workspace root is not currently a Git repository.

## Park State

Parked. The BCC is now the single operational source for workflow and validation gates. `_docs/TRANCHE_WORKFLOW.md` is retained only as a pointer for convenience.
