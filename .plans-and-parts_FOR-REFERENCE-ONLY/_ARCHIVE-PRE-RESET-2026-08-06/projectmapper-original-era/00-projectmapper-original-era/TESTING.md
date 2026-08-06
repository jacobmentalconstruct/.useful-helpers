# Testing

Status: Core foundation tests active

Preferred test command:

```bat
python -m pytest -q
```

Tranche 0 contained only a minimal launch surface. Tranche 1 added audit and
architecture documentation only. The core foundation repair added the first
owned behavior tests for file info, exclusions, selection, and scanner logic.

## Early Test Candidates

Add tests as soon as the corresponding behavior is re-homed into owned modules:

| Behavior | Target module | Suggested assertions |
| --- | --- | --- |
| Display size formatting | `src/core/file_info.py` | bytes, KB, MB, GB thresholds |
| Path relation helpers | `src/core/file_info.py` | relative POSIX output; outside-root fallback |
| Text/binary classification | `src/core/file_info.py` | forced binary extensions, null-byte files, oversize files, UTF-8 decode failure |
| Exclusion policy | `src/core/exclusions.py` | default folder skips, filename globs, `.gitignore` dir/file/path patterns, dynamic patterns |
| Project scanning | `src/core/scanner.py` | traversal order, parent paths, skipped path records, cancellation path |
| Selection model | `src/core/selection.py` | click-independent inclusion state, recursive folder toggles, selected working-set generation |
| Folder/file inspection | `src/core/inspection.py` | folder metadata listing, text preview, unsupported/binary status |
| SQLite schema | `src/storage/schema.py` | required tables and indexes exist |
| Snapshot storage | `src/storage/snapshot_store.py` | inserts, row counts, output readback, skipped/error records |
| Markdown exports | `src/core/exports/markdown.py` | tree output, filedump output, combined output ordering |

## Manual Smoke Checks Later

Once UI behavior exists, smoke checks should cover:

- launch app,
- choose project root,
- browse left tree,
- click folder and inspect right-pane listing,
- click text file and inspect preview,
- click binary/unsupported file and inspect metadata status,
- check/toggle multiple files/folders,
- run mapper operation from top menu,
- verify generated output location.

## Current Test State

`python -m pytest -q` currently passes the core foundation tests. Latest repair
verification: `8 passed`.

The next test gap is UI smoke coverage once Tranche 2 introduces the explorer
shell.