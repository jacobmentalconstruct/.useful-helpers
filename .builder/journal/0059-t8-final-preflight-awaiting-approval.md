# 0059 - T8 Final Preflight Awaiting Approval

Date: 2026-09-03

Status: AWAITING_APPROVAL

## Declared Outcome Under Review

T8 remains the Release and STOP tranche declared in `0053-t8-release-stop-declaration.md`.
Entry `0058-t8-final-preflight-return.md` returned the `0057` candidate to VERIFYING for
two bounded final preflight witness repairs based on Reviewer evidence
`.builder/evidence/reviews/T8/20260903T134140Z-external-review.md`.

## What Changed

- Added a sealed-artifact update witness that intentionally corrupts an installed
  runtime payload file and adds an extra installed payload marker, runs `factory update`
  from the sealed release payload, and proves the installed payload bytes are restored,
  the extra marker is removed, the instance UUID remains stable, and App Journal state
  survives.
- Added a sealed-artifact MCP-removal witness that removes `.sidecar/core/mcp.py`, proves
  CLI `status`, tool discovery, and a mechanical `read_file` call still work, and proves
  `sidecar mcp` fails truthfully with `mcp_unavailable`.
- Strengthened the T8 gate discrimination witness so tests omitting actual payload
  replacement or sealed MCP removability are rejected.

## Scope Discipline

This repair did not broaden T8 beyond final preflight/release evidence. It did not add a
GUI, local AI, embeddings, domain cartridges, cloud service, workflow engine, rollback
system, public repository publication workflow, or consumer quickstart requirement. The
Reviewer's public-distribution topology and README quickstart notes remain advisory
release-readiness items unless the operator explicitly amends scope.

## Verification Evidence

- Focused T8 product tests: `python -B -m pytest tests\test_t8_release_stop.py -q`
  passed 6/6.
- Canonical product regression: `python -B -m pytest -q` passed 78/78.
- Static check: `python -B -m ruff check . --no-cache` passed.
- Whitespace check: `git diff --check` passed.
- T8 gate `20260903T135132Z-5f6595f9` passed 11/11.
- T8 receipt:
  `.builder/evidence/T8/20260903T135132Z-5f6595f9/t8-gate.json`
  SHA-256 `4964E06BC9BE4551F07B367932C790F522BA91DF85B483A5BA3146342765DFAD`.
- Sealed artifact:
  `.builder/evidence/T8/20260903T135132Z-5f6595f9/release/sidecar-workbench-0.1.0.zip`
  SHA-256 `EE5021C92D3E11093B7D9EDCEC3A7DF2D59CAD008ABAB2E3CC96B072743328A5`.

## Cumulative Gate Evidence

- T7 `20260903T135304Z-ad81dabe`, 15/15,
  SHA-256 `1E4936A8ECC5E28030541EFD99C9DD6493FE9E00102AEFE351B2288EE451ECEE`.
- T6 `20260903T135424Z-cf362fc0`, 11/11,
  SHA-256 `A20C3CD30BE3BF4D640F616AFEF9BA877B8476ACF6BBCF926E79009304FE77E9`.
- T5 `20260903T135549Z-cc196764`, 13/13,
  SHA-256 `87FA63712A25985FB226FAA44276C0674711D271CFF99D77F7337D505FD74ADB`.
- T4 `20260903T135724Z-2b49cfd0`, 14/14,
  SHA-256 `5C9F2C0256495A455B4140220B657FB7A956E6EDD6DAE882CC7A9C98CF3B9C7A`.
- T3 `20260903T135842Z-66427761`, 12/12,
  SHA-256 `F2A61EF360A4290B04B20575D0536E90661D0EBDC9C69CC207B51E8EC8EA6108`.
- T2 `20260903T140005Z-7e2d9fb1`, 13/13,
  SHA-256 `426AA3A7A66F9C18F5CE6E178EBB06CFA2EEE0B2C676ACD21392BA027088B1F1`.
- T1 `20260903T140022Z-7dee7dc7`, 9/9,
  SHA-256 `DFCDF014506255C12194DEC4723BE179D4028DB86FE5823B152E1BC6C322833B`.
- T0 `20260903T140135Z-cd3cf0bb`, 13/13,
  SHA-256 `07D3BDA3699CC4AD454595DEF1F60881534340D18799E60890E1AF6B0C37BF07`.

## Review Position

T8 is resubmitted for Reviewer/operator assessment at AWAITING_APPROVAL. The Builder does
not park T8, credit P8, claim Product STOP, or close the project. If approved, the next
action is the normal T8 park and Product STOP credit closeout.
