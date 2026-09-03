# External Review: T8 Release and STOP Final Preflight

Date: 2026-09-03T18:25:27Z
Reviewer: The Reviewer
Reviewed commit: e864e85ab80c6cf0623638f788ddc0ca5a96fcfc
Reviewed evidence: `.builder/journal/0053-t8-release-stop-declaration.md`; `.builder/journal/0058-t8-final-preflight-return.md`; `.builder/journal/0059-t8-final-preflight-awaiting-approval.md`; submitted T8 gate `.builder/evidence/T8/20260903T135132Z-5f6595f9/t8-gate.json`; Reviewer rerun `.builder/evidence/T8/20260903T182454Z-13060d42/t8-gate.json`; source digest `136600c4ac287f17dbb7e8a5d89b363e49d6505257486759a26e109d9c08bf9c`

## Disposition

APPROVE CANDIDATE

## Executive Finding

The `0059` T8 final preflight candidate resolves the two remaining Reviewer return items and is strong enough, as construction evidence, to support operator approval, T8 PARKED disposition, P8 credit, and Product STOP under the Product Charter. The sealed release artifact path now proves actual payload replacement during update, sealed MCP removability, Windows/Linux acceptance, target-class orientation breadth, governed mutation, boundary cleanliness, dependency direction, and cumulative parked-tranche preservation.

## Findings

- [NOTE] The compatible update witness now proves actual installed payload replacement while preserving UUID and App Journal state.
  Evidence: `tests/test_t8_release_stop.py::T8ReleaseStopTests::test_sealed_update_replaces_installed_payload_while_preserving_state`; `.builder/gates/t8_release_stop.py::_release_discrimination_witness`; `.builder/evidence/T8/20260903T135132Z-5f6595f9/t8-gate.json`.
  Required action: none.

- [NOTE] The sealed artifact now proves CLI/host/mechanical usability after MCP adapter removal and truthful MCP unavailability.
  Evidence: `tests/test_t8_release_stop.py::T8ReleaseStopTests::test_sealed_cli_survives_when_mcp_adapter_is_removed`; `.builder/gates/t8_release_stop.py::_release_discrimination_witness`; `.builder/evidence/T8/20260903T135132Z-5f6595f9/t8-gate.json`.
  Required action: none.

- [NOTE] The prior `0056` repair items remain covered: Linux acceptance depth, sealed CLI breadth across target classes, and sealed MCP error behavior.
  Evidence: `tests/test_t8_release_stop.py`; `.builder/gates/t8_release_stop.py::_linux_release_smoke`; submitted T8 gate `20260903T135132Z-5f6595f9`; Reviewer rerun `20260903T182454Z-13060d42`.
  Required action: none.

- [NOTE] Current HEAD has no measured T8 source drift from the submitted T8 gate source digest.
  Evidence: submitted source digest `136600c4ac287f17dbb7e8a5d89b363e49d6505257486759a26e109d9c08bf9c`; Reviewer-computed source digest `136600c4ac287f17dbb7e8a5d89b363e49d6505257486759a26e109d9c08bf9c`; `git diff --name-status 403e196bdbf28b2761b78871db694aef0d9ecec0 HEAD -- factory product tests .builder\gates` returned empty.
  Required action: none.

- [ADVISORY] Public GitHub distribution still needs an operator decision before broad external testers.
  Evidence: current branch `codex/t1-mechanical-host`; `origin/HEAD -> origin/main`; `git rev-list --left-right --count origin/main...HEAD` returned `95 115`; `.UsefulHELPERS.7z` remains tracked.
  Required action: Decide whether testers receive the sealed artifact directly or whether the governed lineage becomes the public default branch and donor/archive material is retired. This is public-release preparation, not a T8 closure blocker unless the operator amends scope.

- [ADVISORY] A short consumer quickstart would reduce public-testing risk.
  Evidence: `README.md` remains primarily construction/status oriented; release manifest exposes install/update/uninstall commands.
  Required action: Before inviting broad public testers, provide concise operator-owned instructions for install, attach, observe, orient, preview/approve/apply, optional MCP use, update, uninstall, limitations, and where receipts live.

## Boundary Checks

- T8 remains `AWAITING_APPROVAL`; T8 is not parked, P8 is not credited, and Product STOP remains incomplete until explicit operator approval.
- T0-T7 remain parked with P1-P7 credited; fresh cumulative T7/T6/T5/T4/T3/T2/T1/T0 receipts all pass and no parked-tranche failed premise surfaced.
- T8 does not introduce GUI, local AI, embeddings, vector authority, domain cartridges, workflow engine, rollback platform, cloud service, or construction-role runtime semantics.
- Release assembly positively selects `product/`, `factory/`, `README.md`, and `pyproject.toml`; the artifact excludes `.builder/`, tests, gates, evidence, `.git`, caches, fixture debris, projectmapper dumps, and local sandbox paths.
- Product runtime does not import `factory/`, `.builder/`, or `tests/`; factory remains manufacture/install/update/uninstall/release.
- MCP mutation exposure routes through `product/core/mutation.py` owner APIs rather than MCP-owned mutation persistence.
- The sealed artifact proves blank runtime state, one `.sidecar` footprint, relocation identity preservation, compatible update, clean uninstall, Windows lifecycle, Linux acceptance walk, target-class orientation, governed mutation, MCP parity/error behavior, and MCP removability.

## Evidence Checked

- Read `.builder/evidence/reviews/REVIEWER_MANIFEST.md`.
- Read `.builder/CURRENT_STATE.md`, `.builder/TRANCHE_PLAN.md`, `.builder/journal/0053-t8-release-stop-declaration.md`, `.builder/journal/0058-t8-final-preflight-return.md`, and `.builder/journal/0059-t8-final-preflight-awaiting-approval.md`.
- Inspected `docs/PRODUCT_CHARTER.md`, `docs/ARCHITECTURE.md`, `README.md`, `tests/test_t8_release_stop.py`, `.builder/gates/t8_release_stop.py`, and the T8 release manifest.
- Inspected submitted T8 gate `.builder/evidence/T8/20260903T135132Z-5f6595f9/t8-gate.json`: PASS 11/11, artifact SHA-256 `ee5021c92d3e11093b7d9edcec3a7df2d59cad008abab2e3cc96b072743328a5`.
- Verified submitted T8 receipt SHA-256: `4964E06BC9BE4551F07B367932C790F522BA91DF85B483A5BA3146342765DFAD`.
- Verified submitted T8 artifact SHA-256: `EE5021C92D3E11093B7D9EDCEC3A7DF2D59CAD008ABAB2E3CC96B072743328A5`.
- Computed current T8 source digest: `136600c4ac287f17dbb7e8a5d89b363e49d6505257486759a26e109d9c08bf9c`.
- Ran `python -B -m pytest tests\test_t8_release_stop.py -q`: PASS 6/6.
- Ran `python -B -m pytest -q`: PASS 78/78.
- Ran `python -B -m ruff check . --no-cache`: PASS.
- Ran `git diff --check`: PASS.
- Ran `python -B .builder\gates\t8_release_stop.py` under the managed sandbox: FAIL only from Windows temp-directory `PermissionError`.
- Reran `python -B .builder\gates\t8_release_stop.py` unrestricted: PASS 11/11, Reviewer receipt `.builder/evidence/T8/20260903T182454Z-13060d42/t8-gate.json`, artifact SHA-256 `35769f508ea15ef31674fa3cc81198d3bc12ec2b34b5aafe1522ee78c41da90b`.
- Spot-checked submitted cumulative receipts from `0059`: T7 15/15, T6 11/11, T5 13/13, T4 14/14, T3 12/12, T2 13/13, T1 9/9, T0 13/13, all PASS.

## Discrimination Review

- A no-op update no longer passes the focused T8 suite because the sealed update test corrupts an installed runtime payload file, adds an extra installed payload marker, runs update, and asserts release bytes are restored while stale payload debris is removed.
- A sealed artifact whose CLI depends on MCP no longer passes the focused T8 suite because the sealed MCP-removal test deletes `.sidecar/core/mcp.py`, then proves status, tool discovery, and `read_file` still work.
- A sealed artifact with silent or misleading MCP removal no longer passes because `sidecar mcp` must fail truthfully with `mcp_unavailable`.
- A Windows-only, target-narrow, or success-only MCP implementation remains rejected by existing T8 witnesses for Linux acceptance, sealed target breadth, and MCP invalid-argument behavior.

## Closure Review Pass

The live repository is strong enough to justify operator approval, T8 PARKED disposition, P8 credit, and Product STOP under the Product Charter. This review is not the ruling; the operator must still explicitly approve, and the Builder must perform the normal park/STOP-credit closeout after that ruling.

## Residual Risk

- macOS remains UNSCORED by Charter design.
- The compatible update mechanism is intentionally minimal; it proves payload replacement and state preservation, not a full updater subsystem or rollback guarantee.
- Public GitHub/tester onboarding remains a release-management concern: default branch/topology and consumer quickstart should be handled before broad public testing.
- The managed sandbox temp-directory failure appears to be review-environment friction; unrestricted gate execution passed from the same source digest.

## Suggested Operator Action

Approve the T8 candidate, direct the Builder to perform the normal T8 park and Product STOP credit closeout, and keep public-distribution topology plus a concise tester quickstart as immediate post-STOP release-prep tasks before inviting broad external testers.
