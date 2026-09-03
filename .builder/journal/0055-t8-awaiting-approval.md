# 0055 - T8 Release and STOP Awaiting Approval

Date: 2026-09-03

Status: AWAITING_APPROVAL

## Declared Outcome

Entry `0053-t8-release-stop-declaration.md` declared one positive-composed sealed
release artifact that can be installed and used from clean Windows and Linux
environments, proves compatible update and clean removal behavior, preserves
lower-layer dependency direction, excludes construction history and transient state, and
completes the Product STOP evidence walk without beginning a new product layer. Entry
`0054-t8-execution-start.md` records same-turn operator approval to implement.

## What Changed

- Added `factory/release.py`, a packaging-neutral sealed zip builder that positively
  selects `product/`, `factory/`, `README.md`, and `pyproject.toml`, writes
  `RELEASE_MANIFEST.json`, and emits an outer manifest with artifact SHA-256.
- Extended `factory/cli.py` with `release build`, `release inspect`, `update`, and
  `uninstall`.
- Extended `factory/installer.py` with compatible runtime-payload update and clean
  `.sidecar` removal while preserving target-owned work products.
- Extended `product/core/mcp.py` so MCP exposes `mutation.preview_write`,
  `mutation.approve`, and `mutation.apply` through the existing `mutation.py` owner.
- Added `tests/test_t8_release_stop.py` for sealed artifact boundary, blank-state
  install, relocation, compatible update, removal, and sealed CLI/MCP governed mutation.
- Added `.builder/gates/t8_release_stop.py` as the authoritative T8 gate.

## Scope Discipline

T8 did not introduce a GUI, autonomous agent, local AI, embeddings, vector authority,
domain cartridges, plugin marketplace, workflow engine, rollback system, cloud service,
global registry, standalone Tool Pack, standalone App Journal distribution, or Coherent
Development product. The release format is a zip source artifact chosen only as the
smallest packaging-neutral sealed artifact sufficient for the prototype.

## Evidence

- T8 gate `20260903T073452Z-5680a19f` passed 11/11 from commit
  `bb6f58569be40aaa53c9febe224b2e811031fad4`.
- T8 receipt:
  `.builder/evidence/T8/20260903T073452Z-5680a19f/t8-gate.json`
  SHA-256 `E7B7D56D2DFB6497868717263B82B88EA497E869B3EEB735FC7AEEDEF2D59F8B`.
- Sealed artifact:
  `.builder/evidence/T8/20260903T073452Z-5680a19f/release/sidecar-workbench-0.1.0.zip`
  SHA-256 `5AB81C3F6DCCB996E4A847100EA74F272ECF748581828C03BA0FAE9B34907A90`.
- The gate proves positive artifact boundary, focused T8 product behavior, Windows
  lifecycle, same-artifact WSL/Linux smoke, MCP governed mutation parity,
  dependency-direction preservation, canonical regression, static discovery,
  discrimination witnesses, and repository hygiene.

## Cumulative Gate Evidence

- T7 `20260903T073655Z-cad93a0b`, 15/15,
  SHA-256 `37E40803BE4D9D5330DF67C161ECF949F96EE3844E37242C457878CD62EEFCC6`.
- T6 `20260903T073830Z-5cef823d`, 11/11,
  SHA-256 `B5E37B9CE305604A431767F6E92CF3263D54489908C877F6C47D6F8695DC49E2`.
- T5 `20260903T074002Z-fc406e6e`, 13/13,
  SHA-256 `8815649669E5A8254EBCF0E85A0A449FEEDA4CE151867A5515EC9BD5BA2E84D2`.
- T4 `20260903T074147Z-59a44628`, 14/14,
  SHA-256 `87026A568BCC12EACF0A7B54FAE1ED2EC6FD7A7A588F3D22C00AD145721A4306`.
- T3 `20260903T074319Z-181874b2`, 12/12,
  SHA-256 `2EADADFF2002D6015BD6C26ADFC5BF7226BF00ED1E8FDA30CEEEC565B0B70B72`.
- T2 `20260903T074452Z-9c42d0f1`, 13/13,
  SHA-256 `9AF6C8E77915F2B771699B81119749C60988CB02671419C14A1CDCB8C7C364AC`.
- T1 `20260903T074512Z-238b28cd`, 9/9,
  SHA-256 `7BC5CEE8D62627F26CCF1C32ECFE976BA794CC9778035C38BC50631AA2326642`.
- T0 `20260903T074634Z-b7f6f5e3`, 13/13,
  SHA-256 `9BA9B14EBFB0EA0D028970149908CCF062743CAEDE12EC63BEBA2E05D1214703`.

## Review Position

T8 is submitted for operator/reviewer assessment. The Builder does not park T8, credit
P8, claim Product STOP, or close the project. If approved, the next action is a normal
T8 park/STOP-credit closeout entry and status synchronization.
