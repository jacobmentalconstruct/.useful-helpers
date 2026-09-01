# External Review: T7 Domain Truth Amended Declaration

Date: 2026-09-01T12:45:01Z
Reviewer: The Reviewer
Reviewed commit: 4313dd7b2e5db98edf70100d5eeef7121a3910ba
Reviewed evidence: .builder/journal/0044-t7-domain-truth-declaration.md; .builder/journal/0045-t7-declaration-weak-material-amendment.md; .builder/evidence/reviews/T7/20260901T115016Z-external-review.md; .builder/CURRENT_STATE.md; .builder/TRANCHE_PLAN.md; docs/PRODUCT_CHARTER.md; docs/ARCHITECTURE.md; .builder/journal/0039-t5-park.md; .builder/journal/0043-t6-park.md

## Disposition

APPROVE CANDIDATE

## Executive Finding

The amended T7 declaration is ready for operator approval to begin implementation. Entry `0045` resolves the prior required finding by making weak-material degradation an explicit T7 completion and discrimination requirement, while preserving the original P7 scope: deterministic T3-owned domain/profile facts, compact T4 awareness projection, truthful limitations, unobserved-vs-empty distinction, CLI/MCP as entrances, and no expansion into parsers, AI, cartridges, GUI, mutation, release, or construction-role runtime machinery.

## Findings

- [NOTE] The prior required weak-material witness finding is resolved by the amendment.
  Evidence: .builder/journal/0045-t7-declaration-weak-material-amendment.md `Amended Scope`, `Amended Completion Evidence`, and `Amended Discrimination Plan`
  Required action: none.
- [NOTE] The amended declaration remains correctly bounded as a declaration only.
  Evidence: .builder/journal/0045-t7-declaration-weak-material-amendment.md `Operator Direction` and `Current Review Position`; .builder/CURRENT_STATE.md; .builder/TRANCHE_PLAN.md
  Required action: none.

## Boundary Checks

- Confirmed: T7 remains `DECLARED`, not implementing, parked, or awaiting approval of implemented work.
- Confirmed: T0-T6 remain parked; P1-P6 are credited; P7-P8 remain unscored; Product STOP remains incomplete.
- Confirmed: entry `0045` supersedes `0044` only as the current declaration review submission and does not rewrite historical declaration evidence.
- Confirmed: deterministic domain/profile facts remain assigned to T3 substrate; awareness remains compact projection through T3-owned handles.
- Confirmed: awareness may not directly scan the target for domain findings.
- Confirmed: CLI and MCP remain entrances rather than capability owners.
- Confirmed: observe/orient may not create receipts, App Journal entries, mutation records, or MCP-private state merely from domain truth work.
- Confirmed: local AI, embeddings, vector search, OCR, broad parsers, cartridge/plugin frameworks, GUI, MCP expansion, mutation expansion, release/update/removal, remote/cloud services, and construction-role runtime concepts remain out of scope.

## Evidence Checked

- Read `.builder/evidence/reviews/REVIEWER_MANIFEST.md`.
- Read `.builder/CURRENT_STATE.md`, `.builder/TRANCHE_PLAN.md`, `docs/PRODUCT_CHARTER.md`, and `docs/ARCHITECTURE.md`.
- Read T7 base declaration `.builder/journal/0044-t7-domain-truth-declaration.md`.
- Read T7 amendment `.builder/journal/0045-t7-declaration-weak-material-amendment.md`.
- Read prior T7 review `.builder/evidence/reviews/T7/20260901T115016Z-external-review.md`.
- Read parked T5/T6 context in `.builder/journal/0039-t5-park.md` and `.builder/journal/0043-t6-park.md`.
- Searched current repository for T7 transition, weak-material, domain, large, binary, vendor, unparsed, and schema terms.
- `git rev-parse HEAD` -> `4313dd7b2e5db98edf70100d5eeef7121a3910ba`.
- `git status --short --branch` before this review note -> clean branch state, `codex/t1-mechanical-host...origin/codex/t1-mechanical-host [ahead 7]`.
- `git diff --name-status HEAD~1 HEAD` -> declaration/review/state documentation and T0 evidence only; no product source, tests, T7 gate, or implementation surfaces.
- No product tests were run because this is a declaration review, not an implemented candidate review.

## Discrimination Review

- Prior plausible wrong implementation: pass only small extension-based software/document/empty fixtures while failing on real weak materials. Resolved: `0045` requires a weak-material known-answer fixture and gate rejection for omitting it.
- Prior plausible wrong implementation: claim PDF, binary, media, large, generated, vendor, or unparsed content was semantically understood from metadata only. Resolved: `0045` requires metadata-only or limited-basis representation and explicit rejection of unsupported content-understanding claims.
- Plausible wrong implementation: implement weak-material handling only in awareness prose. Rejected by `0045`, which requires T3 substrate support and T3-owned handles for awareness limitations.
- Plausible wrong implementation: let vendor/dependency-like trees dominate compact orientation. Rejected by `0045`, which requires they not exhaustively dominate or derail refresh/orientation.
- Plausible wrong implementation: treat unobserved as observed empty, scan from awareness, or create receipts/journal/mutation/MCP state while orienting. Still rejected by `0044` completion evidence and discrimination plan.

## Residual Risk

- Exact weak-material thresholds remain implementation choices; this is acceptable because `0045` requires cheap test constants while preserving the behavioral distinction.
- T7 usefulness will depend on precise limitation wording and restrained labels during implementation.

## Suggested Operator Action

Approve the amended T7 declaration, treating entries `0044` plus `0045` as the effective implementation contract, then instruct the Builder to enter IMPLEMENTING. Do not park T7, credit P7, or begin T8 until an implemented T7 candidate is submitted and separately approved.
