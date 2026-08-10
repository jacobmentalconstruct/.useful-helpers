# 0016 — The Contract Is A Tool. Correcting 0015.

- **Date:** 2026-08-09
- **Tranche:** none — correction and alignment, at operator instruction
- **Corrects:** 0015 §2, whose stated justification was wrong.

---

## 1. The Correction

Entry 0015 justified amending the contract like this:

> `.bcc` is in **`NEVER_SHIP`**. The contract governs *this construction* and does
> not travel with the payload. Amending it changes nothing downstream.

**Both halves are wrong.** The operator's ruling:

> The BCC.md is not merely governing our workflow right now — it's a contract which
> is yet another tool in this side-car, useable by agent and user. It ships with the
> sidecar **if** the user or agent chooses to enable its inclusion at install. This
> prevents it taking over in cases where it is not needed for the target project.

So the contract is **opt-in payload**, not build-only artifact. The amendments made
in 0015 are therefore shipped text, and had to be re-read as such.

Prior entries are not rewritten (protocol §6). 0015's *changes* stand; its
*reasoning* is superseded here.

---

## 2. What The Wrong Model Had Already Cost

The operator gave this requirement earlier in the project, in plain terms:

> Can we simply expose them in the installation UI if the user chooses to install
> the sidecar with the bcc enabled? So like a checkbox for the bcc and if filled a
> set of fields with preset default values in them but the user can change them if
> desired. Likely these should be text fields so the user can paste in a location
> but also have a folder picker.

It was represented nowhere:

```
payload.py  NEVER_SHIP = { ".bcc", ... }          # wholesale, one directory
charter §5  | .bcc/ | ... | No |
installer   grep -rn "bcc" tools/sidecar_install/  ->  nothing
E1-E12      no condition mentioned the contract at all
```

T1 built the ship manifest and swept `.bcc` in as a single name. A whole category of
the product disappeared into a one-line frozenset entry, and **T1 parked green**,
because the gate asserted the payload was small and clean — which it was. Nothing
asserted it was *complete*.

That is the shape worth remembering: an exclusion list is not falsifiable by
inspecting what shipped. Everything wrongly excluded is invisible by construction.

---

## 3. Decisions Taken

| Question | Decision |
| --- | --- |
| Cartridge contents | **Contract + protocol + gate runner** — the discipline arrives executable, not aspirational |
| Timing | **T9**, which already owns Install and Packaging |

---

## 4. Changes

**`src/core/payload.py`**

- `NEVER_SHIP` re-documented as **default-off, not forbidden** for `.bcc` and
  `gates`.
- New **`GOVERNANCE_CARTRIDGE`** — `.bcc/BUILDER-CONSTRAINT-CONTRACT.md`,
  `.bcc/TRANCHE_PROTOCOL.md`, `gates/run.py`. Relative paths, not names, because the
  point is carving files out of otherwise-excluded directories.
- New **`CARTRIDGE_FORBIDDEN`** — `CHARTER.md`, `TRANCHE_PLAN.md`, `evidence/`.
  Enumerated so the cartridge cannot be widened by a later hand reading `.bcc` as
  one undifferentiated thing.
- `MAX_CARTRIDGE_FILES = 8` and `cartridge_conflicts()`, which is always empty and
  exists so the contradiction is *detectable* rather than arguable.

**`.bcc/BUILDER-CONSTRAINT-CONTRACT.md`** — two changelog notes added in 0015 were
removed. "An earlier revision listed twelve steps while its checklist listed
thirteen" and "this rule previously hardcoded `_AppJOURNAL/`" are *our repair
history*. In a build-only document they were useful; in a document that installs
into someone else's project they are our laundry. The rules they produced stay; the
account of how we got there moved here.

**`.bcc/CHARTER.md`**

- **E13** added: the cartridge installs *optionally and blank*.
- §5 Zones rewritten. It still listed `toolkit/` as the deliverable and `_design/`
  as the governance zone — **neither has existed since the collapse to root on
  2026-08-06**, and it quoted a line of `harness.py` that had since been changed to
  `TOOLKIT = FACTORY`. The authority document described the previous shape for three
  tranches. It now also states that `payload.py` is the single source of truth and
  that prose disagreeing with the manifest is wrong by definition.

**`.bcc/TRANCHE_PLAN.md`**

- Scoreboard: thirteen conditions, plus the **evidence column** proposed at the last
  alignment. E6a corrected from "not started" to MET (T3 closed two entries ago and
  the table had not moved). **E8 marked MET *to re-derive*** — the harness passes,
  but mount prevention is Linux-only and skips on Windows, so the charter's stated
  proof is half-satisfied. Now: five met, four partial, four not started.
- T9 gains the toggle, its UI shape, and four new gate assertions — including that
  blankness is asserted **by content scan**, not by trusting the substitution, since
  the substitution is the thing under test.
- Backlog: the shipped contract must arrive blank. Our copy still carries resolved
  `BCC-CONFIG` values and project-specific bootstrap notes.

---

## 5. Standing Note

**An exclusion list cannot be validated by looking at the output.** Anything wrongly
excluded leaves no trace to find. `MAX_PAYLOAD_FILES` catches the manifest getting
too loose and nothing catches it getting too tight, which is why a requirement the
operator had already given could vanish into a single frozenset entry and stay
vanished across four tranches.

The discovery-pass technique that applies is **census** — enumerate what the
requirement space contains, not what the implementation touched.

---

## 6. Next

**T5a — One Surface: Observe and Select**, declared under the amended loop:
current state measured, non-goals stated, completion condition written as
`gates/t05a_observe_select.py` before implementation, ordered plan declared, then a
hard stop at step 12 for operator review.
