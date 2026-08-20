# 0040 — T8 Parked

- **Date:** 2026-08-20
- **Tranche:** T8 — Governed Work Loop Prototype
- **Status:** **PARKED** at certified commit `445a68c`, on operator approval.
- **Certification:** `20260820-015043-windows-445a68c.json` — PASS, clean tree, 427.8s.

---

## 1. What is now true

> A human or agent moves from **awareness → impact → preview → diff → approval → Apply
> → measured change → verification → refreshed awareness**, composed entirely from
> existing tools and the existing seam.

```text
gates      262/262   ZERO SKIPPED   (t08: 52/52)
suite      87 tests, 1 skipped
lint       clean
discovery  12 tools exercised, no failed axes
             precept pass | front_door pass | enforcement pass | cleanliness pass
```

Three safety preconditions closed and mutation-tested. No new diff, approval,
verification or runner subsystem. No new application. `apps/` untouched.

---

## 2. The distinction that survives this tranche

**Absence has four shapes, not three.** T8 found the first three; the operator supplied
the fourth, and it is the one that would have caused the next false green.

| shape | correct treatment | example |
| --- | --- | --- |
| **not asked for** | proceed | no witness sent, no governance file, no ceiling declared |
| **asked and failed** | refuse | witness mismatch, unreadable config, `pass: false` |
| **not applicable** | report, do not judge | composition on a target with no subsystems |
| **applicable but unmeasured — no oracle** | report as **unscored**, and *do not let it satisfy coverage* | truthfulness on an adopted real target |

The fourth is not a variant of the third. *Truthfulness absolutely matters on `_theCELL`* —
we simply cannot compute a false-positive rate there without independently establishing
what is true and false. Reporting that as "N/A" would claim the property is irrelevant
when it is only unmeasured.

This tranche already made the opposite mistake twice in one day, in both directions:
absence read as a pass hid a nine-day-dead acceptance walk, and absence read as a failure
accused a run that had done exactly what it should. The fourth shape is where the next one
would have come from.

---

## 3. The discovery that came *after* the certifier became trustworthy

The acceptance-walk coverage problem is the right kind of finding: it only became visible
because the instrument was finally honest. It is recorded as a condition on prototype
closure and is **not** a reason to reopen T8 — T8's declared outcome is certified, and
nothing about it depends on whether the harness has oracles.

**T8 is not reopened unless the acceptance walk demonstrates a regression in T8's own
behaviour.**

---

## 4. Carried forward

| item | owner |
| --- | --- |
| 26 Apply tools declare no `writes` field | bounded manifest-truth pass |
| `tool_health` reports a rate with no threshold | acceptance walk |
| composition / truthfulness need oracle fixtures | **acceptance walk — condition recorded** |
| ProjectMapper: manifest not self-reproducing; dot-folder pruning | parity closure gate |

---

## 5. Next

Closure, not construction:

1. **Parity certification** — every donor contract classified Retained-direct,
   Retained-composed or Superseded, with a fixture through the current runtime for every
   retained row. *"Deferred" is not one of the three outcomes.*
2. **Release certification** — clean clone, release artifact, clean machine, no
   development repository.
3. **Acceptance walk** — three real C4 targets **plus two oracle controls**, under the
   coverage rule recorded in the Plan.
