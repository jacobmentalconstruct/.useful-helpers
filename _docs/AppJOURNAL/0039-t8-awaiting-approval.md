# 0039 — T8 Stop Condition Met, **Awaiting Approval**

- **Date:** 2026-08-20
- **Tranche:** T8 — Governed Work Loop Prototype
- **Status:** **AWAITING-APPROVAL.** Every clause of the declared stop condition is met
  and evidenced. Parking is the operator's call, not the builder's.
- **Certification:** `20260820-015043-windows-445a68c.json` — **PASS**, clean tree.

---

## 1. The stop condition, clause by clause

0037 §9 declared six clauses. Each is checked against the certification record rather
than against memory.

| clause | evidence |
| --- | --- |
| the full loop completes on the software target | `t08_governed_loop` 52/52 |
| degrades truthfully on the records and empty targets | both report no verification rather than inventing one; both still produce an awareness revision |
| all three preconditions closed **and mutation-tested** | nine mutations, §8 of 0038 |
| `certify.py` reports **PASS on Windows** | `445a68c`, 427.8s, tree clean |
| the **zero-skip** authority holds | **262/262 gate assertions, 0 skipped**; suite 87 tests, 1 skipped |
| the discovery pass is clean | `precept`, `front_door`, `enforcement`, `cleanliness` **all pass**; **12 tools exercised** |
| the operator approves | **outstanding — this journal exists to ask** |

---

## 2. What the certification actually says now

```text
VERDICT   PASS      commit 445a68c   dirty False   427.8s
lint      ok
suite     ok        87 tests, 1 skipped
gates     262/262   0 skipped
discovery ok        12 tools exercised, no failed axes
            precept     pass
            front_door  pass   mode=mapped  domain=python-app  24 mounted
            enforcement pass   rejected AND detected_write
            cleanliness pass
```

**This is the first trustworthy green since 2026-08-18.** The three certifications before
it reported PASS while the discovery pass was not running at all.

---

## 3. Three things this tranche should be remembered for

### The verifier was wrong more often than the product

Eight defects in 0038 §6 were mine, in gates and in the certifier. The product defects
were found *by* those instruments only after the instruments were repaired. Every time
the count moved, the honest question was *"did the product improve, or did the verifier
learn to ask?"* — and once, it was the latter, recorded as such:

```text
30 baseline -> +7 product -> +1 VERIFIER REPAIR -> 38 -> 52/52
```

### A mutation fixture must reproduce the defect's causal sequence

My first attempt at proving the catalog-staleness fix corrupted the catalog's *content*,
which made it the newest file on disk — a state mtime cannot detect and never claimed to.
The mutation "failed" for a reason outside the mechanism's stated sensing ability, which
is not a finding about the mechanism.

### Absence has exactly three shapes, and conflating any two of them is a lie

This tranche hit all three, and got the last one wrong before getting it right:

| shape | correct treatment |
| --- | --- |
| **not asked for** | proceed — no witness sent, no config present, no ceiling declared |
| **asked and failed** | refuse — witness mismatch, unreadable config, `pass: false` |
| **not applicable / not measured** | *report, do not judge* — `changed_paths: null`, `composition` on an adopted target |

The certifier first treated shape 3 as shape 1 (absence looked like a pass, and hid a
discovery pass that had not run for nine days), and my fix then treated it as shape 2
(absence looked like a failure, and accused a run that had done exactly what it should).
**Neither reading was more honest than the other.** The rule that finally discriminated
was specific rather than sweeping: *fail on an explicit `pass: false`, or if no tools were
exercised* — `tool_health.ran` being 0 in every broken run and 12 in every good one.

---

## 4. Carried forward — recorded, not repaired

| item | why it is not T8's |
| --- | --- |
| **26 Apply tools declare no `writes` field** | only `patch` is on T8's Apply path; the rest are a bounded manifest-truth pass |
| **`tool_health` reports a rate with no threshold** | a measurement without a bar is not a verdict; setting the bar is a deliberate decision |
| **`composition` / `truthfulness` never run on adopted targets** | they need planted ground truth — **this one matters for C4** |
| **ProjectMapper: manifest not self-reproducing; unconditional dot-folder pruning** | parity closure gate; deferred deliberately, including the "small" half |

### The C4 item deserves the operator's attention before the acceptance walk

`composition` and `truthfulness` are computed **only** when a target carries a
`_ground_truth.json` declaring expectations. Adopted real targets have none. If all three
C4 acceptance targets are adopted, **two whole axes of the acceptance walk never
execute**, and the walk reports green while measuring less than it claims — the same
shape as the defect this tranche just spent a day removing from the certifier.

---

## 5. Where the plan stands

T2–T8 green. The prototype's twelve behavioural steps are covered by shipped, gated
capability. What remains before **Prototype STOP** is closure, not construction:

1. **Parity certification** — every donor contract classified Retained-direct,
   Retained-composed, or Superseded, with a fixture through the current runtime for
   every retained row. *"Deferred" is not one of the three outcomes.*
2. **Release certification** — a clean clone, a release artifact, a clean machine, no
   development repository.

Steps 13–15 moved in front of STOP on 2026-08-18 precisely so the prototype cannot be
declared done while saying *"we have not proven the old workflows produce their outputs."*

---

## 6. The ask

T8's outcome is achieved, its gate is adversarial and green, its stop condition is met in
every clause the builder can satisfy, and the acceptance walk that corroborates it is
running again and passing.

**Park T8, or name what is still missing.**
