# Archive — Pre-Reset, 2026-08-06

This holds the project's history up to the point it was unified and reset.

**Nothing here is authority.** It is evidence. The live authority is
`.bcc/CHARTER.md`, `.bcc/TRANCHE_PROTOCOL.md`, `.bcc/TRANCHE_PLAN.md` and
`.bcc/BUILDER-CONSTRAINT-CONTRACT.md`.

---

## Why the reset

The project was assembled from parts belonging to several predecessor projects
whose histories do not share a chronology. That left multiple competing
authorities in one tree: two BCCs, several project plans, at least three tranche
numbering systems, and completion claims describing codebases that are not this
one.

The failure mode was demonstrated rather than theorised. An implementing agent
read an inherited contract header — *"backend implemented; GUI wiring pending"* —
and had to reason explicitly about whether it applied here. It did not. A second
agent might not have stopped to ask.

So: one authority, one numbering starting at T0, one journal starting at 0001.

---

## Contents

| Path | What it is |
| --- | --- |
| `superseded-bcc-docs/` | Seven control documents written 2026-08-05 under a since-retired model. They specified a *second* application with the toolkit behind a bridge. That model was withdrawn. |
| `journal/` | Journal entries 0001–0002 of the pre-reset effort. |
| `factory-design/_design/` | The toolkit's own design authority: charter, plan, capability gaps, completion plan, dirty ledger, scrub audit. Its live doctrine — the precept — is carried forward into `CHARTER.md` §1.2. |
| `projectmapper-original-era/` | A complete competing plan set: a 473-line PROJECT_PLAN covering Tranches 0–8, its own CURRENT_STATE, a superseded BCC, and eight journal entries. |
| `harness-runs-summary.md` | What the 58 recorded harness runs established, before they were cleared. |
| `toolkit-header-provenance.md` / `.json` | `STATUS:` and `TRANCHE:` values for 136 toolkit source files, captured before those fields were stripped. 64 distinct tranche identifiers. |

## What was removed rather than archived

Moved to `_trash/` for operator deletion:

- **The governing blueprint PDF.** It specified a second application built
  alongside the toolkit. Retired as authority; its capability detail lives on in
  the twelve tool contracts, which remain in `_PLANS/`.
- **`_LoRA_TRAIN`.** Operator decision, 2026-08-06 — a Tkinter shell over an
  external conda training environment, outside the sidecar's weight class.
- **A stale installed sidecar** found inside the daily-driver tree, declaring
  `VERSION 1.1.0` while carrying 78 tools against the canonical 95.
- **Prior toolkit memory**: event log, journal, LLM usage records, harness runs,
  regenerable scaffold targets, caches.
- **The pre-reset git history**: three commits.

## What was deliberately kept

- **`.bcc/evidence/`** — the 2026-07-18 measurement of the sidecar against the
  real daily-driver tree: 143 events, 124 ok / 19 failed, 79 distinct tools. The
  only measurement against real tools, and irreplaceable.
- **`_PLANS/`** — the twelve capability contracts. Requirements, not history.
- **`_PARTS-FOR-PLANS/`** — the original applications.
- **`_harness/`** — a working instrument, not a record.
- **`_harness/targets/_UsefulHelperSCRIPTS/`** — the daily drivers.

---

## Lifetime

This archive is committed to git. When the parts bin is deleted at charter
condition E9, the archive goes with the folder but survives in version history.

Deliberate: the history is scaffolding for the transition. Once the project
stands on its own it is not needed on disk, only recoverable.
