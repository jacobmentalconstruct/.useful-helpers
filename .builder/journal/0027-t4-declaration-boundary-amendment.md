# 0027 - T4 declaration boundary amendment

Date: 2026-08-27

Status transition: T4 Awareness DECLARED -> DECLARED, amended.

## Operator review finding

Oversight accepted the T4 declaration shape but identified three boundary ambiguities to
remove before implementation:

- awareness could be read as authorized to bypass the T3 owner through direct SQL
  against T3-owned tables;
- direct target freshness signatures needed an explicit epistemic boundary; and
- direct `operation:` and `journal:` handles were too broad for the initial T4 awareness
  contract.

This does not reopen T2 or T3. It does not redesign T4.

## Amendment

The effective T4 declaration is amended as follows:

- T4 reads T3 semantics only through `product/core/substrate.py` APIs and handles.
  Verified storage remains appropriate for T4's own awareness tables, not for direct
  interpretation of T3-owned tables.
- A direct cheap target signature used by T4 is an ephemeral freshness/invalidation
  signal only. It cannot create awareness findings or epistemic facts. A missing,
  incompatible, or weak comparable basis yields `unknown`; a provable mismatch yields
  `stale`; only a sufficiently comparable matching basis can yield `current`.
- Initial awareness directly references T3-owned resource/path, version, observation,
  evidence, claim, and provenance handles. T2 receipt or App Journal information is not
  an independent T4 input and may appear only if mediated by an owning provenance layer.
- T4 should use one canonical awareness-owned handle form: `awareness:<digest-or-id>`.

All other T4 scope, non-goals, completion evidence, implementation order, and STOP
position remain as declared in `0026`.

## Implementation approval

The operator direction authorizes implementation under this amended declaration and
requires the builder to stop at AWAITING_APPROVAL. T4 must not be parked, P4 must not be
credited, and T5 must not begin without explicit operator approval.
