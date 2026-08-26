# T1 Mechanical Hands + Governed Host Awaiting Approval

- Date: 2026-08-26
- Tranche: T1 Mechanical Hands + Governed Host
- Entry class: awaiting approval
- Transition: IMPLEMENTING -> VERIFYING -> AWAITING_APPROVAL
- Approved declaration: `0008-t1-mechanical-host-declaration.md`
- Execution start: `0010-t1-execution-start.md`
- Product outcome PARKED: no

## Declared outcome

Five manifest-defined mechanical operations execute against a small product-neutral
transported context with no Sidecar installation identity dependency, while the Sidecar
CLI host still validates a complete instance and refuses unauthorized, invalid, or
uncontained calls before child execution.

## What was built

- Replaced the broad four-field `ToolContext` with strict `MechanicalContext` transport
  containing only resolved `target_root` and explicit `excluded_roots`.
- Removed child-context projection from `InstanceContext`; complete identity, state,
  registry, authority, containment, attribution, process, and result policy remain above
  the subprocess boundary in the governed host.
- Adapted inventory, read, search, hash, and write mechanics to the product-neutral
  substrate without creating per-tool context classes.
- Strengthened all five manifest-owned output schemas with typed result fields and
  rejection of undeclared output fields.
- Added a generic subprocess harness proving all five tools operate without constructing
  a Sidecar instance, plus a host context probe and malicious-child refusal fixture.
- Added the sole T1 closure gate under `.builder/gates/` with manifest, dependency,
  consumer, construction-boundary, static-discovery, and hygiene checks.

## Deviations and discoveries

The first direct fixture used text-mode setup and exposed platform newline normalization;
the fixture was corrected to byte-exact known answers. Consolidation also found that
handle creation resolved symlink targets before relativizing, which could make inventory
fail on an outward-pointing symlink. Handle construction is now lexical while host path
containment remains resolved and authoritative for actual access.

The dependency mutation initially exposed a verifier defect. With a temporary
`from core import instance` dependency in `hash_file`, run
`20260826T121747Z-fa1ee0e3` incorrectly reported PASS because the AST collector reduced
that import to `core`. Its receipt (SHA-256
`ECC6F163F48D947CFD5C213CE9887D2DCF4DB0231CB607714DEC673331F03810`) is preserved but
is explicitly disqualified as closure evidence.

The collector was repaired to retain imported member paths. With the identical mutation,
run `20260826T121824Z-2c769618` failed only
`mechanical_dependency_direction`, identifying `core.instance` in the mutated tool. Its
receipt SHA-256 is
`7A28AFA026F5BB7DF117BD5979567AA0F3DB84AFC24E0B798EF1CF5030CB0215`.
The mutation was then removed.

## Verification evidence

Authoritative clean run `20260826T122010Z-b96be9ec` passed 8/8 T1 gate checks. Its
receipt is `.builder/evidence/T1/20260826T122010Z-b96be9ec/t1-gate.json`, SHA-256
`6B6B7D01BEA7DFB3EA34064285DA5FC8C4B216F27BA509ECD7A2B79719B8C4D8`, with source
digest `a35361c2f6b48cbd31f308b31b61c9121c21eabccc013f1adc0304f4b8ff3464`.

Independent closeout checks passed:

- canonical `python -m pytest`: 15 passed;
- focused T1 tests: 5 passed;
- Ruff over the repository: passed;
- `git diff --check`: no whitespace errors;
- five direct mechanical known-answer calls without Sidecar identity;
- live installed CLI/context probe transporting only `target_root` and
  `excluded_roots`;
- pre-launch refusal for malformed identity, insufficient authority, invalid input, and
  escaping path, with no malicious-child witness created;
- clean-install, empty-target, relocation/re-entry, private-subtree, symlink, observation
  footprint, and explicit apply regressions; and
- outward symlink inventory discovery without following or resolving it into a false
  target handle.

## Changed surfaces

- Product runtime: `product/core/{control,instance,tool_runtime}.py` and all five tool
  implementations/manifests.
- Product evidence: `tests/test_t1_mechanical_host.py`.
- Construction gate/evidence: `.builder/gates/t1_mechanical_host.py` and the three
  retained T1 receipts described above.
- Review authority/projections: Architecture, Tranche Plan, Current State, README, and
  journal entries `0010`/`0011`.

## Remaining risks and deferred work

Host containment followed by child path access retains a filesystem race window; no
command runner is present, and stronger descriptor-based techniques remain a measured
future safety question rather than hidden T1 scope. Output schemas constrain every
declared field but use the current small schema subset rather than conditional
success/failure unions. Cross-platform sealed-artifact proof remains T7 work.

Operational receipts, App Journal, epistemic evidence, awareness, preview/stale approval,
MCP, additional tools, and release/update behavior remain outside T1 and unchanged.

## Review position

The declared T1 outcome is implemented and mechanically verified but not operator
approved. P1/P2 and Product STOP remain UNSCORED. T1 is AWAITING_APPROVAL. The builder
has not parked T1 and has not begun T2.

