# 0036 — T7 Parked

- **Date:** 2026-08-19
- **Tranche:** T7 — Shared Project Awareness Prototype
- **Status:** **PARKED** (BCC §2.8 step 13). Operator approval granted on the Windows
  certification record.
- **Record:** `_docs/certification/runs/20260818-152839-windows-c58b77b-t07-park.json`

---

## 1. The certification

Windows, the zero-skip authority, on commit `c58b77b`, clean tree, 314 seconds.

```text
VERDICT  PASS
lint     clean
suite    86 tests, 1 skipped, 0 failures, 0 errors
gates    210/210 assertions
           t00_foundation        25/25      t04_cancellation      12/12
           t01_ship_manifest     23/23      t05_ownership_model   52/52
           t02_ledger_presence   18/18      t06_instance_identity 27/27
           t03_live_channel      13/13      t07_shared_awareness  40/40
discovery PASS
```

**One skip**, against seven on Linux — which is the whole reason Windows is the
authority. The §7 gap named in 0035 is closed: this is the exact final behavioural
commit, certified on both platforms.

T7's stop condition is met in full. Every clause in 0035 §5 now has a Windows record
behind it, not an inference.

---

## 2. The second run, and why it failed

Two records exist. The second says `VERDICT: FAIL`, and the failure was **mine, in the
certification script, not in the product**:

```text
t00_foundation  24/25   FAIL: working tree is clean
```

`certify.py` writes its record **into the tree it certifies**. The first run's record
was still uncommitted when the second ran, so `t00`'s clean-tree assertion saw the
certifier's own leftovers and failed. Every other assertion in that run was green,
including all 40 of t07.

A tool that cannot be run twice in a row without failing on its own output is broken,
so two repairs:

**It now refuses a dirty tree**, naming what is dirty, before doing any work. The
sequencing is explicit: commit → certify → commit the record → push. `--allow-dirty`
overrides and is recorded in the JSON, so an overridden run cannot be mistaken for a
clean one.

**Not** fixed by excluding `_docs/certification/` from `t00`. Blinding a census so it
stops seeing a surface is the defect this project has now recorded three times — the
harness vanishing from the identity census, the T7 gate tripping t06, and this. The
assertion is correct; the sequencing was wrong.

### And a second, quieter defect in the same script

The discovery step recorded `"scores": {}` — `ok: true` with nothing to read. The
harness writes `score`; the script looked for `scores` or `summary` and found neither,
so **a guessed key silently produced a substanceless record.** A passing step that
carries no evidence of passing is the same family as everything else this tranche
found. Corrected, and the record now also carries the precept, enforcement and lineage
axes directly.

Neither defect affects the T7 verdict: the first record was produced on a clean tree
with the discovery pass exiting 0.

---

## 3. What T7 delivered

One shared module and two call sites. No awareness engine, no database, no schema
framework, no private orchestration.

| | |
| --- | --- |
| **reduction** | 133,477 B of contributor evidence → **2,343 B** projection on a real 254-file target (ratio 0.018) |
| **revision identity** | content-anchored; stable across re-observation, restart and **relocation**; returns to an earlier value when the target does |
| **handles** | every promoted identifier carries its owning tool and resolves through it |
| **drill-down** | recovers the evidence *actually used* for that revision — never a rerun |
| **freshness** | projected at read time, so a stale re-engagement says so |
| **records** | write-once; `revision X → evidence X` is permanent |
| **degradation** | software, records and empty targets all produce truthful envelopes |

Full account in 0035, including the seven defects — five of them in the verifier — and
the **five mutations that escaped** before being closed. Every one had the same shape:
an assertion satisfied by reading back a stored value, or a fixture that could not tell
two implementations apart. That pattern is the most durable thing this tranche
produced, and the second certification run was its fifth instance.

---

## 4. Carried

- E8 and E11 remain **NOT MET**; T7 advanced no lifecycle row.
- `patch` declares `writes: toolkit` while writing to a target path — **T8 owns it**,
  and the governed work loop is not safe until it closes.
- Governance fails open, audibly. The declared safe posture before STOP: a broken
  configuration may keep permitting **Observe** but must not silently grant **Apply**.
- `report` returns `modules` and `markdown` — the same information twice, ~30.5 KB
  against ~14.8 KB before. The cost of honouring a contract, not a defect.
- The canonical payload assembler remains deferred to release certification.

---

## 5. Next

**T8 — Governed Work Loop Prototype**, gate-first, declared before any implementation.

It begins from a concrete object rather than a question:

```text
revision X + evidence X  ->  canonical handle  ->  impact  ->  preview  ->  diff
   ->  approval  ->  Apply  ->  changed paths  ->  target-native verify
   ->  awareness stale  ->  refresh  ->  revision Y + evidence Y
```

Because evidence is captured at observation time and revision records are immutable,
attribution across that loop is a comparison of two fixed records rather than an
inference.

Then the two closure gates — **parity** and **release** — and STOP.
