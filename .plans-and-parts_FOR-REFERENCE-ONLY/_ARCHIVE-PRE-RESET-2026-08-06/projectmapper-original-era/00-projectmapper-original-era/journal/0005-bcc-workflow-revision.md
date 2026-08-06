# 0005 - BCC Workflow Revision

Date: 2026-08-03

Status: closed

## Scope

Fold the granular tranche workflow into the Builder Constraint Contract so it
is required by contract, not only by project-local guidance.

## Authorization

The user explicitly authorized updating the BCC to include the workflow
specification.

## Completed

- Added `2.8 Required tranche workflow rule` to `artifacts/BCC.md`.
- Added the same `2.8 Required tranche workflow rule` to
  `.project-mapper/_docs/BCC.md`.
- Updated `_docs/TRANCHE_WORKFLOW.md` to identify BCC section 2.8 as the
  contract authority.

## Decision

The required workflow is now contractual:

```text
read constraints
declare tranche
inspect current state
record start
implement narrowly
verify and review critically
repair required issues
re-verify
document fully
capture evidence
summarize current state
park cleanly
respect closure
```

The standalone `_docs/TRANCHE_WORKFLOW.md` remains useful as the project-local
operational companion, but the requirement now lives in the BCC itself.

## Files Changed

- `artifacts/BCC.md`
- `.project-mapper/_docs/BCC.md`
- `.project-mapper/_docs/TRANCHE_WORKFLOW.md`
- `.project-mapper/_docs/_AppJOURNAL/0005-bcc-workflow-revision.md`

## Verification

- Confirmed both BCC copies contain section `2.8 Required tranche workflow
  rule`.
- Confirmed both BCC copies have matching SHA256 hashes after the update.
- Runtime behavior was not changed.

## Park Point

BCC workflow revision is closed. Future meaningful tranches must follow BCC
section 2.8.
