# External Review: T8 Release and STOP

Date: 2026-09-03T08:20:12Z
Reviewer: The Reviewer
Reviewed commit: 3254e764f61411a931c3a88897466a573f572057
Reviewed evidence: `.builder/journal/0053-t8-release-stop-declaration.md`; `.builder/journal/0055-t8-awaiting-approval.md`; `.builder/evidence/T8/20260903T073452Z-5680a19f/t8-gate.json`; T8 source digest `9c4d012549fd892d3feec81c9da5c0bc5d9d88d749f621a4fb423f28f3467fb0`; release artifact SHA-256 `5ab81c3f6dccb996e4a847100ea74f272ecf748581828c03ba0fae9b34907a90`

## Disposition

RETURN TO VERIFYING

## Executive Finding

The T8 candidate is directionally strong and passes its declared gate, focused tests, canonical pytest, Ruff, and diff whitespace checks, but the submitted evidence does not yet discriminate enough of the declared Product STOP surface to justify operator approval/PARK/P8 credit. The material gaps are bounded: the sealed artifact proof should exercise the declared breadth of CLI orientation, the Linux acceptance walk, and sealed-install MCP conformance/error behavior rather than relying on Windows-only behavioral coverage plus a Linux install/update/removal smoke.

## Findings

- [REQUIRED] The Linux evidence does not prove the declared same-artifact acceptance walk; it only attaches, reports status, updates, and uninstalls.
  Evidence: `.builder/journal/0053-t8-release-stop-declaration.md` lines requiring clean Windows/Linux use and Product STOP evidence; `.builder/gates/t8_release_stop.py` function `_linux_release_smoke`; `.builder/evidence/T8/20260903T073452Z-5680a19f/t8-gate.json` check `linux_release_smoke`.
  Required action: Add a same-artifact Linux witness that runs the minimum T8 product walk needed for P8, including substrate refresh, awareness refresh/current orientation, handle/drill use, governed mutation or explicit parity-equivalent proof, and durable-state verification; if full Linux proof cannot be produced, stop with that limitation explicit rather than claiming Product STOP.

- [REQUIRED] The sealed CLI evidence does not cover the declared empty, software, and mixed/document target classes.
  Evidence: `.builder/journal/0053-t8-release-stop-declaration.md` completion evidence item 6; `tests/test_t8_release_stop.py` tests `test_sealed_install_blank_state_relocation_update_and_removal` and `test_sealed_cli_and_mcp_complete_the_same_governed_mutation_walk`; `.builder/gates/t8_release_stop.py` check `focused_t8_product_evidence`.
  Required action: Add sealed-artifact CLI fixtures for empty, software, and mixed/document targets that prove observe/orient/current/handle drill still work from the installed artifact, without reopening T7 domain semantics.

- [REQUIRED] The C3 MCP conformance carry-in is only partially witnessed through the sealed install because error behavior is not exercised behaviorally.
  Evidence: `.builder/journal/0053-t8-release-stop-declaration.md` carried finding C3; `tests/test_t8_release_stop.py` method `test_sealed_cli_and_mcp_complete_the_same_governed_mutation_walk`; `.builder/gates/t8_release_stop.py` functions `_windows_release_lifecycle`, `_mcp_governed_mutation_parity`, and `_release_discrimination_witness`.
  Required action: Add a sealed-install MCP witness for at least one realistic error path, such as unknown method/tool, invalid arguments, stale mutation refusal through MCP, or malformed request handling, while preserving the existing owner boundaries.

- [NOTE] The current repository HEAD is later than the T8 gate commit, but the reviewed T8 source digest still matches the submitted gate digest and post-receipt drift appears limited to documentation/state/evidence surfaces.
  Evidence: current HEAD `3254e764f61411a931c3a88897466a573f572057`; T8 gate commit `bb6f58569be40aaa53c9febe224b2e811031fad4`; T8 source digest `9c4d012549fd892d3feec81c9da5c0bc5d9d88d749f621a4fb423f28f3467fb0`.
  Required action: none.

## Boundary Checks

- T8 remains `AWAITING_APPROVAL`; T8 is not parked, P8 is not credited, and Product STOP remains incomplete in `.builder/CURRENT_STATE.md` and `.builder/TRANCHE_PLAN.md`.
- T0-T7 remain parked and P1-P7 remain credited; no new evidence reviewed here reopens those parked tranches.
- T8 implementation uses release/factory/MCP/mutation surfaces and does not appear to introduce GUI, local AI, embeddings, domain cartridges, autonomous repair, rollback platform, or construction-role runtime semantics.
- MCP mutation exposure appears routed through `product/core/mutation.py` owner APIs from `product/core/mcp.py`, not through direct MCP-owned persistence.
- The sealed artifact boundary excludes `.builder/`, tests, `.git`, runtime caches, and construction material according to the T8 gate and focused test.

## Evidence Checked

- Read `.builder/evidence/reviews/REVIEWER_MANIFEST.md`.
- Inspected `.builder/CURRENT_STATE.md`, `.builder/TRANCHE_PLAN.md`, `.builder/journal/0053-t8-release-stop-declaration.md`, and `.builder/journal/0055-t8-awaiting-approval.md`.
- Inspected `.builder/evidence/T8/20260903T073452Z-5680a19f/t8-gate.json`.
- Inspected `factory/release.py`, `factory/installer.py`, `product/core/mcp.py`, `tests/test_t8_release_stop.py`, and `.builder/gates/t8_release_stop.py`.
- Verified current T8 source digest: `9c4d012549fd892d3feec81c9da5c0bc5d9d88d749f621a4fb423f28f3467fb0`.
- Ran `python -B -m pytest tests\test_t8_release_stop.py -q`: pass.
- Ran `python -m ruff check . --no-cache`: pass.
- Ran `git diff --check`: pass.
- Ran `python -B -m pytest -q`: pass.

## Discrimination Review

- A release could pass the current gate while Linux substrate refresh, awareness refresh, mutation, or MCP behavior is broken, because Linux currently proves only attach/status/update/uninstall.
- A release could pass while sealed-artifact orientation fails on empty, software, or mixed/document target classes, because the T8 focused tests do not exercise those declared classes from the installed artifact.
- A release could pass while sealed MCP conformance has poor error behavior, because the C3 behavioral path covers successful initialize/list/call/shutdown and relies on static discrimination for MCP apply exposure.

## Closure Review Pass

The live repository is not yet strong enough to justify operator approval, T8 PARKED disposition, P8 credit, or Product STOP. The remaining work is not a T8 redesign; it is a bounded evidence repair aligning the sealed artifact acceptance witnesses with the declared closure sentences.

## Residual Risk

- The release artifact and Windows lifecycle may be sound while cross-platform consumer behavior remains under-proven.
- STOP credit would currently rest partly on source-tree T7 evidence rather than sealed artifact acceptance evidence for target breadth.
- MCP adapter removability is asserted by lifecycle scope and product boundaries, but the missing conformance/error witness keeps adapter behavior under-discriminated for closure.

## Suggested Operator Action

Return T8 to VERIFYING for the three bounded witness repairs above. Instruct the Builder not to broaden T8 scope; the repair should strengthen sealed-artifact acceptance evidence for Linux, declared target breadth, and MCP conformance/error behavior, then rerun focused T8, canonical pytest, Ruff, diff check, the T8 gate, and cumulative receipts before resubmitting AWAITING_APPROVAL.
