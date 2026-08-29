# External Review: T5 Governed Mutation Loop

Date: 2026-08-29T10:43:44Z
Reviewer: The Reviewer
Reviewed commit: 10bcc00d794701ffcff777a2afbbb4988a0a5039
Reviewed evidence: `.builder/journal/0036-t5-governed-mutation-loop-declaration.md`; `.builder/journal/0037-t5-execution-start.md`; `.builder/journal/0038-t5-awaiting-approval.md`; `.builder/evidence/T5/20260829T095546Z-e30c36d7/t5-gate.json`; live focused/canonical pytest, Ruff, and diff check

## Disposition

APPROVE CANDIDATE

## Executive Finding

The T5 candidate appears complete for the declared P5-sized outcome. It implements the minimal governed mutation loop without widening into a workflow engine: fresh mutation state starts blank; preview records a bounded `write_file` change without applying; approval binds to the preview digest and reviewed basis; missing/mismatched/stale apply is refused before launch; approved apply routes through the existing control plane; changed paths are independently measured; verification absence is recorded honestly; substrate and awareness refresh after successful mutation; and mutation records link the distinct receipt, artifact, verification, awareness, and optional App Journal records. I recommend operator approval, PARKED status for T5, and P5 credit.

## Findings

- [NOTE] No approval-blocking T5 finding identified.
  Evidence: `product/core/mutation.py`; `product/core/storage.py`; `product/core/control.py`; `tests/test_t5_governed_mutation.py`; `.builder/gates/t5_governed_mutation.py`; T5 receipt `20260829T095546Z-e30c36d7`.
  Required action: none.

- [ADVISORY] Preview payload integrity currently relies on mutation-table immutability rather than recomputing `preview_digest` from `payload_json` at apply/read time.
  Evidence: `product/core/mutation.py::preview_write` computes and stores `preview_digest`; `product/core/mutation.py::read_preview` returns stored `payload_json` and stored `preview_digest`; `product/core/mutation.py::apply` compares approval digest to stored preview digest.
  Required action: none for T5 closure; consider recomputing digest from decoded payload before apply in a future hardening pass if runtime-state tamper resistance becomes in scope.

- [ADVISORY] Independent changed-path measurement is whole-target and memory-bound.
  Evidence: `product/core/mutation.py::_target_snapshot` walks `context.target_root.rglob("*")` and hashes each file with `read_bytes()`.
  Required action: none for the one-write T5 witness; carry to T7 truthful breadth/performance limitations.

## Boundary Checks

- Confirmed: T5 owns mutation previews, approvals, records, verifications, links, and mutation-loop policy through `product/core/mutation.py`.
- Confirmed: approved apply routes through `ControlPlane(context).invoke("write_file", ..., authority="apply")`; T5 does not create a private write backend.
- Confirmed: T5 calls App Journal, substrate, awareness, and runtime receipt owners rather than directly writing their tables.
- Confirmed: T5 repairs migration version stamping and advances schema version to 5 with mutation-owned tables.
- Confirmed: child process environment is allowlisted through `product/core/control.py::_child_environment`.
- Confirmed: no MCP, GUI, local AI, embeddings/vector index, domain cartridge, rollback platform, planner, workflow engine, release/update/removal, or construction-role runtime concept was introduced.
- Confirmed: T0-T4 remain PARKED; T5 remains AWAITING_APPROVAL; P5 is not credited; T6 has not begun.

## Evidence Checked

- Read Reviewer manifest and current state/plan surfaces.
- Read T5 declaration, execution start, and awaiting approval journals: `0036`, `0037`, `0038`.
- Inspected T5 receipt `.builder/evidence/T5/20260829T095546Z-e30c36d7/t5-gate.json`: PASS 13/13 from clean commit `62e321e2abbe68da8693ca3562bbacafcf3ea5a1`.
- Inspected later T5 receipts `20260829T101212Z-fe751942` and `20260829T101334Z-62008e69`; the former is hygiene-only FAIL for generated cache directories, and the latter is PASS with the same T5 source digest.
- Inspected current HEAD diff from authoritative receipt commit: later changes are documentation/evidence plus a T0 gate update, with no product, product-test, or T5-gate drift.
- Inspected `product/core/mutation.py`, `product/core/storage.py`, `product/core/control.py`, `product/core/cli.py`, `tests/test_t5_governed_mutation.py`, and `.builder/gates/t5_governed_mutation.py`.
- Ran `python -B -m pytest tests\test_t5_governed_mutation.py -q -p no:cacheprovider`: 8 passed.
- Ran `python -B -m pytest -q -p no:cacheprovider`: 48 passed.
- Ran `python -m ruff check . --no-cache`: passed.
- Ran `git diff --check`: passed.
- Ran `git status --short --branch` before this review note: clean branch, ahead of origin by 8 commits.

## Requirement Matrix

- Fresh attach blank mutation state: PASS, `test_fresh_attach_starts_with_blank_mutation_state`.
- Version-accurate migration stamping: PASS, `storage._migrate(target_version=...)` and `test_migration_stamps_each_materialized_version_before_t5_schema`.
- Preview without apply: PASS, `mutation.preview_write` and `test_preview_records_reviewed_write_without_applying`.
- Approval binds to exact preview/basis: PASS, `mutation.approve`, `mutation.apply`, and preview mismatch fixture.
- Apply without approval refused before launch: PASS, no receipt or target mutation in refusal fixture.
- Stale target/basis refusal before launch: PASS, stale target fixture and `stale_basis` checks in `mutation.apply`.
- Approved apply uses existing governed host: PASS, `ControlPlane(context).invoke` path.
- Independent changed-path measurement: PASS, before/after target snapshot and changed-path assertions.
- Honest verification: PASS, durable `unavailable` verification with explicit no-target-native-verifier detail.
- Substrate then awareness refresh: PASS, successful apply fixture confirms post-mutation awareness and source handle.
- Linked distinct records: PASS, mutation links include receipt, artifact, verification, awareness, and optional journal IDs.
- Generic directory target: PASS, `plain.records` fixture does not assume a software project.
- No out-of-scope surfaces: PASS, source inspection and T5 gate.
- Lower layers do not import mutation governance: PASS, T5 gate structural check.
- Focused/canonical/Ruff/gate/cumulative evidence: PASS, live commands and recorded receipts.

## Discrimination Review

- Plausible wrong implementation: preview applies the file immediately while still returning a preview record. Rejected by focused preview fixture asserting no file and no receipt.
- Plausible wrong implementation: approval authorizes a different preview/path/content. Rejected by preview mismatch fixture, preview digest binding, and gate discrimination.
- Plausible wrong implementation: apply proceeds after unrelated target or basis drift. Rejected by stale target/basis checks before child launch and fixture asserting no receipt/mutation on stale target.
- Plausible wrong implementation: mutation trusts the tool's changed-path self-report. Rejected by before/after target snapshot measurement and changed-path assertion.
- Plausible wrong implementation: unavailable verification is converted into PASS. Rejected by explicit `unavailable` status assertions and gate discrimination.
- Plausible wrong implementation: T5 writes substrate, awareness, App Journal, or receipt state directly. Rejected by source inspection and gate owner checks.
- Plausible wrong implementation: child processes inherit broad ambient secrets. Rejected by allowlisted environment implementation and focused environment probe.
- Plausible wrong implementation: T5 assumes a software repository. Rejected by generic `plain.records` fixture.

## Closure Review Pass

The live repository is strong enough to justify operator approval/PARK/P5 credit for the declared T5 outcome. The evidence proves the consumer-visible governed mutation loop at prototype scale and preserves the construction/runtime boundary. Product STOP remains incomplete after T5 because P6-P8 remain UNSCORED.

## Residual Risk

- Preview digest recomputation from decoded payload would harden runtime-state integrity but is not required by the current trusted SQLite-owner boundary.
- Whole-target snapshot measurement is acceptable for the minimal one-write witness but should become an explicit T7 limitation/performance concern for large targets.
- Verification is honestly `unavailable`; richer target-native verification remains future scope.

## Suggested Operator Action

Approve and park T5, credit P5, and keep Product STOP incomplete because P6-P8 remain UNSCORED. Do not begin T6 until the T5 park/credit entry is recorded and the T6 declaration is prepared and reviewed.
