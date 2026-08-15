# 0030 — Five Clarifications to the Product Shape

- **Date:** 2026-08-14
- **Status:** alignment only. **No implementation.** T6 remains **REOPENED** (0028);
  T7 remains **sketched, not declared.**
- **Clarifies:** 0029. That entry stands unedited; this one corrects its language where
  the operator found it too strong, too rigid, or aimed at the wrong measure.

---

## 1. Why this is a separate entry

0029 declared the shape hours ago and got one framing materially wrong. Amending it in
place would erase the fact that the correction was needed — and the correction is the
useful part. Protocol §5.1: historical evidence is immutable; active statements move.

Four of the five clarifications *narrow* the work. None expand it.

---

## 2. The correction that matters most — size is not the smell

**0029 §2.3 led with "1051 lines."** That is the wrong measure, and stating it first
implied line count is the charge. It is not.

> A 1,000-line deterministic snapshot compiler with **one narrow contract** is
> acceptable. A 300-line "tool" that owns a private project model, its own parser
> suite, its own state store and its own workflow is not.

The real smell is **private ownership of capabilities, state or workflows that belong
to the common bench.** `attach`'s problem was never its size; it is that the tree
probe, the `ast` reader, the manifest parsers and the cartridge scoring are privately
owned. The line count is a proxy for how much was inspected, and this plan now says so
wherever a count appears.

Recorded in `CHARTER.md` §1.4 as its own sub-section, and in `C1a.3`.

---

## 3. Do not decompose Project Mapper ceremonially

Finding 1 in 0029 changed the problem and 0029 did not follow the change through.

If `apps/projectmapper` is already a registered tool with no private backend and no
app-framework dependency, then **sitting in `apps/` is partly a classification defect,
not necessarily an architectural one.**

The audit now applies an explicit test first:

> Is this one coherent deterministic operation with a useful independent contract, or
> merely an orchestration of independently useful existing primitives?

Genuinely atomic from the caller's perspective — target in, canonical artifact out —
means it **may remain one tool and simply be re-homed.** Only if its internals
duplicate canonical primitives does composition apply.

**Splitting snapshot compilation into six tools plus a playbook to satisfy an abstract
preference for chains would be ceremony.** The goal is removal of duplicated
ownership, not maximum decomposition.

---

## 4. `playbook.py` is the presumptive owner — do not enlarge it speculatively

Its limitations (whole-value references, no fan-out, fail-fast) **remain limitations
until a real T7 or T8 acceptance path cannot be expressed without one of them.** Not
improved because T7 *might* need richer orchestration. The prototype forces the minimum
extension, if any.

And 0029's assertion *"T7 is composed as a chain through existing machinery"* was too
rigid — rigid enough to manufacture ceremony around itself. It is replaced by the
invariant it was trying to express:

> **T7's understanding is produced by canonical tools through the common governed
> composition path, not through a private application or backend.**

One playbook, several small playbooks selected by evidence, or an existing front-door
operation invoking them — decided by implementation evidence. What is forbidden is new
private orchestration inside `attach`. What is not required is a playbook file written
to prove a point.

---

## 5. The `attach` audit is the high-value half of C1b

Now specified concretely. Each substantial internal responsibility receives one of five
verdicts: **keep** (front-door orchestration), **replace** (duplicates an
already-registered tool — name it), **move** (shared state/core, multiple consumers),
**presentation**, or **retain for now** (no existing equivalent *demonstrated*).

The deliverable is one sentence:

> *Of `attach`'s current responsibilities, N are legitimate front-door logic, N
> duplicate canonical tools, N belong to shared awareness state, and N are
> presentation.*

**Refactor none of them during the audit.** `replace` verdicts are discharged **only
where T7 actually touches that responsibility.** T7 is partly a reduction pass;
reduction is a consequence of the work, never a separate 1051-line rewrite.

---

## 6. The STOP assertion means semantics, not folder purity

*"If deleting `apps/` would break the walk, convergence is not finished"* is retained,
and now reads explicitly as **no dependency on specialised application architecture** —
not *the directory must become empty at all costs*.

If the surviving `projectmapper` is an ordinary registered tool that happens to live
under `apps/`, **re-homing it satisfies the architecture.** What must not survive is a
private backend, project model, state store or workflow engine that the acceptance walk
depends on.

---

## 7. C1b's question, narrowed

The audit exists to answer one thing:

> **How much of the useful prototype already exists as canonical tools, and exactly
> what duplicated or private logic must be removed or relocated so those tools behave
> as one bench?**

**That answer determines T7's implementation size.** Nothing is coded until it is in
hand.

---

## 8. Surfaces changed

| Surface | Change |
| --- | --- |
| `CHARTER.md` §1.4 | new sub-section *"A large tool is not an application"* — ownership not size; location is not architecture; removal of duplicated ownership, not maximum decomposition |
| `TRANCHE_PLAN.md` C1a.3 | the measure restated as private ownership; line counts declared a proxy for inspection, never the charge |
| `TRANCHE_PLAN.md` C1a.4 | no speculative enlargement of the chain engine; limits stand until an acceptance path cannot be expressed |
| `TRANCHE_PLAN.md` C1b | the narrow question stated first; the atomicity test; Part 1 applications, Part 2 the five-way `attach` classification with its one-sentence deliverable; *refactor nothing during the audit* |
| `TRANCHE_PLAN.md` T7 | the rigid chain assertion replaced by the composition-path invariant; T7 named as partly a reduction pass, bounded to what it touches |
| `TRANCHE_PLAN.md` STOP | semantics and ownership, not folder purity; re-homing satisfies it |
| `TRANCHE_PLAN.md` sequence | standing operator instruction: **architecture discussion does not reopen before the T6 repairs** |
| `apps/README.md` | the atomicity test; location-is-not-architecture; size-is-not-the-smell; retirement **or re-homing** |

---

## 9. Next, and it is fixed

```text
T6 bounded updater repair  ->  certify  ->  re-park
  ->  C1b Application Absorption Audit  ->  return the classification table
  ->  declare T7  ->  shared-awareness proof  ->  park
  ->  T8 governed work loop  ->  park
  ->  release / STOP certification  ->  DOGFOOD
```

Next session opens on T6's two updater defects, gate-first. No architecture discussion
before them. No T7 implementation before C1b's table exists.
