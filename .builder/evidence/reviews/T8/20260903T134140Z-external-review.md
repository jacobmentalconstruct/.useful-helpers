# External Review: T8 Release and STOP Repair

Date: 2026-09-03T13:41:40Z
Reviewer: The Reviewer
Reviewed commit: a30f1dcbfc8d3f8f6f0705ad2a85420a97859ab7
Reviewed evidence: `.builder/journal/0053-t8-release-stop-declaration.md`; `.builder/journal/0056-t8-verification-return.md`; `.builder/journal/0057-t8-verification-repair-awaiting-approval.md`; submitted T8 gate `.builder/evidence/T8/20260903T131126Z-a9773084/t8-gate.json`; Reviewer rerun `.builder/evidence/T8/20260903T133637Z-cfbdc3cb/t8-gate.json`; source digest `451df64bd1ae5525a8bfdb567eb195f3a539308d26278a137439993badf82fee`

## Disposition

RETURN TO VERIFYING

## Executive Finding

The repaired T8 candidate is substantially stronger and resolves the three findings returned in `0056`: Linux same-artifact acceptance is now behavioral, sealed CLI target breadth is now covered, and sealed MCP error behavior is now witnessed. However, a closure review of every declared T8/P8 sentence found two remaining approval-relevant witness gaps: the compatible update test does not prove actual runtime payload replacement, and T8 does not prove MCP adapter removability through the sealed artifact. Both are small evidence repairs, not a T8 redesign.

## Findings

- [REQUIRED] The compatible update witness proves UUID and journal-state preservation, but not that update actually replaces the installed runtime payload.
  Evidence: `docs/PRODUCT_CHARTER.md` P1/P8 and acceptance walk; `.builder/journal/0053-t8-release-stop-declaration.md` completion evidence item 10; `tests/test_t8_release_stop.py::T8ReleaseStopTests::test_sealed_install_blank_state_relocation_update_and_removal`; `.builder/gates/t8_release_stop.py::_release_discrimination_witness`.
  Required action: Add a sealed-artifact update fixture that would fail for a no-op update. For example, attach from the release artifact, mutate or stale-mark an installed payload file or extra installed payload member, run `factory update` from the sealed payload, then assert the installed payload is restored/replaced while instance UUID and runtime engagement state remain preserved. Do not grow an updater subsystem.

- [REQUIRED] T8 does not prove the declared sealed-artifact MCP-removal condition.
  Evidence: `docs/PRODUCT_CHARTER.md` P6 and acceptance walk; `.builder/journal/0053-t8-release-stop-declaration.md` completion evidence item 9; `tests/test_t8_release_stop.py`; `.builder/gates/t8_release_stop.py`; cumulative T6 witness `tests/test_t6_mcp_entrance.py::T6McpEntranceTests::test_cli_survives_when_mcp_adapter_is_removed`.
  Required action: Add a sealed-artifact fixture that attaches from the release artifact, removes `.sidecar/core/mcp.py`, proves CLI status/tool discovery/a mechanical CLI call still work, and proves `sidecar mcp` fails truthfully with `mcp_unavailable`. This may mirror the parked T6 witness but must run through the sealed T8 install.

- [ADVISORY] Public clone/distribution topology is not ready for broad testers even if T8 later parks.
  Evidence: `git symbolic-ref refs/remotes/origin/HEAD` returns `refs/remotes/origin/main`; current branch is `codex/t1-mechanical-host`; `git rev-list --left-right --count origin/main...HEAD` returns `95 113`; `git ls-files` still tracks `.UsefulHELPERS.7z`.
  Required action: Before inviting public testers through GitHub, explicitly decide distribution: either publish the sealed artifact directly, or promote the governed lineage to the public default branch and retire/untrack donor/archive material. This is public-release prep; it need not be folded into T8 unless the operator wants T8 to own repository publication.

- [ADVISORY] The shipped README remains construction-oriented rather than consumer-oriented.
  Evidence: `README.md`; submitted artifact manifest includes `README.md` but not a standalone quickstart.
  Required action: Before public testing, provide a short tester quickstart covering install, attach, observe, orient, preview/approve/apply, MCP optional use, update, uninstall, and known limitations. Treat this as release readiness unless the operator amends T8 closure to require it.

- [NOTE] The three `0056` return findings appear resolved.
  Evidence: `tests/test_t8_release_stop.py::T8ReleaseStopTests::test_sealed_cli_orients_empty_software_and_mixed_document_targets`; `tests/test_t8_release_stop.py::T8ReleaseStopTests::test_sealed_cli_and_mcp_complete_the_same_governed_mutation_walk`; `.builder/gates/t8_release_stop.py::_linux_release_smoke`; submitted T8 gate `20260903T131126Z-a9773084`.
  Required action: none.

- [NOTE] The T8 source under current HEAD matches the submitted source digest, and the only source drift after the submitted T8 gate commit is outside T8 measured source surfaces.
  Evidence: submitted gate source digest `451df64bd1ae5525a8bfdb567eb195f3a539308d26278a137439993badf82fee`; Reviewer-computed source digest `451df64bd1ae5525a8bfdb567eb195f3a539308d26278a137439993badf82fee`; `git diff --name-status 2556cbbbff81e46f098307da0d7db38d4f84d8e7 HEAD -- factory product tests .builder\gates` is empty.
  Required action: none.

- [NOTE] The first Reviewer T8 gate rerun failed only under the sandboxed command environment with Windows temp-directory access errors; the same gate passed unrestricted.
  Evidence: failed Reviewer receipt `.builder/evidence/T8/20260903T133003Z-2a04087f/t8-gate.json`; passing Reviewer receipt `.builder/evidence/T8/20260903T133637Z-cfbdc3cb/t8-gate.json`.
  Required action: none for product closure; optionally keep in mind that the certification gate now depends on system temp access outside restrictive sandboxes.

## Boundary Checks

- T8 remains `AWAITING_APPROVAL`; T8 is not parked, P8 is not credited, and Product STOP remains incomplete in `.builder/CURRENT_STATE.md` and `.builder/TRANCHE_PLAN.md`.
- T0-T7 remain parked and P1-P7 remain credited; this review found no new evidence requiring a parked-tranche reopen.
- T8 does not appear to introduce GUI, local AI, embeddings, vector authority, domain cartridges, workflow engine, rollback platform, cloud service, or construction-role runtime semantics.
- Release assembly positively selects `product/`, `factory/`, `README.md`, and `pyproject.toml`; the gate and artifact manifest show no `.builder/`, tests, `.git`, cache, fixture, projectmapper, or local sandbox path leak inside the zip.
- Product runtime still does not import `factory/`, `.builder/`, or `tests/`; factory remains manufacture/install/update/uninstall/release.
- MCP mutation exposure routes through `product/core/mutation.py` owner APIs rather than MCP-owned mutation persistence.
- The repaired Linux witness now runs observe, awareness refresh/current, drill, governed mutation, receipt/history checks, update, and uninstall against the same release artifact.
- The repaired sealed CLI breadth witness now covers empty, software, and mixed/document target classes.

## Evidence Checked

- Read `.builder/evidence/reviews/REVIEWER_MANIFEST.md`.
- Read `.builder/CURRENT_STATE.md`, `.builder/TRANCHE_PLAN.md`, `.builder/journal/0053-t8-release-stop-declaration.md`, `.builder/journal/0056-t8-verification-return.md`, and `.builder/journal/0057-t8-verification-repair-awaiting-approval.md`.
- Read `docs/PRODUCT_CHARTER.md`, `docs/ARCHITECTURE.md`, `README.md`, and `pyproject.toml`.
- Inspected `factory/release.py`, `factory/installer.py`, `factory/cli.py`, `factory/__main__.py`, `product/bin/sidecar.py`, `product/core/cli.py`, `product/core/mcp.py`, `product/core/mutation.py`, `product/core/storage.py`, `tests/test_t8_release_stop.py`, and `.builder/gates/t8_release_stop.py`.
- Inspected submitted T8 gate `.builder/evidence/T8/20260903T131126Z-a9773084/t8-gate.json`: PASS 11/11, artifact SHA-256 `cf8c8be09a2597a5812ad2433027e1ef88e221b4b0a8369303717e4d5ec12a6e`.
- Verified submitted T8 receipt SHA-256: `8DA9BBE13266E0223F85A536876FE2679406E34074806CC8FCC48A0625BD1E99`.
- Verified submitted T8 artifact SHA-256: `CF8C8BE09A2597A5812AD2433027E1EF88E221B4B0A8369303717E4D5EC12A6E`.
- Computed current T8 source digest: `451df64bd1ae5525a8bfdb567eb195f3a539308d26278a137439993badf82fee`.
- Ran `python -B .builder\gates\t8_release_stop.py` under the default sandbox: FAIL from temp-directory `PermissionError` only.
- Reran `python -B .builder\gates\t8_release_stop.py` unrestricted: PASS 11/11, Reviewer artifact SHA-256 `3e0d301159c88460032655552cb1e945b2c1e6f0496afd261971accc1a176d8c`.
- Ran `python -B -m pytest tests\test_t8_release_stop.py -q`: PASS 4/4.
- Ran `python -B -m pytest -q`: PASS 76/76.
- Ran `python -B -m ruff check . --no-cache`: PASS.
- Ran `git diff --check`: PASS.
- Spot-checked cumulative receipts listed by `0057`: T7 15/15, T6 11/11, T5 13/13, T4 14/14, T3 12/12, T2 13/13, T1 9/9, T0 13/13, all PASS.
- Checked repository topology: current branch `codex/t1-mechanical-host`; `origin/HEAD -> origin/main`; `origin/main...HEAD` local divergence `95 113`; `.UsefulHELPERS.7z` remains tracked.

## Discrimination Review

- A no-op `factory update` implementation could pass the current T8 tests because the update witness checks preserved UUID and journal state, but does not assert a changed/stale installed payload was actually replaced by the sealed release payload.
- A sealed artifact whose installed CLI fails after `core/mcp.py` is removed could pass the current T8 gate because the T8 sealed tests never remove the MCP adapter. Cumulative T6 proves the source-install behavior, but T8 declares this as a sealed-artifact completion condition.
- The previous Linux gap is now closed materially: a Windows-only implementation would no longer pass the T8 gate because `_linux_release_smoke` now executes observe/orient/drill/mutation/state/update/removal under WSL/Linux.
- The previous sealed target-breadth gap is now closed materially: removing the T8 target-breadth test is rejected by the T8 discrimination check.
- The previous sealed MCP error gap is now closed materially for missing required arguments: the sealed MCP mutation walk now asserts a `-32602` error with truthful content.

## Closure Review Pass

The live repository is not yet strong enough to justify operator approval, T8 PARKED disposition, P8 credit, Product STOP, or public testing based on Product STOP. The candidate is close, but the two REQUIRED findings correspond to declared T8/P8 closure sentences and have plausible wrong implementations that would pass the current tests.

## Residual Risk

- Compatible update failure atomicity is still prototype-thin; this is acceptable for T8 if actual payload replacement plus state preservation are witnessed, but should be called out to testers.
- The sealed release can be behaviorally valid while public repository distribution remains confusing until the default branch/archive/topology issue is resolved.
- The release artifact does not contain a consumer quickstart; public testers will need operator-provided instructions unless README is revised in a later authorized prep step.

## Suggested Operator Action

Return T8 to VERIFYING for two bounded witness repairs only: prove update performs actual installed payload replacement while preserving state, and prove MCP adapter removal through the sealed installed artifact. After repair, rerun focused T8 tests, canonical pytest, Ruff, `git diff --check`, the T8 gate, and cumulative T7/T6/T5/T4/T3/T2/T1/T0 receipts before resubmitting AWAITING_APPROVAL. Separately, before inviting broad public testers, decide repository publication/default-branch handling and provide a short consumer quickstart.
