# T0 Review Amendment

- Date: 2026-08-25
- Tranche: T0 Bootstrap
- Entry class: amendment and replacement review submission
- Transition: AWAITING_APPROVAL -> IMPLEMENTING -> VERIFYING -> AWAITING_APPROVAL
- Operator terminal disposition: not granted
- Supersedes: `0002-t0-awaiting-approval.md` as the current review submission only

## Operator review finding

The operator accepted T0's structure and direction but found that the declared
one-authority invariant was not realized. Architecture repeated Charter-owned product
identity, invariants, topology, work-loop, and anti-goal facts. The Protocol compressed
the BCC-owned required workflow, and the Plan repeated the journal-owned T0 declaration
body. The existing gate proved that authority paths were listed but did not discriminate
against these plausible second owners.

Entries `0001` and `0002` remain unchanged because they accurately record the state and
beliefs at their times. This entry replaces `0002` only as the current submission.

## Repair

- Recast `docs/ARCHITECTURE.md` as a consumer of Charter facts. It now records current
  installed structure, module responsibilities, control mechanics, substrate behavior,
  tool contracts, limitations, and provisional evidence.
- Replaced the Protocol's required-loop restatement with a repository-mechanism mapping
  to the BCC-owned stages.
- Removed the T0 declaration body from the Plan and retained only journal pointers under
  its sequence/status/dependency/closure ownership.
- Strengthened the existing `authority_ownership` gate assertion with narrow structural
  checks for those three duplicate-owner forms. No generalized semantic framework was
  introduced.

## Mutation witness

After the repaired focused check passed, a forbidden `## Product identity` section was
temporarily restored in Architecture. The real T0 gate failed 11/12 solely at
`authority_ownership` with:

> Architecture declares Charter-owned normative sections: Product identity

The mutation receipt is
`T0/20260825T152900Z-83f07731/bootstrap-gate.json`, SHA-256
`227629FFF94AAD93C9E3E660173AB630E83832924C508BFD4479F1705DC2CC53`.
The duplicate section was then removed.

## Replacement review evidence

The repaired full gate passed 12/12 and produced the authoritative review receipt
`T0/20260825T152930Z-8ecc1428/bootstrap-gate.json`, SHA-256
`B4356FB767FA9AEFE64BE04B9EA9CF7D51744068068DB433C597FE40E5F3EC4C`.

Independent post-receipt checks passed:

- canonical `python -m pytest`: 10 passed;
- `python -m ruff check . --no-cache`: all checks passed;
- focused `authority_ownership`: singular owners with mappings or pointers;
- `git diff --check`: no whitespace errors.

Review-document synchronization after that receipt was limited to this entry, Plan and
Current State pointers, and the README receipt pointer. It receives focused checks only,
so no recursive latest-receipt chain is created.

## Current position

T0 is AWAITING_APPROVAL and is not PARKED. P1-P8 remain UNSCORED. The provisional
product source was not redesigned or audited, and T1 has not begun. The next action is
operator review of this replacement submission.
