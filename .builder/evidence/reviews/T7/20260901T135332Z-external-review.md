# External Review: T7 Domain Truth

Date: 2026-09-01T13:53:32Z
Reviewer: The Reviewer
Reviewed commit: 8e4f28a8c303e8e573a84fdc2ebdcc5b2f91f1b8
Reviewed evidence: .builder/journal/0044-t7-domain-truth-declaration.md; .builder/journal/0045-t7-declaration-weak-material-amendment.md; .builder/journal/0046-t7-execution-start.md; .builder/journal/0047-t7-awaiting-approval.md; .builder/evidence/T7/20260901T134412Z-f6f03036/t7-gate.json; tests/test_t7_domain_truth.py; product/core/substrate.py; product/core/awareness.py; .builder/gates/t7_domain_truth.py

## Disposition

RETURN TO VERIFYING

## Executive Finding

The T7 candidate is broadly effective: it adds deterministic domain/profile claims in T3 substrate, projects compact T4 awareness orientation, distinguishes unobserved from observed-empty, covers software and records/documents fixtures, prevents historical profile leakage, and preserves CLI/MCP entrance boundaries. One approval-relevant weak-material invariant remains unsatisfied: the implementation advertises large/weak material as metadata-only or without content-heavy inspection, but the common resource path still reads and hashes every file before that classification.

## Findings

- [REQUIRED] Weak-material "metadata-only" and "without content-heavy inspection" claims are not behaviorally true for large files because every file is read and hashed before domain classification.
  Evidence: product/core/substrate.py:152; product/core/substrate.py:161; product/core/substrate.py:402; product/core/substrate.py:406; product/core/substrate.py:407; tests/test_t7_domain_truth.py:120; tests/test_t7_domain_truth.py:126; tests/test_t7_domain_truth.py:133; .builder/journal/0045-t7-declaration-weak-material-amendment.md `Amended Scope` and `Amended Completion Evidence`
  Required action: Repair resource/domain observation so large or otherwise metadata-only weak material is not fully read for content hashing, or change the declared/runtime claim to an honest limited-basis statement that matches actual inspection. Add a behavioral witness that would fail if a metadata-only large/weak resource is still fully read/hashed.
- [NOTE] The implemented domain ownership boundary otherwise appears sound.
  Evidence: product/core/substrate.py::_domain_signal; product/core/substrate.py::_insert_domain_claims; product/core/awareness.py::refresh; product/core/awareness.py::_domain_profile; .builder/gates/t7_domain_truth.py
  Required action: none.
- [NOTE] The T7 lifecycle chain is intact; no missing step was found going into implementation.
  Evidence: .builder/journal/0045-t7-declaration-weak-material-amendment.md; .builder/evidence/reviews/T7/20260901T124501Z-external-review.md; .builder/journal/0046-t7-execution-start.md; .builder/journal/0047-t7-awaiting-approval.md; .builder/CURRENT_STATE.md; .builder/TRANCHE_PLAN.md
  Required action: none.

## Boundary Checks

- Confirmed: `0046` records operator approval to implement under the effective `0044` plus `0045` declaration; no missing transition step was identified.
- Confirmed: T7 is `AWAITING_APPROVAL`, not parked; P7 remains unscored; T8 has not begun.
- Confirmed: deterministic domain facts are recorded in `product/core/substrate.py`; awareness projects through `substrate.current_awareness_basis(context)`.
- Confirmed: awareness does not directly query T3-owned resource, observation, evidence, claim, or relation tables for domain findings.
- Confirmed: focused fixtures cover unobserved, observed-empty, software, records/documents, weak material, replacement/no historical leakage, runtime-state separation, and CLI/MCP shared-world readback.
- Confirmed: no local AI, embeddings, vector search, OCR, broad parser, cartridge framework, GUI, MCP expansion, mutation expansion, release/update/removal, remote/cloud, or construction-role runtime surface was identified.

## Evidence Checked

- Read Reviewer manifest, current state, tranche plan, Product Charter, Architecture, and T7 journal entries `0044`-`0047`.
- Read T7 receipt `.builder/evidence/T7/20260901T134412Z-f6f03036/t7-gate.json`: PASS 11/11, source digest `faa56f7d41e6e5277bbb37f8a841999892d12b635d0f1ae31b1ffad9abd0453f`.
- Computed current T7 gate source digest from HEAD: `faa56f7d41e6e5277bbb37f8a841999892d12b635d0f1ae31b1ffad9abd0453f`.
- `git rev-parse HEAD` -> `8e4f28a8c303e8e573a84fdc2ebdcc5b2f91f1b8`.
- `git status --short --branch` before this review note -> clean branch state, `codex/t1-mechanical-host...origin/codex/t1-mechanical-host [ahead 9]`.
- `python -B -m pytest tests\test_t7_domain_truth.py -q` -> passed, 7 tests.
- `python -B -m pytest -q` -> passed.
- `python -m ruff check . --no-cache` -> passed.
- `git diff --check` -> passed.

## Discrimination Review

- Plausible wrong implementation: add labels saying `metadata_only` and "large file is represented without content-heavy inspection" while still reading full file bytes on refresh. This passes the current focused tests and gate but violates the weak-material amendment; it is present in the current candidate.
- Plausible wrong implementation: classify software or records/documents only in awareness. Rejected by substrate-owned claim implementation and awareness owner checks.
- Plausible wrong implementation: unobserved target is treated as observed empty. Rejected by focused fixture.
- Plausible wrong implementation: historical software records leak into a later records/document basis. Rejected by focused replacement fixture.
- Plausible wrong implementation: observing/orienting creates receipts, App Journal entries, mutation records, or MCP-private state. Rejected by focused separation fixture.
- Plausible wrong implementation: CLI and MCP expose different domain worlds. Rejected by focused shared-world fixture.

## Closure Review Pass

The live repository is not yet strong enough to justify operator approval, PARKED disposition, or P7 credit. The candidate satisfies most T7 breadth and ownership requirements, but the weak-material basis/content-inspection mismatch materially weakens the amended P7 evidence.

## Residual Risk

- After the weak-material repair, rerun focused T7, canonical pytest, Ruff, diff check, T7 gate, and cumulative T6/T5/T4/T3/T2/T1/T0 gates from the repaired candidate.
- The existing whole-target traversal remains acceptable for T7 if honestly bounded, but any metadata-only claim must match actual byte-inspection behavior.

## Suggested Operator Action

Return T7 to VERIFYING for the bounded weak-material inspection/basis repair only. Do not reopen T0-T6, park T7, credit P7, or begin T8 until the repaired candidate is resubmitted and approved.
