# 0004 - Tranche Workflow Codification

Date: 2026-08-03

Status: closed

## Scope

Review where the project workflow is currently articulated and codify the
granular tranche workflow as a project-local operational artifact.

## Findings

- `_docs/BCC.md` contains the high-level contract rules for tranche discipline,
  phase governance, documentation, testing, reporting, closeout, and park
  states.
- `_docs/PROJECT_PLAN.md` contains the project completion state and tranche
  sequence.
- `_docs/CURRENT_STATE.md` contains the current handoff state.
- No single project-local document previously contained the detailed operational
  checklist that makes review, repair, re-verification, full documentation, and
  clean parking explicit.

## Completed

- Added `_docs/TRANCHE_WORKFLOW.md`.
- Linked the workflow from README, project plan, and current-state docs.
- Left `_docs/BCC.md` unchanged as the higher-level contract authority.

## Decision

Treat `_docs/TRANCHE_WORKFLOW.md` as the active operational workflow under the
BCC. The workflow is one loop, not two: review, repair, re-verification,
documentation, evidence, current-state summary, and parking are required parts
of tranche work.

## Files Changed

- `.project-mapper/README.md`
- `.project-mapper/_docs/CURRENT_STATE.md`
- `.project-mapper/_docs/PROJECT_PLAN.md`
- `.project-mapper/_docs/TRANCHE_WORKFLOW.md`
- `.project-mapper/_docs/_AppJOURNAL/0004-tranche-workflow-codification.md`

## Verification

- Documentation links were added.
- No runtime code changed.

## Park Point

Workflow codification is complete. Future meaningful tranches should begin by
reading `_docs/TRANCHE_WORKFLOW.md` along with `_docs/BCC.md`,
`_docs/PROJECT_PLAN.md`, `_docs/ARCHITECTURE.md`, and `_docs/CURRENT_STATE.md`.
