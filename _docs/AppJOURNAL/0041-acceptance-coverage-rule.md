# 0041 — The Acceptance Coverage Rule, Mutation-Tested

- **Date:** 2026-08-20
- **Scope:** closure gate **C4a**. No product change. T8 remains parked at `445a68c`.
- **Artifact:** `_docs/certification/acceptance.py`

---

## 1. Five states, and none of them collapses into PASS

| state | meaning |
| --- | --- |
| `PASS` | measured, and it met the bar |
| `FAIL` | measured, and it did not |
| `N/A` | the property genuinely does not apply here |
| `NO-ORACLE` | applicable and **relevant**, but unmeasurable here — nothing establishes the right answer |
| `NO-THRESHOLD` | measured, but no acceptance bar has ever been declared |

The last two are the ones that get lost. `NO-ORACLE` is **not** `N/A`: truthfulness
matters enormously on a real adopted target — we simply cannot compute a false-positive
rate there without independently establishing what is true. `NO-THRESHOLD` is **not**
`PASS`: `tool_health` reports a rate nobody ever set a bar for, and a number without a bar
is not a verdict.

`NOT_EVIDENCE` is declared as a named set rather than tested ad hoc, so that adding a
sixth state cannot silently start counting as green.

---

## 2. The two oracle controls were run, not assumed

Both existing scaffolds were scaffolded and executed. **Real records, not constructed
shapes** — the distinction this project has been burned by before.

```text
oracle-composite   COMPOSITION  composite=True (expected True) -> True
                                subsystems 3/3 placed  src=top-level-dirs
oracle-python      TRUTHFULNESS false_positives=0 (naive 1, policy prevented 1) missed=0
```

The `oracle-python` line is the whole point: *naive produced 1 → policy prevented 1 →
faithful produced 0 → the genuine positive was still found.*

---

## 3. Mutation results

Every mutation was applied to a **real** record and re-scored.

| mutation | required | observed |
| --- | --- | --- |
| adopted target alone, `{}` ground truth | composition + truthfulness coverage FAIL | **both False** |
| `composite_correct → False` | composition coverage FAIL | FAIL |
| one subsystem misplaced (`mismatches` non-empty) | composition coverage FAIL | FAIL |
| `score.composition` dropped while an oracle is declared | composition coverage FAIL | FAIL |
| **`naive=0, prevented=0` with `fp=0`** | truthfulness coverage FAIL | FAIL |
| a true positive missed | truthfulness coverage FAIL | FAIL |
| a faithful false positive | truthfulness coverage FAIL | FAIL |
| bait planted but score nulled | truthfulness coverage FAIL | FAIL |

### The rule itself was mutated, not just its inputs

The discriminating clause is the one that could most easily have been decorative, so it
was removed and the hollow record re-scored:

```text
record: false_positives 0, naive 0, prevented 0, missed 0   ("found nothing at all")

WITH the discriminating clause : FAIL
WITHOUT it                     : PASS   <- a run that found NOTHING certifies as truthful
```

**`false_positives == 0` is also exactly what "nothing meaningful was exercised" looks
like.** A tool that finds nothing scores a perfect zero. The clause is what makes the easy
explanation impossible — the same discipline as T8's stale-preview interference preserving
the pattern's match count.

---

## 4. Two things the run surfaced that are not defects

**C4 coverage correctly fails today: 1 of 3 real targets.** Only `_theCELL` exists as an
adopted target; B (mixed records/documents) and C (empty/nascent) have not been adopted.
That is a true finding about the walk's readiness, not a fault in the rule.

**`tool_health` 12/14 on the composite oracle is two FIXTURE artefacts**, and this is why
the axis must not be handed a naive threshold:

- `git_inspect` — "not a git repository". A scaffold is not a git repo.
- `pdf_info` — "Stream has ended unexpectedly". The scaffold writes a **69-byte** PDF stub
  with no xref table. `pdf_info` refusing it is **correct behaviour**.

Had a bar been set at "100% of tools succeed", it would have been red for reasons with
nothing to do with the product. A threshold here needs to distinguish *the tool failed*
from *the fixture does not support that tool* — which is the `N/A` state again, one level
down.

---

## 5. Why this is a separate file from `certify.py`

`certify.py` certifies **one commit**: lint, suite, gates, one discovery pass. This
certifies the **acceptance walk** — several runs across several targets — and adds the one
thing a single record structurally cannot show: *whether an axis was ever measured at
all.*

Real targets prove usefulness under uncertainty; controlled targets prove correctness
where truth is knowable. Synthetic alone risks a product exquisitely adapted to its own
tests; real alone risks beautiful green reports where correctness was never measurable.
The rule requires both because neither substitutes for the other.
