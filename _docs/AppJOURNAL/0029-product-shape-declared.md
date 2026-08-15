# 0029 — The Enduring Product Shape, Declared

- **Date:** 2026-08-14
- **Status:** alignment only. **No implementation.** T6 remains **REOPENED** (0028);
  T7 remains **sketched, not declared.**
- **Amends:** `CHARTER.md` (new §1.4), `TRANCHE_PLAN.md` (C1a, C1b, T7, T8, STOP,
  sequence), `docs/ARCHITECTURE.md` §2 and §7, `apps/README.md`

---

## 1. The alignment that was missing

Every prohibition in Charter §2 was circling one shape without naming it. Named now:

```text
    mechanical tools  ->  governed tool chains  ->  common runtime/seam  ->  human + agent
```

**not**

```text
    mechanical tools  ->  specialised applications  ->  human + agent
```

Useful Helpers is not a platform hosting a family of applications built on a toolbench.
It is **one governed box of capable hands**. `apps/` — including Project Mapper — is
transitional implementation and reference material. Its *behaviours* are valuable; its
*structure* is not part of the intended prototype.

Charter §1.4 owns this, anchored `SIDECAR:PRODUCT-SHAPE` and enumerated in
`gates/t05`. The governing test for any proposed structure, from here on:

> Is this something a **tool** does, something a **chain** of tools accomplishes,
> **shared state** the whole bench needs, or a **projection** for a human or agent?
>
> If it cannot be justified as one of those four, it does not belong in the prototype.

---

## 2. Three preliminary findings

Established while writing the alignment, because a plan built on assumptions about
`apps/` and the chain machinery would have been aspirational. **This is not the
Application Absorption Audit** — it is what made the audit's shape obvious, and two of
the three materially reduced the work the audit implies.

### 2.1 `apps/` contains exactly one application, and it is already a tool

One registered entry: `projectmapper`, `Apply`, `writes: toolkit`, entry
`apps/projectmapper/cli.py`. It satisfies the tool contract and imports only
`_toolkit` and stdlib.

So "the Project Mapper application", in the live tree, is **one tool sitting in the
wrong directory**, plus a GUI (`src/ui/mapper_view.py`) and a `run.bat map` verb.

The absorption is far smaller than the phrase suggests, and the real question is not
*"how do we replace this application"* but *"should its capture behaviour become a
chain over existing primitives, or remain one primitive that is simply re-homed?"* The
audit answers that. **Neither answer is a new application.**

### 2.2 The chain engine already exists and already passes the test

`src/core/playbook.py` runs `[{id, tool, args}]` through `invoke()` and binds a later
step's argument to an earlier step's output field via `@<id>.<dotted.path>`. That is
precisely *tool A → select fields → tool B → compose result*.

`playbooks/ground_report.json` demonstrates it in the shipped tree today:

```text
report  ->  @report.markdown  ->  evidence attach  ->  @ground.evidence_id  ->  evidence verify
```

**No second chain engine is needed, and building one is now explicitly forbidden**
(C1a.4). Its known limits are named rather than worked around: whole-string references
only (no transform of the referenced value), no fan-out or map, and
stop-on-first-failure. If T7 needs more, the requirement is the *smallest extension to
that owner*.

This is the second time in two days that inspecting before concluding overturned an
assumed gap. The first was `symbol_graph`.

### 2.3 `attach` is already the hazard it was warned about

**1051 lines. Imports `_toolkit`, `summarize_shared` and stdlib — and nothing else.
It calls no other tool through the seam.**

It carries its own tree probe, its own `ast` docstring reader, its own YAML / TOML /
`go.work` manifest parsers, its own cartridge scoring, its own map builder, and its own
staleness signature. Every one of those is **category C**: capability that exists, or
should exist, as a registered tool.

The guidance was *"do not let `attach` become Project Mapper 2."* The honest reading is
that **it is already partway there**, and the warning arrived after the fact rather
than before it.

Two consequences, both now binding:

- **T7 must not add to that mass.** Its awareness composition runs as a chain through
  the playbook machinery and the seam, not as more private orchestration inside
  `attach`.
- **Reduction is incremental and evidence-led.** The audit classifies every internal
  function as **A** orchestration, **B** shared-core, **C** duplicated primitive, or
  **D** presentation. Category C migrates to the canonical tool over time. *No rewrite
  is scheduled*, because a 1051-line rewrite during convergence is exactly the
  architecture-first work this phase exists to stop.

---

## 3. What changed in the active surfaces

| Surface | Change |
| --- | --- |
| `CHARTER.md` §1.4 **new** | the enduring product shape; the four-layer table; `apps/` declared transitional; the governing design test. Anchored `SIDECAR:PRODUCT-SHAPE` |
| `gates/t05` | anchor enumerated |
| `TRANCHE_PLAN.md` **C1a** | anti-regression: no new application; the private-backend tripwire; `attach` must not become an application disguised as a tool; no second chain engine; no tool merely because an app had that function name |
| `TRANCHE_PLAN.md` **C1b** | the **Application Absorption Audit** — a declared diagnostic step between T6 re-park and T7 declaration, with its deliverable table specified. Plus the three findings above |
| `TRANCHE_PLAN.md` T7 | reframed as the **first proof of the tool-chain architecture**; contributor selection declared evidence-driven, not a hardcoded universal pipeline; two added assertions — composed as a chain, and **no live `apps/` member in the path** |
| `TRANCHE_PLAN.md` T8 | the second proof; the four forbidden applications named explicitly (change-review, verification, diff, awareness-refresh) |
| `TRANCHE_PLAN.md` STOP | **the architectural STOP assertion**: the acceptance walk must not require any specialised application layer. *If deleting `apps/` would break the walk, convergence is not finished.* Plus the six-condition parity test for retiring an application |
| `TRANCHE_PLAN.md` sequence | audit + T7 + T8 + release/STOP certification. **"The finish line is finite and this is all of it."** No T9 unless use demonstrates a blocker |
| `docs/ARCHITECTURE.md` §2, §7 | `apps/` no longer presented as an enduring adapter class; layout marks it TRANSITIONAL; stale `_docs/` path corrected |
| `apps/README.md` | rewritten as a transitional-layer notice: preserve behaviour not structure, Project Mapper's valuable behaviours enumerated, retirement by demonstrated parity only, audit named as the gate |

**Not changed:** the BCC. `apps/` was not deleted — retirement is by demonstrated
parity, and nothing has been demonstrated yet.

---

## 4. Local computation as the compression boundary

Restated here because it is a product requirement, not an optimisation, and C2 already
carries it: filesystem, AST, database, graph and scanning work happens **locally**;
rich raw evidence stays local and reachable; only compact summaries and canonical
handles are promoted into awareness; the model receives awareness plus requested
drill-down.

The measured failure it exists to prevent: **~25 KB of envelope spent to recover three
integers the machine had already computed.** Optional natural-language synthesis may
use a local model, but the deterministic observations remain authoritative.

---

## 5. Next

1. Discharge T6's bounded repair (0028) — gate first, mutation-tested — then certify
   and re-park.
2. Run the **Application Absorption Audit** (C1b). Diagnostic; implements nothing.
3. Declare T7.

No T7 implementation and no absorption work begins before step 1 completes.
