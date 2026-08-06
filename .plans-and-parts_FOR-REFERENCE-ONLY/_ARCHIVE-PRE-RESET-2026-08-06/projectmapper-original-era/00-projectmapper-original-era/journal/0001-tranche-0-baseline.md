# 0001 - Tranche 0 Baseline

Date: 2026-08-02

Status: closed

## Scope

Establish `.project-mapper` as the self-contained project root and install the
contract, plan, scaffold, documentation, and journal baseline required before
feature work begins.

## Contract Authority

The governing contract is `_docs/BCC.md`, copied from
`../artifacts/BCC.md` during setup.

## Completed

- Created `.project-mapper` project root.
- Created baseline scaffold for `src`, `src/ui`, `src/core`, `src/storage`,
  `tests`, `assets`, `config`, `scripts`, and `_docs`.
- Installed project-local BCC copy.
- Installed project plan at `_docs/PROJECT_PLAN.md`.
- Created baseline architecture, provenance, testing, README, run, setup, and
  ignore files.

## Decisions

- The parts-bin applications are reference sources only.
- Runtime application code must live inside `.project-mapper`.
- Tranche 0 remains setup-only. Explorer, mapper, patcher, line-numberizer,
  and git workflow behavior are out of scope until later tranches.
- The first runtime surface is a minimal launch placeholder, not a feature
  implementation.

## Files Changed

- `.project-mapper/README.md`
- `.project-mapper/LICENSE.md`
- `.project-mapper/requirements.txt`
- `.project-mapper/run.bat`
- `.project-mapper/setup_env.bat`
- `.project-mapper/.gitignore`
- `.project-mapper/src/app.py`
- `.project-mapper/src/__init__.py`
- `.project-mapper/src/ui/__init__.py`
- `.project-mapper/src/core/__init__.py`
- `.project-mapper/src/storage/__init__.py`
- `.project-mapper/_docs/BCC.md`
- `.project-mapper/_docs/PROJECT_PLAN.md`
- `.project-mapper/_docs/ARCHITECTURE.md`
- `.project-mapper/_docs/SOURCE_PROVENANCE.md`
- `.project-mapper/_docs/TESTING.md`
- `.project-mapper/_docs/_AppJOURNAL/0001-tranche-0-baseline.md`

## Verification

- Inspected scaffold tree under `.project-mapper`.
- Ran `python src\app.py`.
  - Result: launched the Tranche 0 placeholder successfully.
- Ran `python -m pytest -q`.
  - Result: pytest ran, but no tests were discovered.
  - Residual risk: expected for Tranche 0; behavior tests begin when Tranche 1
    and later tranches introduce owned logic.

## Risks

- No feature behavior has been migrated yet.
- Existing ProjectMapper behavior still lives only in the reference source.

## Next Action

Begin Tranche 1: reference audit and architecture map.
