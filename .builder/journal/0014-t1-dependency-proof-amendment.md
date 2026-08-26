# T1 Positive Dependency Proof Amendment

- Date: 2026-08-26
- Tranche: T1 Mechanical Hands + Governed Host
- Entry class: operator-returned review amendment
- Transition: VERIFYING -> AWAITING_APPROVAL
- Operator return: `0013-t1-verification-return.md`
- Amends submissions: `0011-t1-awaiting-approval.md`, `0012-t1-review-document-amendment.md`
- Product scope or behavior changed: no
- T1 outcome PARKED: no

## Operator finding

The prior `mechanical_dependency_direction` check used a blacklist of selected higher
modules. That proof could accept imports of unlisted host-owned modules such as
`core.containment` or `core.contracts`, despite the approved T1 boundary retaining those
responsibilities above the subprocess seam.

## Verification repair

The T1 gate now encodes the positive dependency invariant directly:

- `product/tools/*` may import `core.tool_runtime`, but no other `core.*` subsystem; and
- `product/core/tool_runtime.py` may import no higher `core.*` subsystem, including a
  relative import back into the Sidecar core package.

Standard-library imports and non-`core.*` tool-local or declarable mechanical
dependencies are not constrained by this narrow assertion. Product source, manifests,
runtime context, CLI behavior, and product tests were unchanged.

The gate's discrimination check applies each of `core.containment`, `core.contracts`,
and `core.instance` as an in-memory mutation to both the real `hash_file` tool source and
the real shared-runtime source. The exact assertion used on repository files fails each
tool and runtime mutation and identifies the injected dependency.

## Committed-state evidence

Commit `944ee9bace82d8272f6a134af3354c1f251d0fc2` records the complete T1 candidate and
positive dependency repair. The first committed-state gate run
`20260826T132954Z-438bad45` refused closure only because ignored bytecode caches remained;
its immutable FAIL receipt has SHA-256
`8AE11979BB59A81F4939ABF12C553E971EC914D4F04FEA92D6BBFBFA18F36FFD`. The caches were
removed without changing tracked source, and the failed receipt was preserved in commit
`4e791928cffae7226a2d3657fb95424c29b5178f`.

Authoritative T1 run `20260826T133048Z-8782844f` then passed 9/9 checks from that clean
commit. Its receipt records an empty `working_tree`, source digest
`d9c3550655f09efd0e69ab4069add127c1ef6e0483adbf1f1d5b96318ea64906`, and SHA-256
`C48A61C114C0F5D6AAA6EE8800B2D78D097ADB8BCF6DED7CE017565B8515BCD9`.
Commit `c17825a04d4ac71f1fb4c9405b45eed9b5decd53` preserves that authoritative receipt.

As explicitly requested, the current T0 gate ran once from clean commit `c17825a`.
Run `20260826T133128Z-129b3024` passed 13/13 checks, including 15 canonical product tests,
Ruff, authority ownership, positive product boundary, gate ownership, baseline
provenance, reference independence, and repository hygiene. Its receipt SHA-256 is
`03718F0D3DC8FFE2C6B57F3A3B0F727D20A1497B1A025BE68A3BC12A4442C2F8`.

All three earlier T1 receipts and entries `0011`/`0012` remain unchanged as historical
evidence. The new T1 receipt supersedes run `20260826T122010Z-b96be9ec` only as the
current closure proof; it does not rewrite the earlier submission.

## Review position

The operator-returned proof defect is repaired. T1 is again AWAITING_APPROVAL, not
PARKED. P1/P2 and Product STOP remain UNSCORED pending operator ruling. T2 has not begun.

