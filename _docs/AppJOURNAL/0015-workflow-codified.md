# 0015 — The Workflow Is Now Actually The Workflow

- **Date:** 2026-08-09
- **Tranche:** none — governance alignment, at operator instruction
- **Status:** Closed.

---

## 1. The Question

*"Is our workflow codified in the BCC, so that any time I ask you to continue to the
next step this is your basic pattern of engagement?"*

**No.** The eleven steps the operator described were not what was written down, and
the gap was not cosmetic.

---

## 2. Authority To Amend

The operator's ruling: this repository **is** the sidecar that gets vended, not an
instantiation of the sidecar governing a foreign project. The BCC here is a
component of the product under construction, not a contract borrowed from elsewhere,
so aligning it with the project's path is setup work rather than a violation.

Corroborated by the ship manifest: `.bcc` is in **`NEVER_SHIP`**. The contract
governs *this construction* and does not travel with the payload. It reaches other
projects only when supplied by hand as a standalone seed, per its own bootstrap
section. Amending it changes nothing downstream.

---

## 3. What Was Missing

Five things in the operator's list, absent from the written loop:

| Missing | Consequence |
| --- | --- |
| **Operator approval gate** | The builder closed its own work. T1, T2, T3, T4. |
| **Declared plan of steps** | Scope drift had nothing to be checked against. |
| **Consolidation as a named pass** | Done by habit — which is how the `t02` dead stub survived. |
| **"All staleness resolved"** | Only `docs/` and `AGENTS.md` were covered. |
| **Synopsis of the next tranche** | The rule said only "the next action is stated". |

The first is the serious one. There was no point in the written loop where the
builder stopped and required the operator's word. Four tranches were parked on the
builder's own account of the builder's own work.

Three things already in the loop and absent from the operator's list, kept
deliberately: `read constraints` and `record start`; gate-first plus
verify → repair → re-verify, evidence, and the discovery pass; `respect closure`.

---

## 4. Two Defects Found In The Contract Itself

**§2.8 numbered twelve steps; its own checklist listed thirteen.** `record start`
appeared only in the checklist. The builder had been following the checklist, so an
unnumbered step was governing real work. Both forms now agree, and a note in the
rule says they must.

**§3.1 hardcoded `<sidecar-root>/_AppJOURNAL/`** while `[BCC-CONFIG:
JOURNAL_PATH="_docs/AppJOURNAL"]` sat above it. The contract contradicted its own
configuration block. The config line is now stated as authoritative.

---

## 5. What Changed

**`.bcc/BUILDER-CONSTRAINT-CONTRACT.md`**

- **§2.8 rewritten** — seventeen steps in four blocks (declare 1–6, execute 7–11,
  approve 12–13, close 14–17) and **three terminal states**: parked, blocked, and
  **awaiting approval**.
- New steps: *declare current state* (measured, not remembered), *declare
  non-goals*, *declare the completion condition*, *declare the plan*, *consolidate*,
  *submit for operator review*, *revise and resubmit*, *resolve staleness*, and
  *declare the next tranche*.
- Step 10 now requires an activity **capable of revealing what the builder was not
  looking for**, and requires the verification configuration to be recorded.
- Step 11 now states that every repair is presumed to have a **partner effect**
  elsewhere until shown otherwise. Five occurrences justify a standing rule.
- **§2.6** — parking is a state the user grants, not one the builder declares.
- **§3.1** — journal path defers to `JOURNAL_PATH`.

**`.bcc/TRANCHE_PROTOCOL.md`**

- **§2 no longer reproduces the loop.** It carried a verbatim copy, which meant two
  copies that could drift — the exact failure this project was started to remove. It
  now points at the anchor and carries only the *mechanism*: which project artifact
  satisfies which BCC step.
- **§4 Declaration** extended to BCC steps 2–7, including the ordered plan.
- **§5.0 Awaiting approval** — what is submitted, and what the builder may not do
  while waiting.
- **§5 Parking** — operator approval is the first criterion; staleness and the
  next-tranche synopsis added.

**`.bcc/TRANCHE_PLAN.md`** — standing practice recorded.

---

## 6. Effect On `"continue to the next step"`

The builder runs BCC steps 1–11, **stops at 12**, and waits. No documentation, no
parking, no next tranche without the operator's word.

---

## 7. Next

**T5a — One Surface: Observe and Select.** Declaration to follow under the amended
loop: current state measured, non-goals stated, completion condition written as
`gates/t05a_observe_select.py` before implementation, and the ordered plan declared
so there is something to review the work against.
