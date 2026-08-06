# ProjectMapper Slice Migration Marker

Status: migrated to root scaffold as source slice; retained for historical comparison

The active project is `.useful-helpers`, not `.project-mapper`.

Copied into root during Root Tranche 1:

- `.project-mapper/src/core/*.py` -> `src/useful_helpers/core/`
- `.project-mapper/tests/test_core_*.py` -> `tests/`

Current root authority:

- `../BCC.md`
- `../_docs/CURRENT_STATE.md`
- `../_docs/PROJECT_PLAN.md`
- `../_journal/`

Do not add new implementation work here unless a later tranche explicitly uses
this folder as a temporary comparison source. New runtime work belongs under
`../src/useful_helpers/`.
