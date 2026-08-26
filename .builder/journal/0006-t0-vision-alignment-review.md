# T0 Vision-Alignment Review Submission

- Date: 2026-08-26
- Tranche: T0 Bootstrap
- Entry class: reopen closeout and awaiting-approval submission
- Transition: IMPLEMENTING -> VERIFYING -> AWAITING_APPROVAL
- Operator terminal disposition: not granted for the reopened alignment
- Preserved historical park: `0004-t0-park.md` at commit `91413b1`
- Alignment candidate: `356f922150e999ac7fdd5bfb1740255b088525fe`

## What T0 originally established

The original approved T0 established this repository's construction authority, Product
Charter/STOP owner, tranche and journal mechanics, product/factory boundary, canonical
verification entrance, sole gate authority, preserved provisional baseline, and clean
construction/product separation. Entry `0004` and its approved evidence remain immutable
and correct for that outcome.

## What later understanding changed

The operator clarified that Sidecar Workbench is one integrated instrumentation product,
not the owner or definition of Coherent Development; that mechanical tools and App
Journal semantics are separable lower layers; that host binding is transported policy
rather than tool identity; and that construction history, runtime receipts, App Journal
memory, epistemic evidence, and awareness are distinct owners. The original authorities
did not protect all of those distinctions, and “T1 Bound Hands” risked making installed
Sidecar identity intrinsic to tools.

The finite clause-by-clause before-state, finding, evidence, and minimal amendment table
is preserved in `0005-t0-vision-alignment-reopen.md`.

## Authority surfaces amended

- `docs/PRODUCT_CHARTER.md`: owns the independent-method boundary, host/tool dependency
  direction, entrance removability, five runtime/construction state meanings, blank-start
  behavior, update preservation, revised P1-P8, aligned Product STOP, and extraction
  non-goals.
- `.builder/BCC.md`: constrains only this repository's application of Coherent
  Development and no longer claims general method ownership.
- `.builder/TRANCHE_PROTOCOL.md`: maps ORIENT through PARK to repository mechanisms
  without making the workbench a prerequisite for the method.
- `.builder/TRANCHE_PLAN.md`: replaces Bound Hands with Mechanical Hands + Governed Host;
  separates receipts/work memory from epistemic substrate; makes MCP removable; and adds
  dependency-direction and blank-state release proof.
- `docs/ARCHITECTURE.md`: records all five current tool imports of the overbroad
  `ToolContext` as provisional T1 separability debt rather than accepted architecture.
- `.builder/gates/t0_bootstrap.py`: verifies the exact method/product/state markers,
  manifest-owned contracts, absence of forbidden upward tool imports, aligned T1 wording,
  removable-entrance intent, and acknowledged current debt.
- `README.md` and `.builder/CURRENT_STATE.md`: orient to the canonical owners and current
  reopened review position.

## What remains unchanged

No product source, manifest, SQLite schema, factory behavior, tool operation, runtime
package, or product test was changed. T1 was neither declared nor implemented. P1-P8
remain UNSCORED. The prototype still proves the integrated Sidecar Workbench at STOP;
it does not require a standalone Tool Pack, App Journal distribution, scaffold kit, or
Coherent Development application.

## Why this prevents future coupling

Canonical ownership now makes upward dependency violations mechanically reviewable:
manifests own contracts; the host owns identity/context/policy; tools own mechanics;
receipts own runtime events; App Journal owns work memory; awareness owns projections;
and CLI/MCP only expose the host. T1 must reduce the measured context debt while
preserving host safety. Later extraction remains possible because lower-layer semantics
cannot legitimately import projections or construction machinery, but extraction itself
is outside current scope.

## Discrimination and discovery

Temporarily restoring `T1 Bound Hands` caused the focused alignment assertion to fail
specifically with `Plan retains identity-conflating T1 Bound Hands wording`; reverting it
restored PASS.

The first fresh clone exposed two gate defects. Receipt
`T0/20260826T054001Z-36ad267d/bootstrap-gate.json`, SHA-256
`C46EEAC4F372251141ED67B6D0635C5E716075B5F37577435CCA052278D2C7D9`, records the
whitespace-fragile journal check as FAIL at commit `fcd6978`. The gate also wrote that
receipt before its summary reporter rejected an evidence path outside the checkout.
Both verifier defects were repaired narrowly and preserved at commit `356f922`.

## Authoritative review evidence

A second newly created clone had a clean `main...origin/main` status and ran the T0 gate
against commit `356f922150e999ac7fdd5bfb1740255b088525fe`. Run
`T0/20260826T054142Z-b5ec742a/bootstrap-gate.json` passed 13/13 with SHA-256
`D1BBDBB661F2F943230ABC7CA167EBA181E7AEF03EEF26C9552533D6371711B7`.

The receipt includes 10 passing canonical pytest cases, Ruff plus AST parsing, positive
product boundary, immutable baseline provenance, journal separation, and the new vision
alignment check. Pre-commit focused verification also passed pytest, Ruff, authority
ownership, vision alignment, provisional status, journal continuity, and diff hygiene.

Review-document synchronization after the receipt is limited to this immutable entry,
Plan/Current State pointers, and README orientation. It receives focused checks only; no
recursive certification receipt is generated.

## Current position

T0 is AWAITING_APPROVAL for this bounded alignment. The historical T0 park is preserved
but does not self-approve the reopened claim. T1 remains PROVISIONAL and undeclared. The
next action is operator review; the builder stops here.
