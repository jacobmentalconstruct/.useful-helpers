# External Review: T7 Domain Truth Declaration

Date: 2026-09-01T11:50:16Z
Reviewer: The Reviewer
Reviewed commit: 17d1fe5fd0425962eae6e89e8af610ec9876817a
Reviewed evidence: .builder/journal/0044-t7-domain-truth-declaration.md; .builder/CURRENT_STATE.md; .builder/TRANCHE_PLAN.md; docs/PRODUCT_CHARTER.md; docs/ARCHITECTURE.md; .builder/journal/0039-t5-park.md; .builder/journal/0043-t6-park.md; .builder/evidence/reviews/T5/20260829T104344Z-external-review.md

## Disposition

RETURN TO VERIFYING

## Executive Finding

The T7 declaration is strongly aligned with P7 and the Swiss Army knife prototype boundary: it keeps target truth in T3, awareness in T4, entrances removable, and explicitly rejects domain cartridges, AI, broad parsing, and construction-role leakage. One bounded declaration repair is approval-relevant before implementation: the declared evidence should explicitly require a large/binary/vendor-or-weak-material degradation witness, so T7 cannot pass with only small extension-based known-answer fixtures while leaving the T5-carried breadth/performance risk unowned.

## Findings

- [REQUIRED] T7 does not explicitly require a large/binary/vendor-or-weak-material degradation witness or declared limitation policy.
  Evidence: .builder/journal/0044-t7-domain-truth-declaration.md `Completion Evidence` items 3-4 and `Discrimination Plan`; .builder/journal/0039-t5-park.md `Accepted evidence`; .builder/evidence/reviews/T5/20260829T104344Z-external-review.md `Residual Risk`
  Required action: Amend the declaration to require at least one adversarial known-answer fixture containing weakly observed material such as large files, binary files, vendor/dependency-like trees, or unparsed document bodies, and require substrate/awareness to report metadata-only or otherwise explicit limitations without overclaiming content understanding or exhausting the target.
- [NOTE] The declaration otherwise preserves the correct T7 owner boundary.
  Evidence: .builder/journal/0044-t7-domain-truth-declaration.md `Ownership And Dependency Rules`, `Non-Goals`, and completion evidence items 5-10
  Required action: none.
- [NOTE] T7 is correctly declared only; it has not begun implementation, P7 is unscored, and T8 has not begun.
  Evidence: .builder/CURRENT_STATE.md; .builder/TRANCHE_PLAN.md; .builder/journal/0044-t7-domain-truth-declaration.md
  Required action: none.

## Boundary Checks

- Confirmed: T0-T6 are parked and P1-P6 are credited; P7-P8 remain unscored.
- Confirmed: T7 is `DECLARED`, not `IMPLEMENTING`, and entry `0044` does not authorize implementation, park T7, credit P7, begin T8, or reopen T0-T6.
- Confirmed: T7 facts are assigned to T3 substrate observations/evidence/claims/relations; T4 awareness remains projection over T3 handles.
- Confirmed: awareness is forbidden from direct target scanning for domain findings.
- Confirmed: CLI and MCP remain entrances and do not become capability owners.
- Confirmed: receipts, App Journal entries, mutation records, and MCP-private state are not to be created merely by observe/orient.
- Confirmed: local AI, embeddings, vector search, OCR, broad parsers, domain cartridge frameworks, GUI, MCP expansion, mutation expansion, release/update/removal, remote/cloud services, and construction-role runtime concepts remain out of scope.

## Evidence Checked

- Read Reviewer manifest and current role/process boundary.
- Read `.builder/CURRENT_STATE.md`, `.builder/TRANCHE_PLAN.md`, `.builder/BCC.md`, `.builder/TRANCHE_PROTOCOL.md`, `docs/PRODUCT_CHARTER.md`, and `docs/ARCHITECTURE.md`.
- Read T7 declaration `.builder/journal/0044-t7-domain-truth-declaration.md`.
- Read parked T5/T6 context in `.builder/journal/0039-t5-park.md` and `.builder/journal/0043-t6-park.md`.
- Read prior T5 review `.builder/evidence/reviews/T5/20260829T104344Z-external-review.md`.
- Searched for existing large/binary/metadata/substantial/domain references across `.builder`, `docs`, `product`, and `tests`.
- `git rev-parse HEAD` -> `17d1fe5fd0425962eae6e89e8af610ec9876817a`.
- `git status --short --branch` before this review note -> `codex/t1-mechanical-host...origin/codex/t1-mechanical-host [ahead 6]`.
- No product tests were run because this is a declaration review, not an implemented candidate review.

## Discrimination Review

- Plausible wrong implementation: classify software and documents only by small filename/extension fixtures, pass P7 fixture labels, and still fail to degrade usefully on a real target with `node_modules`, binaries, large media, or unparsed document bodies. Current declaration partially guards overclaiming but does not require this witness explicitly.
- Plausible wrong implementation: awareness scans the target directly to compute domain labels. The declaration rejects this through ownership rules and completion evidence item 6.
- Plausible wrong implementation: unobserved target is treated as observed empty. The declaration rejects this through completion evidence item 1 and discrimination plan.
- Plausible wrong implementation: file extensions produce unsupported claims such as parsed PDF text. The declaration rejects this through completion evidence item 4 and discrimination plan.
- Plausible wrong implementation: observing/orienting creates receipts, App Journal entries, mutation records, or MCP-private state. The declaration rejects this through completion evidence item 7 and discrimination plan.
- Plausible wrong implementation: T7 becomes a cartridge/plugin framework or AI semantic system. The declaration rejects this through explicit non-goals and scope limits.

## Residual Risk

- The declaration does not yet specify exact thresholds for "large" or which weak-material fixture shape is sufficient; the Builder can choose minimal constants during amendment if the operator approves the bounded repair.
- The declared T7 vocabulary is intentionally thin, so product usefulness will depend on clear limitation wording as much as positive domain labels.

## Suggested Operator Action

Return the T7 declaration for one bounded amendment adding explicit large/binary/vendor-or-weak-material degradation evidence and gate discrimination. After that amendment, the declaration should be suitable for operator approval to begin implementation without reopening T0-T6 or widening T7 beyond P7.
