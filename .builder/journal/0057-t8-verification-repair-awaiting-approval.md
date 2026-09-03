# 0057 - T8 Verification Repair Awaiting Approval

Date: 2026-09-03

Status: AWAITING_APPROVAL

## Operator Return

Entry `0056-t8-verification-return.md` returned T8 to VERIFYING for three bounded
Reviewer witness repairs only:

1. strengthen the same-artifact Linux acceptance walk;
2. prove sealed CLI orientation/drill behavior across empty, software, and mixed/document
   targets;
3. add a sealed-install MCP behavioral error/refusal witness.

This repair did not reopen T0-T7, broaden T8, park T8, credit P8, or claim Product STOP.

## What Changed

- Strengthened `tests/test_t8_release_stop.py` with sealed CLI witnesses for empty,
  software, and mixed/document targets through attach, substrate refresh, awareness
  refresh/current, and awareness drill.
- Strengthened the sealed MCP mutation walk with a malformed `mutation.preview_write`
  JSON-RPC request that must return a behavioral `-32602` error rather than silently
  succeeding.
- Expanded `.builder/gates/t8_release_stop.py` so the same sealed artifact completes the
  Linux mini acceptance walk: attach, status, substrate refresh, awareness
  refresh/current, drill, governed mutation, durable receipt/history checks, update, and
  uninstall.
- Repaired T8/T0 gate hygiene discovered during verification: T8 gate scratch builds now
  use non-repository temp space, certification factory subprocesses run bytecode-free,
  release entry points avoid bytecode debris where possible, and the T0 gate recognizes
  valid T8 lifecycle map headings.
- Repaired the sealed update path to copy staged payload directories into place after
  backing up existing payloads, preserving compatible update semantics while avoiding
  Windows rename/replace denial seen during T8 verification.

## Preserved Failed Evidence

The following failed receipts remain historical discovery evidence and are not treated as
the authoritative passing T8 submission:

- `T8/20260903T090817Z-52c6adb4/t8-gate.json` and
  `T8/20260903T090957Z-d6f344da/t8-gate.json`: repository-owned scratch directories
  became inaccessible during cleanup.
- `T8/20260903T091254Z-71396b71/t8-gate.json`: sealed update hit a Windows
  directory-replacement denial.
- `T8/20260903T091744Z-ca29e231/t8-gate.json` and
  `T8/20260903T130242Z-628cb9bd/t8-gate.json`: certification subprocesses left bytecode
  debris.
- `T8/20260903T130701Z-925b91ed/t8-gate.json`: canonical regression still created
  `factory/__pycache__` before the final certification-harness patch.
- `T7/20260903T131428Z-30577366/t6-gate.json` and
  `T5/20260903T131431Z-eebaf0ed/t5-gate.json`: cumulative gates were mistakenly run in
  parallel against shared `tests/.runtime`; serial reruns passed.
- `T0/20260903T090256Z-875b389b/bootstrap-gate.json`: T0 vocabulary did not yet
  recognize T8 lifecycle map headings; the repaired T0 rerun passed.

## Verification Evidence

- Focused T8 product tests: `python -B -m pytest tests\test_t8_release_stop.py -q`
  passed 4/4.
- Canonical product regression: `python -B -m pytest -q` passed 76/76.
- Static check: `python -B -m ruff check . --no-cache` passed.
- Whitespace check: `git diff --check` passed.
- T8 gate `20260903T131126Z-a9773084` passed 11/11.
- T8 receipt:
  `.builder/evidence/T8/20260903T131126Z-a9773084/t8-gate.json`
  SHA-256 `8DA9BBE13266E0223F85A536876FE2679406E34074806CC8FCC48A0625BD1E99`.
- Sealed artifact:
  `.builder/evidence/T8/20260903T131126Z-a9773084/release/sidecar-workbench-0.1.0.zip`
  SHA-256 `CF8C8BE09A2597A5812AD2433027E1EF88E221B4B0A8369303717E4D5EC12A6E`.

## Cumulative Gate Evidence

- T7 `20260903T131259Z-3aee7847`, 15/15,
  SHA-256 `CECD92FF394A96277CAEC70D52A210CECD1D65EAA6CA4C78D7D0F6DF30737F53`.
- T6 `20260903T131621Z-683d1155`, 11/11,
  SHA-256 `3B4299D78F85104B0856735AA700D6757D58F4DECEADE1019E4951BFC80A3645`.
- T5 `20260903T131740Z-9830e735`, 13/13,
  SHA-256 `7AF3DE3986370107A9B1BCD86CEB14F15DAF66B7758199A64CA039C45D852218`.
- T4 `20260903T131443Z-97157605`, 14/14,
  SHA-256 `CA879415411E2E3C72F1F0E74B317A01700F4264D0E89DF53078905836D10C97`.
- T3 `20260903T131856Z-a4b6c2c8`, 12/12,
  SHA-256 `F6EF34535568B844E43406D38B6E2055C508E995A9EC679F29D0D2DD1389E244`.
- T2 `20260903T132015Z-5e7ef08b`, 13/13,
  SHA-256 `A7EAEC3DC816E10C4F7EF019696012AB3363D214EF11C404E1C3E84B44D2455D`.
- T1 `20260903T132032Z-617c1918`, 9/9,
  SHA-256 `71C0218EB64F9731D572DB2F78F77EAE1CD5E39E8CC217E4B21926692ECB85E5`.
- T0 `20260903T132142Z-9e4ddd44`, 13/13,
  SHA-256 `DA64A26DD6536A7E4CFB89974F42EB0208CC54D779B948D38C8C25E04DEE14CB`.

## Review Position

T8 is resubmitted for Reviewer/operator assessment at AWAITING_APPROVAL. The Builder does
not park T8, credit P8, claim Product STOP, or close the project. If approved, the next
action is the normal T8 park and Product STOP credit closeout.
