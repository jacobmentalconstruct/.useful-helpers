# 0045 - T7 Declaration Weak-Material Amendment

Entry type: declaration amendment
Tranche: T7 Domain Truth
Status: DECLARED
Date: 2026-09-01

## Operator Direction

The operator directed the builder to amend T7 and stop before implementation so the
Reviewer can inspect the amended declaration. This entry preserves `0044` as historical
declaration evidence and supersedes it only as the current declaration review
submission. It does not authorize implementation, park T7, grant P7 credit, begin T8,
or reopen T0-T6.

## Review Finding

The Reviewer recorded declaration review evidence at
`.builder/evidence/reviews/T7/20260901T115016Z-external-review.md` with disposition
`RETURN TO VERIFYING`.

The review found that T7 was broadly aligned with P7 and the product boundaries, but
needed one approval-relevant hardening before implementation: T7 must explicitly require
an adversarial large, binary, vendor/dependency-like, or otherwise weakly observed
material witness. Without that witness, a plausible implementation could pass tidy
software/document/empty fixtures while failing to degrade truthfully on real arbitrary
folders containing large files, binaries, vendored trees, or unparsed document bodies.

## Amended Scope

Entry `0044` remains the base T7 declaration. This amendment adds the following bounded
requirement:

T7 must include at least one weak-material known-answer fixture containing one or more of
the following:

- a file large enough that T7 should avoid expensive or content-heavy inspection;
- binary or media-like material whose bytes should not be treated as parsed text;
- vendor/dependency-like or generated-looking subtrees that should contribute metadata
  and limitations without becoming the center of domain truth;
- unparsed document bodies whose extension or container signal may be observed, but
  whose content understanding must be reported as unavailable or unknown unless a
  deterministic parser actually produced evidence.

The implementation may choose small test constants that keep the fixture cheap, but the
fixture must discriminate metadata-only or weak-observation behavior from unsupported
content-understanding claims.

## Amended Completion Evidence

T7 completion evidence must additionally prove:

1. Weakly observed material is represented with explicit metadata-only or limited-basis
   observations, evidence, claims, and awareness limitations.
2. T7 does not claim textual, semantic, PDF, binary, media, or vendor/dependency content
   understanding that was not deterministically observed.
3. Large or vendor/dependency-like material does not exhaustively dominate or derail the
   refresh/orientation path needed for the prototype acceptance walk.
4. Awareness exposes weak-material limitations through T3-owned handles rather than
   direct target scanning or prose unsupported by substrate evidence.

## Amended Discrimination Plan

The T7 gate must reject these additional wrong implementations:

- passing only small extension-based fixtures while omitting a weak-material witness;
- claiming a PDF, binary, media, large, generated, or vendor-like file was parsed or
  semantically understood when only metadata was observed;
- making weak-material handling an awareness-only heuristic with no T3 substrate support;
- traversing or summarizing vendor/dependency-like trees in a way that overwhelms the
  compact prototype orientation instead of recording clear limitations.

## Unchanged Boundaries

All other T7 scope and non-goals remain as declared in `0044`. T7 still does not add
local AI, embeddings, vector search, OCR, broad parsers, language symbol graphs,
cartridge/plugin frameworks, GUI, MCP expansion, mutation expansion, release/update or
removal lifecycle, or construction-role runtime concepts.

T7 still assigns deterministic domain/profile facts to the T3 substrate owner and compact
presentation to T4 awareness. CLI and MCP remain entrances. Receipts, App Journal
records, mutation records, and MCP-private state remain distinct and must not be created
merely by domain observation.

## Current Review Position

T7 remains DECLARED. P7 remains UNSCORED. The next action is Reviewer/operator review of
this amended declaration. Implementation requires explicit operator approval after that
review.
