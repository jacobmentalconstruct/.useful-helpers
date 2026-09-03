# 0052 - Pre-T8 Housekeeping and Rulings

Date: 2026-09-03

Status: COMPLETE - pre-T8 housekeeping recorded. T8 remains PROVISIONAL and unstarted.

## Context

Entry `0051-t7-park.md` parked T7 and left Product STOP incomplete because P8 remained
UNSCORED. Before T8 declaration, the operator approved the recommended pre-T8 rulings for
line-ending/canonical-byte policy and carried findings C1-C5/H2-H3. This entry records
that bounded housekeeping. It does not reopen T0-T7, does not declare T8, and does not
grant P8 credit.

## Rulings and Disposition

- H1 line endings: resolved before T8 by adding `.gitattributes` with canonical LF text
  policy for repository source/authority/evidence text and binary treatment for opaque
  archives, databases, and media. Historical receipts remain historical and are not
  rewritten. Future release and receipt SHA-256 values should be understood over the
  committed canonical LF bytes unless a later authority explicitly states otherwise.
- C1 gate/prose coupling: resolved before T8. T2/T3/T5 gate exemptions now use explicit
  gate-owned constants rather than reading editable `TRANCHE_PLAN.md` prose for
  provisional tranche status.
- C2 MCP governed mutation parity: carried into T8. T8 must prove the installed release
  exposes the governed mutation lifecycle consistently through the required consumer
  entrances, or explicitly account for any accepted limitation in the T8 declaration.
- C3 MCP client conformance: carried into T8. T8 should include a release/lifecycle
  smoke witness sufficient to substantiate the claimed MCP entrance rather than relying
  only on internal adapter tests.
- C4 gate provenance consistency: carried into T8/final release evidence. Historical T0
  receipts are not rewritten, but final release evidence should consistently include
  head commit, working-tree state, and source digest/provenance where the active gate
  format supports it.
- C5 parked-gate discrimination audit: declined as a reopen trigger absent a concrete
  failed parked premise. It remains a known historical limitation, not active T8 scope by
  itself.
- H2 README/status staleness: closed by the existing parked-state synchronization and
  this entry's current-state updates.
- H3 T6 external evidence-root display failure: closed by the existing T6 gate
  `_display_path` handling. No T6 reopen is required.

## Changed Surfaces

- `.gitattributes`
- `.builder/gates/t2_runtime_receipts_work_memory.py`
- `.builder/gates/t3_epistemic_substrate.py`
- `.builder/gates/t5_governed_mutation.py`
- `.builder/gates/t7_domain_truth.py`
- `.builder/TRANCHE_PLAN.md`
- `.builder/CURRENT_STATE.md`
- `README.md`

## Evidence

- Commit `e4e3b62`: added canonical LF attributes and replaced Plan-prose gate
  exemptions with explicit gate-owned constants.
- Commit `45502a8`: preserved failed Windows T7 receipt
  `.builder/evidence/T7/20260903T023940Z-0cb199c7/t7-gate.json`, showing the original
  Python temp cleanup failure under the managed host sandbox.
- Commit `649d91b`: preserved failed Windows T7 receipt
  `.builder/evidence/T7/20260903T024321Z-b158e0c9/t7-gate.json` and hardened T7 fixture
  cleanup.
- Failed sandbox-only T7 receipt:
  `.builder/evidence/T7/20260903T024631Z-2ef4ccfc/t7-gate.json`; the product checks
  passed except cleanup/hygiene dependent on the managed sandbox denying Python directory
  deletion.
- Passing Windows T7 receipt:
  `.builder/evidence/T7/20260903T024916Z-b8e05b2a/t7-gate.json`, 15/15,
  SHA-256 `020AFF80128955113FB5E1DB99A70F9AB6CC4EEB963ACB0A1E7B259B754894D3`.
- Focused changed-gate receipts:
  - T2 `.builder/evidence/T2/20260903T025046Z-5a9503bc/t2-gate.json`, 13/13,
    SHA-256 `37112B3A5372A03C7980167A57E7FE6680171E2909512FBB58B483CBC3106842`.
  - T3 `.builder/evidence/T3/20260903T025043Z-82fbc767/t3-gate.json` failed only
    `repository_hygiene` during the first parallel housekeeping run after other gates
    had used `tests/.runtime`; it is preserved as attempted evidence, not the
    authoritative T3 housekeeping receipt.
  - T3 `.builder/evidence/T3/20260903T025203Z-fafd2fba/t3-gate.json`, 12/12,
    SHA-256 `5934B8F7ADE9607D11754E251EDFB23F70929D38DB39DC97CBE2ED8720D8DEE0`.
  - T5 `.builder/evidence/T5/20260903T025046Z-377d340b/t5-gate.json`, 13/13,
    SHA-256 `8C14483AA5F869923DA0700A9DD20D1C6684B8DCA3C30DF21154E1CC6CD86215`.
- Canonical pytest: `python -B -m pytest -q` passed.
- Ruff: `python -B -m ruff check . --no-cache` passed.
- Diff hygiene: `git diff --check` passed.
- Gate coupling check: `rg "TRANCHE_PLAN|PROVISIONAL\" not in plan|\| PROVISIONAL" .builder\gates -n`
  returned no matches.

## Next

The next builder action is to prepare the T8 Release and STOP declaration for operator
review. T8 must address the carried C2/C3/C4 items in its declaration and gate plan. Do
not implement T8, grant P8 credit, or claim Product STOP until T8 is declared, approved,
implemented, reviewed, and operator-parked under the BCC protocol.
