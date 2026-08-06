# Harness Runs — summary before reset

58 runs recorded in `_harness/runs/`, archived and cleared 2026-08-06.

## By date

| Date | Runs |
| --- | --- |
| 20260719 | 25 |
| 20260720 | 21 |
| 20260721 | 2 |
| 20260724 | 6 |
| 20260725 | 4 |

## By dimension / target

| Target | Runs |
| --- | --- |
| `seam` | 20 |
| `s-python-app` | 13 |
| `s-composite` | 8 |
| `s-data-curation` | 5 |
| `s-records-research` | 5 |
| `s-workspace` | 4 |
| `s-web-app` | 3 |

## What these established

- Exercised only synthetic scaffolds (`s-*`) and the `seam` dimension.
- **No run targeted `_UsefulHelperSCRIPTS`**, the real daily-driver tree.
- The real-target measurement is separate and preserved in `.bcc/evidence/`:
  143 events, 124 ok / 19 failed, 79 distinct tools, 2026-07-18.

Scaffolds are regenerable via `harness.py scaffold <name> --kind <kind>`.
