# Certification

One command that certifies a tranche and writes a **machine-readable verdict**.

```bat
python _docs\certification\certify.py --label t07-park
```

Takes a few minutes — `t06` and `t07` install real instances and exercise them. Then:

```bat
git add _docs/certification/runs
git commit -m "cert: <platform> <label>"
git push
```

That file is the whole certification record. Nothing else needs to be pasted or read.

## Why it exists

Certification used to be a list of commands typed into a terminal, returning thousands
of lines of console text that had to be read by eye. That is expensive, easy to misread,
and **twice a verdict was reported from a partial scroll**. The output here is one JSON
file with a top-level `verdict`, per-step results, and per-gate assertion counts
including the exact text of any failure.

## Where the numbers come from

Structured where possible; parsed only where necessary.

| step | how |
| --- | --- |
| **gates** | **imported.** `gates/run.py` exposes `_load` and `Result`, so assertion rows are collected directly. No text scraping at all |
| **discovery** | the harness already writes `run.json` per run — read, not parsed |
| **suite** | `unittest`'s tail is parsed, because it is a stable documented format and the suite is a subprocess by design |
| **lint** | exit code plus its one-line summary |

## It never lies by omission

A step that could not run is recorded as `"ok": false` **with a reason** — never skipped
silently, never absent from the record. `--skip-discovery` is recorded as
`"skipped": true` and does **not** count toward a pass. An absent result and a passing
result must not look alike; this project has been bitten by that often enough to make it
a rule.

`--only t07` narrows to one gate for re-running a single red result. The narrowing is
recorded as `narrowed_to`, so a partial run cannot later be mistaken for a full
certification.

## Reading a record

```jsonc
{
  "verdict": "PASS",              // the only field most reads need
  "commit": "129b0b3",
  "dirty": false,                 // true means the tree did not match the commit
  "platform": { "system": "Windows", "python": "3.13.1" },
  "steps": {
    "lint":  { "ok": true },
    "suite": { "ok": true, "tests": 86, "skipped": 1, "failed_tests": [] },
    "gates": { "ok": true, "total_passed": 190, "total_assertions": 190,
               "gates": [ { "id": "t07_shared_awareness", "verdict": "PASS",
                            "passed": 40, "failed": 0,
                            "failures": [],      // exact assertion text when red
                            "partial": [] } ] }, // declared partial coverage
    "discovery": { "ok": true, "scores": { } }
  }
}
```

**`dirty: true` matters.** It means the working tree did not match the commit the record
names, so the record certifies something that is not in git. Commit first, then certify.

## Platform expectations

Windows is the **zero-skip authority** and has twice caught defects no Linux run could
see. Linux skips ~7 tests (`tkinter`, `ollama` absent) and its mount denies `unlink`, so
a handful of tests fail there for reasons that have nothing to do with the product —
recorded in Charter §7.5. **A tranche parks on a Windows record.**

## Where records live

`_docs/certification/runs/<timestamp>-<platform>-<commit>[-<label>].json`

`_docs/` is builder-control documentation and is `NEVER_SHIP`, so nothing here can reach
a payload. The records are committed on purpose: a certification nobody can retrieve is
a certification that did not happen.
