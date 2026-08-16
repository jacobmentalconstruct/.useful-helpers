# 0033 — T7 Declared: Shared Project Awareness Prototype

- **Date:** 2026-08-16
- **Tranche:** T7 — Shared Project Awareness Prototype
- **Status:** **DECLARED.** Gate written, run, and **red**. No implementation.
- **Sized by:** C1b (0032). **Bounded by:** `TRANCHE_PLAN.md` C1–C4, C1a.

---

## 1. Outcome

> Existing deterministic tools are composed into **one compact, evidence-backed current
> orientation** of the bound target, persisted against the instance, and exposed as the
> **same revision** to human and MCP agent.

**Charter §3.3 walk steps advanced:** 6, 7, 8, and the awareness half of 13.

**The invariant, stated so it cannot harden into ceremony:** T7's understanding is
produced by canonical tools through the common governed composition path — **not
through a private application or backend.** Whether the composition ends up as one
playbook, several selected by evidence, or a front-door operation invoking them is
decided by implementation evidence, not declared here.

---

## 2. The gate is black-box, and that is the point

`gates/t07_shared_awareness.py` names **no module, no class, no file.** It builds three
targets, installs real instances, and calls the product's own entrances.

T7's nouns are seductive. *Awareness* invites an `AwarenessManager`, an
`AwarenessStore`, an `AwarenessEngine` and a schema framework — none of which any
requirement asks for. So the gate asserts behaviour at the entrance and lets the
failing assertions say what machinery is actually absent.

**33 assertions. 3 pass, 30 fail.**

The three that pass are pre-existing invariants (protocol §5.1a), not completion:
a payload fixture materialises, an instance installs, and `.git` is excluded from the
map.

---

## 3. Four properties made mechanical

Each had a history of degrading into a green assertion whose meaning drifted.

### 3.1 Context reduction is a measured ratio

Not *"materially smaller"*. The gate sums the serialized bytes of the contributors,
measures the default projection, and holds it to a threshold declared in **one place**:

```python
MAX_PROJECTION_RATIO = 0.25      # projection / summed contributor payload
MAX_PROJECTION_BYTES = 8192      # and a ceiling, so a thin target cannot pass
                                 # merely by having little to be a fraction of
```

The ceiling matters: a ratio alone is satisfiable by an empty target. If dogfooding
proves 25% wrong it is changed **deliberately**, in one place, with a reason.

The invariant: **rich evidence stays local; ordinary orientation does not shovel raw
evidence into model context.**

### 3.2 A revision describes observations, not a counter

Three distinct questions, three distinct fields:

| | |
| --- | --- |
| `instance` | **who am I** — the T6 UUID |
| `revision` | **what did I know** |
| `evidence_fingerprint` | **what observed reality produced that knowledge** |

Asserted both ways: re-observing an unchanged target yields the **same** fingerprint;
adding one file changes it. Without that, *"revision 5"* means only *"the fifth time
this ran"*. Bound to the instance UUID, not to an absolute target path.

### 3.3 A canonical handle must round-trip

Stated strongly, because this is T7's highest-value anti-hallucination property:

> **Every canonical handle awareness promotes must be accepted by the tool that owns
> it and resolve back to the entity it names.**

A handle carries its own owner. Awareness that emits an identifier without saying which
tool resolves it has not made it canonical, only decorative. This exists because a
model in this project invented `CellBackend` from a module name plus a project name and
reported the resulting correct refusal as a capability gap.

### 3.4 Drill-down crosses back into evidence, not narrative

Deliberately **not** *"returns a byte-identical copy"* — that would force awareness to
persist duplicates of every contributor response. The requirement is **provenance
sufficient to retrieve the canonical evidence**. A stored raw observation satisfies it;
a retrievable `evidence_id` satisfies it; a re-runnable invocation satisfies it.

What fails is a drill-down answered with prose — a model reconstructing what the
evidence probably said.

---

## 4. Three targets, and the point is degradation

Software, records, empty. **Equal richness is not required; truthful thinness is.**

- **empty** — proves less evidence is not failure
- **records** — proves software concepts are not imposed just because the richest
  contributor set came from software
- **software** — proves the compact envelope still preserves architecture and handles

Together they stop T7 becoming *"Python Project Awareness"*.

**The records and empty targets run independently of the software target's outcome**,
because *thin is legitimate* is exactly as interesting when the rich case is failing.

---

## 5. Two gate-design decisions worth recording

### 5.1 The gate does not stop at the first missing prerequisite

The first run returned early when no awareness envelope existed: **2 failures where 25
requirements exist.** A reader would have seen *"3 passing, 2 failing"* and inferred the
tranche was nearly done.

Every dependent assertion is now named and failed explicitly, so the gate shows its
whole surface at declaration. `_blocked()` uses **`check(False)`, not `skip()`** — a
skip says *"this could not be measured here"*; these can be measured and the answer is
no. Calling them skipped would hide the tranche's size behind an honest-looking word.

This is the project's recurring defect stated as gate design: **absence is invisible in
a column of green, and an assertion that never ran is absent, not passing.**

### 5.2 One assertion was passing for a reason unrelated to the product

*"the records target does not invent software findings"* was implemented as
`not _has_software_ontology(a)` — and `_has_software_ontology({})` is `False`, so it
**passed whenever awareness did not exist.** Two of the original five passes were
hollow.

Now guarded: meaningful only once there are findings, and recorded as a failure
otherwise. Eighth instance of this family, and the first caught within minutes of
writing it rather than tranches later.

---

## 6. Also gated: the `.git*` prune over-reach

From 0032's backlog, and **narrow on purpose.** `_probe` prunes with
`not d.startswith(".git")` — written for `.git`, silently swallowing `.github`,
`.gitlab` and anything else sharing the prefix. `.github` is **not** in `PRUNE`, so CI
configuration is invisible to the map and `command_profile` cannot find workflow files.

Two assertions, one distinction: `.git` **is** excluded, `.github` **is not**. Confirmed
red. This does not generalise the exclusion subsystem — one failing regression, one
correction.

---

## 7. Non-goals

No target mutation (T8). No `attach` rewrite — the reduction pass is **one**
responsibility, the tree probe, discharged only where T7 touches it. No second chain
engine, and no speculative enlargement of the first. No One Surface. No "Project
Awareness App". No awareness ontology framework. No incremental or semantic
invalidation — coarse staleness only.

**No tool for `newest_mtime`.** *"No canonical tool currently reports it"* is not
*"we need a tool"* (C1 rule 1). Build the T7 path first. If the existing staleness
mechanism can legitimately remain front-door logic, leave it there. Only if a second
consumer independently needs the same primitive does extraction become justified — which
is what the atomicity and ownership rules exist to decide.

---

## 8. Stop condition

Both projections resolve the same revision id on all three acceptance targets, with no
application-layer dependency, and the gate suite green on both platforms.

---

## 9. Next

Implement against the red gate. **Do not design an awareness subsystem in advance** —
let the failing assertions reveal the minimum missing mechanism.
