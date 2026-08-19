# Tranche Plan

Status: **ACTIVE.** T0-T7 parked (0036). **T8 DECLARED** 2026-08-19 (0037) — gate
written and **red: 19 pass, 16 fail**, three safety preconditions among them.
Development mode: **CONVERGENCE**. Then the two closure gates — parity and release —
then STOP. The audit sized it: of `attach`'s 24 responsibilities T7 touches 8, discharges
**one** duplication, and depends on no live `apps/` member.
Date: 2026-08-06, amended 2026-08-09, mode changed 2026-08-14, T6 reopened and
re-parked 2026-08-14.
Authority: subordinate to `CHARTER.md`; procedure defined by `TRANCHE_PROTOCOL.md`.
This document owns **sequencing, the convergence rules and the prototype STOP**.
Product topology, ownership semantics and the prototype objective belong to the
Charter (`SIDECAR:PROTOTYPE-OBJECTIVE`) - cite `SIDECAR:*` identifiers here, never
restate them.

*No ownership declaration appears in this file by design.* Ownership anchors are the
Charter's registry; a Plan that declared one would be the second normative surface
`BCC-ONE-AUTHORITY` exists to prevent, and `gates/t05` asserts their absence here.
It caught an attempt to add two, an hour after the convergence phase was written.

Numbering starts at **T0** and is this project's only valid numbering. Every
identifier in archived material belongs to a predecessor project.

Each tranche states its outcome, its gate, and its non-goals. The gate is
written during declaration, before implementation.

---

## The Convergence Phase

Adopted 2026-08-14, on the evidence of the `_theCELL` dogfood run. **T6 re-parked 2026-08-14 (0031), so it
begins now** — at C1b. The rules and sequence below are settled, and no convergence
tranche is declared while an earlier one is open. The question this plan answers has
changed:

| Until T6 | From T7 |
| --- | --- |
| *What subsystem should we design next?* | **What prevents the existing toolbox from behaving like one useful product?** |

The project has enough organs. Charter §1.3 states the objective; this section states
the rules of engagement, and the two sections after it state the sequence and the
stop. **Nothing here weakens the BCC or the protocol** — the tranche loop, the gate
discipline, the discovery pass and the operator approval gate all still apply.

### C1. Anti-scope-creep rules

Binding for the whole convergence phase. Each one exists because this project has
already spent a tranche on the temptation it names.

1. **No new tool** unless an end-to-end prototype attempt demonstrates that no
   existing tool can supply the required capability. *Attempt first, then conclude.*
   The one time this was skipped, the conclusion was a hallucinated symbol name
   reported as a capability gap.
2. **No new subsystem** if composition of existing mechanisms solves the problem.
3. **No new ontology or graph framework** merely to represent awareness. Charter §2.8
   already forbids a graph engine; this extends it to the awareness envelope.
4. **No One Surface redesign.** Use the smallest existing UI or report surface that
   makes awareness legible. E3 is post-STOP.
5. **No local-agent framework.** Charter §2.7.
6. **No automatic or incremental semantic invalidation system.** Coarse
   signature-based staleness already exists and must not be regressed; a finer one is
   not authorised.
7. **No broad packaging project** beyond what is required to exercise the prototype.

A rule may be discharged only by an operator-approved amendment recorded in the
journal, citing the end-to-end attempt that demonstrated the need.

### C1a. Anti-regression: no new application layer

Charter §1.4 (`SIDECAR:PRODUCT-SHAPE`) states the layering. These are its enforcement
rules for the convergence phase.

1. **No new standalone application may be added.** Not one.
2. **The private-backend tripwire.** If a proposed feature starts acquiring its own
   private backend, project model, state store, tool orchestration, mapping
   representation, or workflow engine — **stop** and re-decide which of the four it is:
   a primitive tool, a tool chain, shared core state, or a projection over shared
   state.
3. **`attach` must not become an application disguised as a tool.** It may coordinate
   existing capabilities. It may not reinvent scanners, parsers, code intelligence,
   snapshot machinery, semantic stores, or a second project ontology.
   *This is not hypothetical — see the preliminary finding below.*

   **The measure is private ownership, not size** (Charter §1.4). A large primitive
   with one narrow contract is acceptable; a surface of any size that owns its own
   project model, parser suite, state store or workflow is not. Where a line count
   appears in this plan it is a proxy for how much was inspected, never the charge.
4. **No second chain engine, and no speculative enlargement of the first.**
   `src/core/playbook.py` already runs `[{id, tool, args}]` through `invoke()` and
   binds a later step's argument to an earlier step's output field via
   `@<id>.<dotted.path>`. That is exactly *tool A → select fields → tool B → compose*.

   Its limitations — whole-value references, no fan-out, fail-fast — **remain
   limitations until a real T7 or T8 acceptance path cannot be expressed without one
   of them.** Do not improve the engine because T7 *might* need richer orchestration.
   Let the prototype force the minimum extension, if any, and make it to that owner.
5. **No new tool because an app once had a function with that name.** Demonstrate the
   primitive capability is genuinely missing first (C1 rule 1 already, restated here
   because absorption is where the temptation lands).

**Preserve useful behaviour, not application structure.** If 80% of an application's
behaviour already exists in tools, compose those tools rather than transplanting its
backend.

### C1b. Application Absorption Audit — a declared step, not a tranche

**COMPLETE — journal 0032, 2026-08-15.** Diagnostic only: it implemented nothing,
refactored nothing, and created no framework. Headline result:

> `attach`'s 34 functions group into **24 responsibilities**: 12 keep, 3 replace,
> 3 move, 4 presentation, 2 retain. **T7 touches 8 and discharges one duplication,
> partially.** `projectmapper` is **atomic — re-home, do not decompose.** T7 needs no
> live `apps/` member.

The original specification follows, unchanged.

**The one narrow question it exists to answer:**

> How much of the useful prototype already exists as canonical tools, and exactly what
> duplicated or private logic must be removed or relocated so those tools behave as one
> bench?

**That answer determines T7's implementation size.** Nothing is coded until it is in
hand.

The expected finding is *not* "build replacements." It is *"most of this already
exists in the bench; compose it, prove parity, remove the shell."*

#### Part 1 — application surfaces

One row per live application surface:

| application | useful behaviour | existing primitive tool(s) already providing it | chain/core component that should own composition | genuinely missing primitive, if any | persisted format worth preserving | retirable after parity? |

Plus: any private state or model duplicated by an app, the safest retirement order,
and **whether T7 can be completed without depending on any live app.**

**The atomicity test — apply it before proposing any decomposition:**

> Is this one coherent deterministic operation with a useful independent contract, or
> is it merely an orchestration of independently useful existing primitives?

If it is **genuinely atomic from the caller's perspective** — target in, canonical
artifact out — it may remain **one tool**, and the correct action is to **re-home it**.
If its internals duplicate canonical primitives, compose those instead.

*Applied to `projectmapper`:* Finding 1 below shows it has no private backend and no
app-framework dependency, so sitting in `apps/` is partly a **classification defect,
not necessarily an architectural one.** Splitting snapshot compilation into six tools
and a playbook to satisfy a preference for chains would be ceremony. **The goal is
removal of duplicated ownership, not maximum decomposition.**

#### Part 2 — `attach`, and this is the high-value half

One row per substantial internal responsibility:

| responsibility | current owner | existing canonical equivalent? | verdict | **T7 touches it?** |
| --- | --- | --- | --- | --- |
| tree probe | `attach` | `file_tree` / other? | replace / retain | yes / no |
| AST docstring read | `attach` | a code-intel tool? | replace / retain | yes / no |
| manifest parsing (YAML / TOML / `go.work`) | `attach` | an existing parser tool? | replace / retain | yes / no |
| cartridge scoring | `attach` | possibly unique | keep / move | yes / no |
| workbench persistence | `attach` | shared-state candidate | move | yes |
| next-step presentation | `attach` | front-door presentation | keep | yes |

*(illustrative rows — the audit fills them from the code, and adds the ones this sketch
does not anticipate.)*

The five verdicts:

| verdict | meaning |
| --- | --- |
| **keep** | legitimate front-door orchestration |
| **replace** | duplicates an **already-registered** tool; name it |
| **move** | belongs to shared state/core because multiple consumers need it — awareness persistence, instance association, revision identity |
| **presentation** | human-readable summary and next-step rendering |
| **retain (for now)** | no existing equivalent **demonstrated**; retained explicitly, not by default |

**`T7 touches it?` is the column that governs the work.** A `replace` verdict is
discharged only where T7 actually needs that responsibility. If T7 needs the tree probe
and a canonical tool already provides it, the duplication goes. If T7 never touches
some parser buried in `attach`, **it is left alone** — and dogfooding decides whether it
ever mattered.

Without that column, convergence becomes *"clean up all of `attach` before
continuing,"* which is how a reduction pass turns into a rewrite and the STOP recedes.

The output that matters is one sentence of the form:

> *Of `attach`'s current responsibilities, N are legitimate front-door logic, N
> duplicate canonical tools, N belong to shared awareness state, and N are
> presentation.*

**Refactor none of them during the audit.** The verdict is the deliverable.
`replace` verdicts are discharged **only where T7 actually touches that
responsibility** — T7 is partly a reduction pass, never a 1051-line rewrite.

#### Preliminary reading, taken 2026-08-14 while writing this section

Three facts, cheap to establish, recorded so the plan is not aspirational. **This is
not the audit** — it is what made the audit's shape obvious.

1. **`apps/` contains exactly one application: `projectmapper`** — one registered tool
   (`Apply`, `writes: toolkit`, entry `apps/projectmapper/cli.py`). It already
   satisfies the tool contract and depends only on `_toolkit` and stdlib. So "the
   Project Mapper application" is, in the live tree, **one tool in the wrong
   directory** plus a GUI (`src/ui/mapper_view.py`) and a `run.bat map` verb. The
   absorption is far smaller than the phrase suggests, and the real question the audit
   must answer is whether its capture behaviour should become a **chain** over
   existing primitives or remain **one primitive** that is simply re-homed.
2. **The chain machinery already exists and already passes the C1a.4 test.**
   `playbooks/ground_report.json` demonstrates it today: `report` → bind
   `@report.markdown` → `evidence attach` → bind `@ground.evidence_id` → `evidence
   verify`. Known limits, to be named rather than worked around: whole-string
   references only (no transform of the referenced value), no fan-out or map, and
   stop-on-first-failure.
3. **`attach` is already the C1a.3 hazard, measured.** 1051 lines, importing only
   `_toolkit`, `summarize_shared` and stdlib — **it calls no other tool through the
   seam.** It carries its own tree probe, its own `ast` docstring reader, its own
   YAML/TOML/go.work manifest parsers, its own cartridge scoring, its own map builder
   and its own staleness signature. Every one of those is category **C**: capability
   that exists, or should exist, as a registered tool.

   Its enduring responsibility narrows toward: *determine current scope → select
   appropriate existing observations → compose compact orientation → persist and
   reference that result → recommend useful next actions.* The audit classifies every
   internal function as **A** legitimate orchestration, **B** shared-core
   responsibility (awareness persistence, instance association, revision identity),
   **C** duplicated primitive capability, or **D** presentation. Category C moves to
   the canonical tool — **incrementally, not as a rewrite.**

   The warning *"do not let `attach` become Project Mapper 2"* arrived late. **It is
   already partway there.** T7 must not add to that mass; the audit classifies it, and
   reduction is incremental and evidence-led, not a rewrite.

### C2. The signal-to-context contract

Local compute is cheap; model context is expensive. Measured on `_theCELL`: `report`
(24.5 KB) and `dead_code` (24.9 KB) returned ~49 KB of envelope to supply **seven
summary integers** of usable orientation.

Every awareness contributor is therefore read at **two levels**:

| Projection | Contents | When |
| --- | --- | --- |
| `summary` (default) | small, deterministic, high-signal fields | ordinary orientation |
| `full` (drill-down) | the complete existing tool output, unchanged | only when a human or agent asks for it |

The tools do not change shape. The composition layer chooses the level. **The model
reasons over derived signal; it does not pay tokens to rediscover the useful fields
inside mechanical output.**

### C3. Canonical handles travel with the prose

The deterministic system knew `src.backend::Backend`. The model, reading prose,
invented `CellBackend` and reported the resulting lookup failure as a product defect.

So awareness records the **machine handle beside the readable label**, for every
directly addressable object — files, modules, symbols, tables, subsystems.

- Human projection may emphasise the readable label.
- Agent projection **must** carry the canonical identifier alongside it.

This lets the next call ground itself in a deterministic identity instead of
reconstructing a name from a sentence.

### C4. Three acceptance targets

T7 and T8 are exercised against all three. **Equal richness is not required; useful
and truthful degradation is.**

| | Target | What it proves |
| --- | --- | --- |
| A | a nontrivial software project (`_theCELL`) | the rich case |
| B | a mixed records / data / document target | the product is not code-only (Charter §2.3) |
| C | an empty or nascent target | thin is a legitimate map, not a failure |

An empty directory and a folder of PDFs are legitimate targets whose awareness is
legitimately thinner. Forcing either into a software ontology is a defect.

---

## End-State Scoreboard

Which of the charter's **thirteen** conditions actually hold. Kept here because "T2
is closed" and "the project is closer to done" are different claims, and only this
table answers the second.

The **evidence** column is the point. A condition backed by "the mechanism exists"
is not met; it is unfalsified. E5 was claimed outright while seven of eight call
sites were unattributed, and the difference between those two states is exactly this
column.

| | Condition | Status | Evidence |
| --- | --- | --- | --- |
| E1 | Installs into an arbitrary directory, CPython only | partial | T6: the real setup application installs a canonical instance, the gate executes the launch command it prints, and the installed product runs. Fresh-**machine** install (bare host, no dev tree) is `P-install-packaging` |
| E2 | Maps any directory, across domains | partial | `attach` works, and was exercised against a real unfamiliar target (`_theCELL`, 2026-08-14) — it classified the domain, mounted a workbench and produced a map. Cross-domain still unproven: T7's three acceptance targets (C4) are the evidence that would close this |
| E3 | One GUI surface reaches every tool and chain | **not started** | **Post-STOP.** Explicitly out of the convergence phase (C1 rule 4). The prototype needs the smallest legible human projection of shared awareness, which is a T7 deliverable and is not One Surface |
| E4 | An agent reaches everything through MCP | partial | MCP entrance exists; parity unasserted |
| E5 | Human and agent indistinguishable to the seam | **MET** | t02 gate: census over all of `src/`, every call site attributed |
| E6a | Each sees the other **act**, live | **MET** | T3 — measured poll cost 0.29 ms; resync on shrunken ledger |
| E6b | Each can query the other's **context** | **MET** | T2 presence; CLI no longer wipes it |
| E7 | Daily-driver workflows exist as chains | **not started** | **Post-STOP.** Formerly scheduled as T7; that number now belongs to Shared Project Awareness. Preserved as `P-chains` |
| E8 | Lifecycle never silently mutates target-owned content; runtime mutation is governed and scoped | **NOT MET** — restated by T5 | **Reclassified 2026-08-09.** The old claim was proven against the old wording. The phase x authority matrix (Charter §3.2) has **no** assertion behind install/update/uninstall/startup/self-maintenance, and `packaging/installer/install.py` — the product's install entrance — had never been exercised by any gate. **T6 closed the install row only**: `gates/t06` runs the real installer and hashes the whole target tree before and after. Update, uninstall, startup and self-maintenance remain unproven, so E8 stays NOT MET. Harness PRECEPT/ENFORCEMENT remain valid partial evidence; mount prevention is Linux-only |
| E9 | Parts bin deletable, everything still passes | **not started** | `P-closure` |
| E10 | Every documented claim is executable | partial | gates cover much, not all |
| E11 | Payload carries product identity and self-knowledge, no development history | **NOT MET** — restated by T5 | **Withdrawn 2026-08-09.** The claim rested on a lineage check searching for *another project's* vocabulary (`mindshard`, `appfoundry`, `bdneural`), in both `_harness` and `t01`. A scan of the real 280-file payload for this project's own terms found `_ProjectMAPPER`, `_UsefulHelperSCRIPTS`, `_NoStringsPDF` and a builder identity. Self-hosting evidence is superseded **Two retained `t01` assertions carry declared PARTIAL coverage** and are printed as `[PARTIAL]` by `gates/run.py`: (1) the predecessor sentinel set is incomplete and cannot detect this project's own predecessors; (2) the payload fixture is materialised by `tools/sidecar_install`, a legacy runtime tool that is a fixture producer only, conferring no product authority and proving nothing about canonical installation. Neither contributes to closing E11 |
| E12 | Installed sidecar removable without trace | partial | vend clean; removal untested |
| E13 | Governance cartridge installs optionally and blank | **not started** | Charter §5.8 states the invariant: enabling it must not expand ownership into target-owned content. Wiring is `P-install-packaging` |

**Three met, four partial, six not started.** Down from five met, and the two losses
are corrections rather than regressions: E8 and E11 were measured against wordings
that did not describe the product. Neither was ever true in the sense now stated.

**A green gate suite is not a complete scoreboard.** Two `t01` assertions are
retained as useful tripwires with **declared partial coverage**; the runner prints
them as `[PARTIAL]` beneath the verdict, and `gates/t05` asserts that it does. A
tripwire that fires is information; a deleted tripwire is nothing; a partial sentinel
wearing the label of a comprehensive proof is the false green this project keeps
finding.

### Standing practices added since T0

- **Verify from a fresh clone, not the working tree** (0007). A suite run against
  the tree that developed it cannot see a missing build step.
- **Gates must exercise a real consumer entrance** appropriate to the outcome
  (protocol rule 8, after T2's presence bug; generalised at T5 to cover governance
  surfaces, build artifacts and the setup application, so no tranche needs an
  informal exception).
- **Windows confirmation at each tranche close.** `tkinter` and `ollama` are absent
  from the sandbox, so 8 tests skip here; Windows is the authority for a zero-skip
  run. Two tranches closed without one and lint had a two-error backlog waiting.
- **Hazards raised at declaration become gate assertions**, not scheduled work.
- **The discovery pass runs at every close** (protocol §3.4, after 0014). The gate
  answers *did this do what was claimed*; only the discovery pass answers *what else
  is true*. Its first run found three tests failing in the default configuration.
- **The operator approves; the builder does not close its own work** (BCC §2.8
  step 12, after 0015). A tranche sits in **awaiting approval** until then. T1–T4
  were closed on the builder's own account and nothing else.
- **One authority per normative fact** (`BCC-ONE-AUTHORITY`, after T5). Consumers,
  generated surfaces and verifiers are permitted; a second hand-maintained copy is
  not, even when the copies agree.
- **Historical evidence is immutable; active proof is current** (protocol §5.1).
  A parked tranche's journal is never rewritten, but its live assertions may be
  surgically retired by an operator-approved superseding tranche, with provenance.
- **Verify in the default configuration, and record the configuration** (0014). A
  green suite means the assertions passed *under the settings you used*. Every
  verification path this project had was setting the one variable that hid the bug.
- **Census before designing** (T6, and again in T8's mutation signal). Three of nine
  "install entrances" turned out to be docstrings; eight target-writing tools turned
  out to report their paths in eight different shapes. Both censuses changed the
  design, and neither cost more than an hour.
- **Attempt end-to-end before concluding a capability gap** (2026-08-14, C1 rule 1).
  A missing capability was reported on the strength of a symbol name the model had
  invented. Querying the real name worked perfectly. **A tool that refuses a bad
  input is not a tool with a gap.**

### Where the `lint` tool sits

Deliberately **unscheduled**, not forgotten. The raw command is now reachable via
`project_run` and asserted at gate level, so the enforcement hole is closed; what
the tool would add is ergonomics — structured findings, Observe authority,
manifest-derived scope, honest unavailability. It earns a slot when a tranche
needs it, rather than displacing product work now.

---

## Sequence

| # | Tranche | Proves |
| --- | --- | --- |
| T0 | Foundation and Reset | **CLOSED** — a blank, unified project with one authority |
| T1 | One Ship Manifest | One declared ship manifest; a payload containing only the product. **Self-hosting assertions superseded by T5** |
| T2 | Ledger and Presence | The seam contract exists in code |
| T3 | Live Channel | E6a, E6b |
| T4 | Cancellation and Progress | Long work is observable and stoppable |
| ~~T5a~~ | ~~One Surface: Observe and Select~~ | **WITHDRAWN** 2026-08-09 — see below |
| T5 | Ownership and Distribution Model | **CLOSED 2026-08-09** — one authority per normative fact; a stated deployment topology |
| T6 | Instance Identity and the Installation Core | **CLOSED 2026-08-14** (0026 → 0027 → reopened 0028 → **re-parked 0031**) — one instance bound to one target, knowing its identity, root and state, surviving relocation **and update**, supplying canonical context to the runtime. 27 gate assertions |
| — | ***convergence phase begins here*** | |
| — | **Application Absorption Audit** (C1b) | *diagnostic, not a tranche.* What `apps/` actually owns, which primitives already provide it, what should become a chain, the safest retirement order, and whether T7 needs any live app |
| T7 | Shared Project Awareness Prototype | **CLOSED 2026-08-19** (0036) — one compact evidence-backed orientation, persisted against the instance, same revision to human and agent. 40/40; measured reduction **133,477 B → 2,343 B (0.018)** on a real target; revision content-anchored, move-stable and write-once; handles round-trip; drill-down recovers the evidence actually used; freshness projected at read time |
| T8 | Governed Work Loop Prototype | **DECLARED, gate red 30/48** (0037, strengthened 0038) — awareness → impact → `read_file` → preview → diff → witness-bound approval → Apply → measured changed paths → `test`/`lint` verification → refresh. Opens with **three safety preconditions**: `patch`'s absent write declaration, governance failing open on Apply, and uninterpretable tool output reported as success |
| — | **Closure gate 1: PARITY certification** | every retained donor product reproduced through the common bench, and the suite still passes **with the parts bin absent** |
| — | **Closure gate 2: RELEASE certification** | a release artifact from a clean clone installs and completes the whole walk on a clean machine, both platforms |
| **STOP** | **Prototype stop / dogfood** | Architectural development halts. See below |

**The finish line is finite and this is all of it.** T6's bounded repair, one audit,
two tranches, **two closure gates**, then stop. **No T9/T10 architecture is created for
the closure gates** — a red closure gate is fixed by repairing the specific red thing
and re-running it, not by scheduling a tranche.

*Rescoped 2026-08-18.* STOP previously meant "enough product to begin dogfooding", with
chains, `apps/` retirement and packaging all sitting **after** it. Under the operator's
stronger definition — a shippable prototype that replaces what motivated it — those are
proof obligations, not future features, so they moved in front.

**Standing sequencing instruction, operator, 2026-08-14.** The alignment is complete
and does not reopen. T6's repairs are discharged (0031). **The next thing is C1b** —
inspect, classify, identify duplication, determine what T7 touches, **implement
nothing** — and T7 is declared from its table. No further documentation sweep,
codebase audit, architecture review, capability census or roadmap is required before
proceeding; each would push the STOP farther away without resolving a demonstrated
blocker.

Ordering rationale up to T6: safety before capability (T1 precedes everything that
acts); the seam contract before the surface that displays it (T2-T4 precede any
surface); **the ownership model before anything that depends on where a boundary
falls** (T5 precedes the rest); **identity before awareness**, because awareness must
belong to an instance rather than to an absolute path (T6 precedes T7).

Ordering rationale from T7: **understanding before transformation.** T8's impact
inspection and post-Apply verification both consume what T7 composes, and T7's
staleness refresh is the last step of T8's loop. Building them in the other order
would mean designing the change loop against an orientation that does not exist yet.

### Post-STOP candidates — recorded, NOT SCHEDULED

These were pre-planned tranche bodies (formerly T7-T10) written before the
convergence phase. They are retained below under `P-` identifiers so nothing is lost,
and **deliberately unscheduled**: pre-planning them again would violate C1. They
return only if dogfooding demonstrates a concrete blocker, or after the prototype
stop.

| | Was | Proves |
| --- | --- | --- |
| `P-one-surface` | (provisional) | E3 |
| `P-contracts` | (provisional) | Ten daily-driver contracts exist |
| `P-chains` | T7 | E7 |
| `P-retire-apps` | T8 | One extension shape, not two |
| `P-install-packaging` | T9 | E1, E2, E4, E13 — includes the **canonical payload assembler**, the one piece of deferred T6 lifecycle work |
| `P-closure` | T10 | E8, E9, E10 |

### T5a - withdrawn

Declared in journal 0017, **withdrawn** the same day in 0019, never implemented. Not
a §5.2 reopening: it was never parked.

The operator's deployment-topology correction made two of its commitments wrong. It
named `installer_view` in the runtime shell's regression set — setup UI belongs to
`SIDECAR:SETUP-DISTRIBUTION` — and it inherited T5b's *"every registered tool
reachable from the shell"*, which with `sidecar_install` registered would have forced
the installed instance to expose *install another sidecar* as runtime capability.

Its gate is preserved at `gates/_deferred/t05a_observe_select.py.deferred`, out of
active discovery, with a README separating salvageable assertions from superseded
assumptions. Most of it returns when One Surface is redeclared.

### Superseded active proof

Under `TRANCHE_PROTOCOL.md` §5.1. Historical evidence is immutable; active
cumulative proof describes current architecture.

| Old assertion | Why retired | Replacement | Superseded by | Evidence |
| --- | --- | --- | --- | --- |
| `t01` — *"the manifest itself ships"* | premise was that a vended sidecar must vend; `instance -> instance` is not a product requirement | positive install manifest owns membership (`SIDECAR:INSTALLABLE-PAYLOAD`) — **owed by the payload tranche** | T5, operator decision 2026-08-09 | `gates/_superseded/t01_self_hosting.py.superseded`; history in 0008 |
| `t01` — *"the payload can reproduce itself exactly (**self-hosting**)"* | same premise | conformance proven against the **built payload** from the assembler, not a runtime tool copying the source tree — **owed by the payload tranche** | T5, operator decision 2026-08-09 | same |

**Census:** all 22 `t01` assertions were examined; two were retired. Everything else
remains active and unchanged.

---

## T0 — Foundation and Reset

**Outcome.** One authority, one numbering, no inherited memory.

**Work.** Charter, protocol and plan agreed. Superseded documents and competing
plans archived. Memory surfaces cleared. Git re-initialized with the foundation
as commit #1. Stale `TRANCHE:` and `STATUS: DONE` headers stripped from toolkit
source, with provenance preserved.

**Gate — `gates/t00_foundation.py`**

- `.bcc/` contains exactly: the BCC, `CHARTER.md`, `TRANCHE_PROTOCOL.md`,
  `TRANCHE_PLAN.md`, `evidence/`
- no file outside the archive contains a `TRANCHE:` header
- no `STATUS: DONE` remains in toolkit source
- `_docs/AppJOURNAL/` contains `0001` and nothing earlier
- `tool-list` returns the expected count
- no tracked file matches the secret patterns
- `git log` has exactly one commit on `main`

**Non-goals.** No behavior change. No GUI. No chains.

---

## T1 — One Ship Manifest · DECLARED

**Note on numbering.** T1 originally read *Explicit Target and Root Safety*. That
work was pulled forward into T0: collapsing the sidecar to the repository root
exposed the defect live, so root resolution was rewritten and verified there. The
slot is reused rather than renumbered; T2–T10 are unchanged.

**Outcome.** Exactly one declared description of what the sidecar ships, consumed
by every place that needs it — and a vend that provably contains only the sidecar,
carrying none of its own history.

**Why now.** Five separate defects trace to this being undeclared. The ship
boundary used to be the nested `toolkit/` folder; collapsing it erased an implicit
rule that four different mechanisms had each been relying on. Each was repaired
individually in journal 0003. Convergence is the actual fix.

The four current descriptions:

| Consumer | Where |
| --- | --- |
| Harness install | `_harness/harness.py::_PAYLOAD_EXCLUDE` |
| Vend / installer | `tools/vendor_export/cli.py::EXCLUDE_DIRS`, `CLEAN_APP_STRIP` |
| Lint scope | `ruff.toml::extend-exclude` |
| Test scopes | `tests/test_smoke.py` — two independent sets |

**Work.**

1. Declare the manifest once, in one module, as the single source of truth —
   **with named categories, not one flat set.** `CLEAN_APP_STRIP` currently holds
   four unrelated reasons for exclusion in a single list, which is why the
   `packaging/` question looked open when it was not:

   | Category | Meaning | Members |
   | --- | --- | --- |
   | `NEVER_SHIP` | development scaffolding and this project's history; absent from **both** deliverables | `.bcc`, `_docs`, `gates`, `_trash`, `_harness`, parts bin, `requirements-dev.txt`, test scratch |
   | `REGENERABLE` | recreated on use; excluded because stale, not secret | `_state`, `_artifacts`, `_exports`, `_tmp_sqlite_probe`, caches |
   | `INSTALLER_ONLY` | **ships as deliverable #1, beside the payload, never inside it** | `packaging/` |
   | `EXPORT_SUBSTITUTED` | replaced at export time by a tool-focused version | `tools/vendor_export/clean_app_docs` |

   The payload exclusion set is then *derived* as the union. Keeping the reasons
   named is the point: a flat list cannot distinguish "junk", "must never exist
   in a target", and "belongs to the other half of the product". Under the flat
   list, `packaging/` sat beside `_trash` — inviting exactly the wrong cleanup.
2. Derive `vendor_export`'s exclusion sets from it.
3. Derive the harness's `_PAYLOAD_EXCLUDE` from it.
4. Derive both test scoping sets from it.
5. `ruff.toml` is static TOML and cannot import — so the **gate** asserts it
   remains consistent with the manifest rather than silently drifting.
6. Ship a minimal payload `.gitignore` covering the sidecar's own `_state`,
   `_artifacts` and `logs` — not the development one, which names the parts bin
   and harness.
7. **Reclassify `packaging/` as `INSTALLER_ONLY`, and gate deliverable #1.**

   The question raised at declaration — *is stripping `packaging/` correct when
   the installer is deliverable #1?* — is answered by the installer itself:

   > `DOMAIN: packaging (ships NEXT TO the product zip, not inside it)`

   It resolves a sibling `useful-helpers-toolkit/` folder or zip, and is
   stdlib-only so it runs on a bare machine. The two-deliverable split is already
   built; stripping it from the payload is correct and must stay.

   What is wrong is that this is invisible. `packaging/` sits in a flat exclusion
   list beside `_trash` and `_state`, indistinguishable from disposable material,
   and the reasoning survives only in a file header. So:

   - move it to `INSTALLER_ONLY`, so the manifest states *why* it is excluded;
   - assert it is **absent from the payload** — a payload containing its own
     installer is circular and dead weight;
   - assert it is **present and intact in the repository**, so a future cleanup
     cannot mistake deliverable #1 for scaffolding;
   - apply the **E11 blank check to the installer too**. It is a shipped artifact
     and currently no check looks at it at all. It must carry no journal, no
     evidence, no build-machine path and no predecessor name, exactly as the
     payload must not.
8. Implement charter condition **E11** — vends blank.

**Gate — `gates/t01_ship_manifest.py`**

- one manifest module exists and declares the payload boundary **by named
  category**, so each exclusion states its reason
- every consumer derives from it; no independent literal exclusion lists remain
- `packaging/` is classified `INSTALLER_ONLY`: absent from the payload, present
  and intact in the repository as deliverable #1
- the installer passes the same blank check as the payload — no journal,
  evidence, build-machine path or predecessor name
- `ruff.toml`'s excludes are consistent with the manifest
- a real vend into a scratch directory contains **no** `_harness`, `.bcc`,
  `_docs`, `gates`, `_trash`, parts bin, or nested `.useful-helpers`
- the vended payload carries the minimal ignore file, not the development one
- **E11:** the vend contains no journal entry, event log, evidence file,
  development document, `.git`, build-machine absolute path, or predecessor
  project name
- vended file count stays within a declared bound — the regression signal that
  caught 4,009 files shipping where 275 belong

**Non-goals.** No UI work. No chains. No ledger or presence work. No new tools.
No change to root resolution — that closed in T0.

**Stop condition.** `python gates/run.py` green, including T0's gate, on a host
with normal delete semantics.

---

## T2 — Ledger and Presence

**Outcome.** The seam contract exists in code: two channels, one seam.

**Work.** A read API over the ledger. A presence store holding current state
with a change tick, ephemeral and dropped on restart. Confirmation becomes a
distinct, attributable ledger event. Client attribution on every entry.

**Gate — `gates/t02_seam_contract.py`**

- ledger is readable and ordered; entries carry client attribution
- an approve and a refuse each produce a distinct confirmation event
- presence returns current state and never persists across restart
- no UI-state change appears in the ledger
- a run of N tool calls grows the ledger by N entries and presence by zero

**Non-goals.** No transport. No GUI rendering.

---

## T3 — Live Channel · NARROWED

**Scope corrected after T2.** This tranche originally claimed **E6a and E6b**.
**E6b is already met**: presence answers "what is true now", survives a CLI call,
and is readable cross-process through the state root. It landed with T2.

What remains is E6a alone, and it is one question, not four:

> **How does a change announce itself?**

**Outcome.** A client learns that the other party acted, without being told to
look. **E6a.**

**Work.** Publish ledger appends and presence changes such that a reader notices
them. One in-process client and one out-of-process client, both observing the
same events.

**Gate — `gates/t03_live_channel.py`**

- an action by client A is observed by client B without restart or manual refresh
- an out-of-process observer sees an in-process action, and the reverse
- a dropped or dead observer does not block, stall, or corrupt the seam
- presence loss does not affect ledger integrity
- observation adds no writes to the target

**Non-goals.** No GUI event view — that is T5, and building it here would smuggle
UI work into a backend tranche. No derived visible-state (charter §6.4 level 2).
No multi-writer presence.

### The concurrency decision, made at declaration

Recorded here rather than discovered later, per the practice that worked in T2.

**Single-writer, polled reads.** Presence has exactly one writer — whoever owns
the session — and readers poll a monotonic tick.

This makes the read-modify-write race carried from T2 **unreachable rather than
handled**: no lock, no daemon, no port, no lifecycle to supervise, and it works
cross-process on any filesystem. The ledger is already append-only with SQLite
managing concurrent appends.

Honest costs, accepted: latency equals the poll interval, and it does not cross
machines. Both are acceptable for a local sidecar, and a polled interface can sit
unchanged in front of a socket if one is ever justified.

**The interval will be measured, not guessed.** Presence read latency is to be
timed against the real tree before a number is chosen — the same lesson as the
per-event migration cost, which was invisible until measured.

---

## T4 — Cancellation and Progress

**Outcome.** Long-running work is observable while it runs and can be stopped.

**Work.** Replace the blocking dispatch with a cancellable one. Per-call timeout
replacing the fixed 120 s. Progress events on the live channel. Redact absolute
host paths from diagnostics.

**Gate — `gates/t04_cancellation.py`**

- a long operation is cancelled and the child process is reaped
- progress is observable before completion
- a per-call timeout overrides the default
- no diagnostic surfaced to a client contains an absolute host path

**Non-goals.** No GUI controls; the backend must be testable headlessly first.

---

## T5 — One Surface · SPLIT INTO T5a AND T5b

**Why split.** Every tranche so far has been a handful of files. This one means
unifying four Tk views into an explorer-first shell with explorer, context panel,
tool workspace and event view — the actual product, and larger than T2, T3 and T4
combined. An outsized tranche is where clean parking breaks down: the gate becomes a
wish, scope creeps, and "mostly done" reappears.

Two closable outcomes instead of one open-ended one. The split follows the product's
own loop — **Observe → Select**, then **Operate → Verify**.

### T5a — Observe and Select

**Outcome.** A single shell opens a project, browses it, and inspects what is
selected. Browse selection and operation inclusion are separate state domains, and
clicking a file authorises nothing.

**Gate.** One window; project-open flow; explorer populates; browse selection and
inclusion are visibly distinct and independently maintained; context renders for a
file and a folder; rescan; clean startup and shutdown; presence reflects the current
selection so an agent can see what the operator is looking at.

**Non-goals.** No tool execution. No event view.

### T5b — Operate and Verify

**Outcome.** Every tool and chain is reachable from that shell, and the live channel
becomes visible. **E3.**

**Gate.** Every registered tool and chain reachable from one surface; no capability
needs a second window; operations show progress and can be cancelled from the UI;
the event view renders ledger and presence live; a GUI action and an agent action are
indistinguishable in that view except by their `client`.

**Non-goals.** No new capability — only reaching what already exists.

### Shared material for both halves

**What is being unified.** `registry_view`, `mapper_view`, `planner_view` and
`installer_view` become one shell: explorer, context, tool workspace, event view.
The four are kept as a running regression reference until T5b retires them — a
second implementation that still works is the cheapest differential available.

**Already built.** `src/lib/theme.py`.

**UX intent**, from the `_UsefulHelperScriptsMENU` filedump: `minsize(900, 600)`,
double-click to launch, mousewheel bound on every scrollable, non-truncating button
rows.

**Controller extraction comes first.** All four views repeat one pattern — worker
thread, queue, `after()` pump. Extracting that once, before any shell exists, keeps
the Tk widgets thin enough to be testable and stops the pattern being copied a fifth
time.

---


## T6 — the reopening, discharged

Declared in 0028, re-parked in 0031. Two defects, gate-first, seen red before green,
then certified against the whole established path. Kept here because the **acceptance
standards** below are now parked evidence and must stay green.

**Defect 1 — acceptance standard.** An update over a manifest that is present but
broken must **fail loudly**. The installer must not absorb `InstanceError` into a
`None` that `create()` then reads as *"mint a new identity."*

**Defect 2 — acceptance standard**, stated by the operator and stronger than the
obvious one:

> **A failed update must not make the installed instance less recoverable than it was
> before the update began.**

*"Do not lose `_state`"* is the weaker claim and would be satisfied by a run that
preserved the journal while leaving the instance unstartable, or by one that preserved
nothing because it never reached the point of moving it. Recoverability is the property
a user actually has: whatever position a failed update leaves them in, it is at least
as good as the position they were in when they started it. That is what the gate
asserts.

Both gates **were seen to fail** against the unrepaired installer before the fix
(protocol §5.1a): 24 pre-existing assertions passed, all three new ones failed, and
27/27 passed afterwards. A check for an absent condition that has never been observed
failing is not evidence.

**Where they were run matters.** `gates/t06` skips its entire install half on a
filesystem that denies `unlink` — honestly and with a stated reason, but it means every
`t06 PASS` recorded on the development mount exercised only the eight static
assertions. Both the red and the green run were performed on real disk. Windows CI
remains the authority.

---

## T7 — Shared Project Awareness Prototype · **PARKED 2026-08-19** (0033 → 0035 → 0036)

**Outcome.** Existing deterministic tools are composed into **one compact,
evidence-backed current orientation** of the bound target, persisted against the
instance, and exposed as the **same revision** to human and MCP agent.

**T7 is also the first proof of the tool-chain architecture** (Charter §1.4). It must
demonstrate that Useful Helpers can understand a project **without an application
layer**:

```text
canonical target -> orientation chain -> deterministic tools -> compact observations
                 -> one persisted awareness revision -> human projection / MCP projection
```

**Walk steps advanced (Charter §3.3):** 6, 7, 8, and the awareness half of 13.
It stops before target mutation — that is T8.

**Contributor selection is evidence-driven, not hardcoded.** The `_theCELL` set below
is what a *Python-rich* target demonstrated. Domain, cartridge and scope evidence
choose the contributors: a records target and an empty folder use different
observations and share the same envelope. A fixed universal pipeline would be the
software ontology C4 forbids.

### The minimum observation set, from measurement not invention

Do not begin by designing a large Project Awareness schema. Begin from what the
`_theCELL` dogfood run actually demonstrated was necessary and sufficient:

| Contributor | Projection used | Raw size returned |
| --- | --- | --- |
| `attach` | whole | 6.3 KB |
| `report` | `summary` only | 24.5 KB |
| `import_graph` | hotspots / edges / cycles / root counts | 9.5 KB |
| `dead_code` | `summary` only | 24.9 KB |
| `sqlite_inspect` | when databases exist | 5.1 KB |

Five calls, ~46 KB raw, and between them they already revealed: project and domain
classification, file and subsystem shape, entrypoints, class/function/symbol scale,
architectural hub modules, dependency structure, plugin and microservice patterns,
database schemas, and the map's own limits.

Measured as **redundant for orientation** and therefore not contributors:
`file_tree` (10 KB, subsumed), `command_profile` (0.5 KB — belongs to T8's
verification selection, not to orientation), `symbol_graph summarize` (2.4 KB —
`symbol_graph` is a drill-down instrument, not an orientation contributor).

C2 applies: the composition reads the `summary` projection; the full envelope is
reachable only on request.

### The awareness envelope — small and universal

The envelope is shared; the findings are not. A Python application, a PDF archive
and an empty directory need the **same envelope and the same honesty**, not the same
ontology (C4).

| Field | Meaning |
| --- | --- |
| awareness revision id | what "the same awareness" identifies |
| instance identity | the T6 UUID — awareness belongs to an instance, never to an absolute path |
| observed target / scope | what was looked at |
| observation time | when |
| compact findings | heterogeneous, domain-shaped, small |
| canonical handles | C3 — machine identifiers beside readable labels |
| evidence / provenance refs | which contributor produced which finding |
| limitations / unknowns | what this map does **not** know |
| freshness / staleness | whether it still describes reality |

**This is composition, not another mapping engine** (C1 rules 2 and 3). Project
Mapper stays a snapshot compiler; `attach` composes.

### Gate — `gates/t07_shared_awareness.py` · **GREEN 40/40** (0036)

*At declaration (0033) it read **33 assertions: 3 pass, 30 fail** — the three passes
being pre-existing invariants under protocol §5.1a. It grew to 40 as three further
semantics were closed, and is green on Windows in the parked record. The declaration
figures are kept because red-before-green is the evidence, not a footnote.*

Four properties are stated **mechanically**, in the gate, because each has a history of
degrading into a green assertion whose meaning drifted:

| | |
| --- | --- |
| context reduction | `MAX_PROJECTION_RATIO = 0.25` **and** `MAX_PROJECTION_BYTES = 8192`, declared in one place. The ceiling exists because a ratio alone is satisfiable by an empty target. Changing it is a deliberate act with a reason |
| revision identity | `instance` (who am I) + `revision` (what did I know) + `evidence_fingerprint` (what observed reality produced it). Same target → same fingerprint; one file added → different fingerprint |
| canonical handles | every handle **must be accepted by the tool that owns it and resolve back to the entity it names**. A handle without an owning tool is decorative, not canonical |
| drill-down | **the evidence ACTUALLY USED for that revision** — a retrievable, content-addressed `evidence_id` captured at observation time. *A re-runnable invocation is NOT sufficient, and this row said it was until 2026-08-18: re-running observes today's target, answering "what did revision X know?" with "what would I know today?", which makes a persisted revision unfalsifiable. The gate has enforced the strict rule since increment 3; this text described the abandoned one.* |

The gate also carries the narrow `.git*` prune regression from 0032: `.git` excluded,
`.github` **not** excluded. One distinction, not an exclusion-subsystem redesign.

**Three further semantics closed 2026-08-18**, each red before its repair and each
mutation-confirmed afterwards:

| | |
| --- | --- |
| a stale re-engagement reports awareness as stale | the envelope was written while
fresh and kept saying so, so one response could report outer `staleness: true` and
`freshness.stale: false` together. Freshness is now projected at read time; the
revision id is deliberately untouched, because recomposing on every attach is the
cost persistence exists to avoid |
| an existing revision record is not rewritten | `_persist` rewrote
`<revision>.json` every observation, so the same id named a moving record. Content-
addressed records are **write-once**; re-observing a known state re-points `current` |
| a contributor whose evidence capture fails is not promoted as evidence-backed |
found by **failure injection** — no ordinary run reaches it. An observation that
cannot be captured is not evidence-backed knowledge, and `limitations` says so |

Original declaration text follows.

Sketched assertions, to be made executable and exercised through a real consumer
entrance (protocol rule 8) at declaration:

- one persisted awareness revision exists, keyed to the instance UUID, and survives
  a restart
- the human projection and the MCP projection **mechanically identify the same
  revision id** — not "look similar"
- the agent projection carries canonical handles for every addressable object it
  names; a handle it emits round-trips through the tool that owns it
- the default projection is bounded and materially smaller than the sum of its
  contributors' raw output; the drill-down projection returns the full existing tool
  output unchanged
- awareness declares its own limitations, and the empty-target case (C4-C) produces a
  **truthful thin map**, not an error and not a software ontology
- awareness for a target with no databases omits the SQLite contributor and says so
- moving the instance with its target preserves the awareness revision (T6 property,
  re-asserted here because awareness is the first durable consumer of identity)

Two further assertions, from the product shape. **The first is stated as an invariant,
deliberately, so it cannot harden into ceremony:**

- **T7's understanding is produced by canonical tools through the common governed
  composition path — not through a private application or backend.**

  Whether the final composition is one playbook, several small playbooks selected by
  evidence, or an existing front-door operation invoking them is decided by
  **implementation evidence**, not declared here. What is forbidden is new private
  orchestration inside `attach`; what is *not* required is manufacturing a playbook
  file to prove a point.
- **T7 completes with no dependency on specialised application architecture.** If
  awareness needs `projectmapper`'s *application* shape, the tranche has not proven
  what it claims. Depending on `projectmapper` as an ordinary registered tool is not a
  violation — see the STOP assertion on semantics versus folder purity.

**T7 is also partly a reduction pass.** Where it touches a responsibility the audit
marked `replace`, it discharges that verdict by calling the canonical tool. Where it
does not touch one, it leaves it alone. Reduction is a consequence of the work, never
a separate rewrite.

**Non-goals.** No target mutation. No change-driven selective refresh. No One
Surface. No "Project Awareness App". No new tool unless C1 rule 1 is discharged. No
awareness ontology framework. No second chain engine (C1a.4). No net growth in
`attach`'s category-C mass.

**Stop condition.** Both projections resolve the same revision id on all three
acceptance targets, with no application-layer dependency, and the gate suite is green
on both platforms.

---

## T8 — Governed Work Loop Prototype · SKETCHED, NOT DECLARED

**Outcome.** A human or agent can move from **awareness → impact inspection →
preview/diff → approval → Apply → target-native verification → awareness refresh**
using existing tools and the existing governed seam.

**Walk steps advanced (Charter §3.3):** 9, 10, 11, 12.

### It is composition. The parts already exist.

Measured on `_theCELL`, 2026-08-14. Each row is a tool that already works.

| Step | Existing mechanism | Status |
| --- | --- | --- |
| impact inspection | `symbol_graph refs` | exact — resolves inbound edges to specific call sites with line numbers |
| proposed transformation | `read_file` → `edit` / `patch` preview | preview returns `result`, `written:false`, `apply_with`. **`source` is the source KIND (`"path"`/`"text"`), not the original content** — the before-state comes from `read_file` |
| reviewable before/after | existing `diff` tool | takes the text pair the preview already returns |
| governed mutation | same call with `apply:true` | returns `written:true` and `path` |
| attribution / audit | `event_log` | records client, authority, args_hash |
| what can be verified | `command_profile` | returns commands with a `kind` — `run`, `setup`, `test` |
| verification | `smoke_runner` / `project_run` | selected by `kind`, mechanically |
| reorientation | `attach` refresh + staleness | exists, coarse |

**T8 proves chains can transform as well as understand.** Same architecture, second
proof.

**Explicitly do not build:** a new diff engine, a new approval engine, a new
verification framework, a new project runner — nor a change-review application, a
verification application, a diff application, or an awareness-refresh application.
Each of those is **a chain over the bench** (C1 rules 1 and 2; C1a rules 1 and 2).

### The three seams that are genuinely missing — all composition, none new subsystems

1. **The preview does not offer its own diff.** `edit` stops at `replacements: 1`, so
   approving means approving *a count*. The real chain is `read_file` → `edit` preview
   → `diff {a_text: read.content, b_text: preview.result}` → `edit {apply:true}`. One
   more existing tool; still nothing new.

   ***CORRECTED 2026-08-19, and the error was fabricated rather than measured.*** This
   entry previously read *"`edit` returns both sides"* and proposed
   `diff {a_text: source, b_text: result}`, on the belief that `edit` returns the
   original text under `source`. **It does not.** `tools/edit/cli.py:39` sets
   `content, source = path.read_text(...), "path"` — `source` is the literal string
   `"path"` or `"text"`, the source KIND. The proposed chain would have diffed the word
   `"path"` against the new content.

   This is the `CellBackend` failure repeated in a *plan* rather than a query: an
   interface asserted from plausibility instead of read from the code, then carried
   into journal 0032 and this section, where it survived a closeout, a park and two
   reviews before an outside reader opened the source. **A gate written against it
   would have tested an imagined product.** The lesson is not "read more carefully" —
   it is that a claimed interface belongs in the same category as a claimed capability,
   and C1 rule 1 already covers it: attempt it before asserting it.
2. **Verification is selectable but not selected.** `kind` is the selector. On
   `_theCELL` it yields only `run_bat` and `setup_env` — **no test command exists in
   that target**. The correct behaviour is to say so, not to invent one. Truthful
   degradation, exactly as C4 requires.
3. **Apply does not mark awareness stale.** See the census below; the datum exists
   and the connection does not.

### The mutation signal — settled by census, 2026-08-14

Censused before designing, as required. Findings:

- **8 tools declare `writes: target`**; `patch` writes to a target path while
  declaring `writes: toolkit` (a misdeclaration, recorded in the backlog).
- Per-tool result fields are **inconsistent**: `path` (`write_file`, `edit`,
  `patch`), `results[].path` + `.dest` (`fs_op`), `written[]` relative to `base`
  (`scaffold_project`), `db` (`sqlite_exec`), `venv` (`dep_install`), nested
  `trail[].base` (`plan`), and **nothing at all** for `project_run`, whose scope is
  an arbitrary shell command.
- Normalising those eight shapes would be **exactly the bespoke per-tool
  architecture C1 rule 2 forbids**, and would still be blind to `project_run`.

**The seam already computes the answer.** `src/core/invoke.py` holds
`_target_manifest()` (stat-only walk of the target, excluding the instance root and
regenerable noise, bounded at 20 000 files with an honest `complete=False`) and
`_manifest_diff()` (added, removed, or changed by mtime/size). Today `_guard_applies`
runs it **only for Observe tools** — that is, only for the tools that must change
nothing. Inverting that gate for governed Apply yields `changed_paths` for **every**
target writer including `project_run`, tool-agnostically, with no per-tool code.

So: `changed_paths` is a **seam measurement**, and any per-tool `path` field is a
*claim* to be checked against it. The census's real value was showing that trusting
the claims would have been the wrong design.

### Gate — `gates/t08_governed_loop.py` *(written at declaration, before implementation)*

- an `edit` preview yields a human-readable unified diff through the **existing**
  `diff` tool, with no new tool registered
- `apply:true` after a reviewed diff produces `written:true`, and the ledger carries
  an attributable entry naming the client
- the seam reports `changed_paths` for a governed Apply, measured not declared, and
  `project_run` — which reports no path of its own — is covered by it
- a tool whose declared path disagrees with the seam measurement is surfaced, not
  silently reconciled
- verification is selected **mechanically** from `command_profile`'s `kind`; a target
  with no test command produces an honest *"this target supplies no verification"*,
  not a fabricated one
- awareness reports itself stale after an Apply that touched a path the awareness
  covers, and refreshes to the new reality
- the loop completes on acceptance target A, and degrades truthfully on B and C

**Non-goals.** No new diff/approval/verification/runner subsystem. No incremental or
semantic invalidation (C1 rule 6) — coarse staleness only. No One Surface.

**Stop condition.** The full loop runs end to end on target A and degrades honestly
on B and C, green on both platforms.

---

## Prototype STOP

**This is the point of the plan.** Without it, this project continues growing.

The prototype is done when a real user can:

```text
 1. install Useful Helpers into a target
 2. launch it from the target root
 3. receive a useful compact understanding of that target
 4. connect an external agent over MCP
 5. know that human and agent share the same current awareness
 6. drill into project details using existing tools
 7. assess the impact of a proposed change
 8. see an actual diff before approval
 9. deliberately Apply the change
10. verify it using meaningful target-provided checks when available
11. audit what happened
12. refresh / re-engage and see the new reality
13. reproduce every RETAINED useful product of the donor apps through the common
    bench, with no runtime or reference dependency on the parts bin
14. do all of it with NO specialised live application architecture — any surviving
    atomic capability, such as ProjectMapper, re-homed as an ordinary tool
15. do all of it from a RELEASE ARTIFACT built from a clean clone, installed on a
    clean machine, without the development repository
```

### Steps 13-15 were added 2026-08-18, and they change what DONE means

The first twelve steps describe *"enough coherent product to stop architecture work and
begin dogfooding"*. That was the right bar when the danger was underbuilding.

The operator's definition is stronger:

> **A shippable prototype that actually replaces the useful products that motivated it,
> can be handed to someone else, and contains no known reason to keep developing it.**

Under the old wording the Plan could declare the prototype done while still saying *"we
have not proven the old workflows produce their outputs, we have not proven the thing
ships from a clean artifact, and `P-chains` will handle that someday."* **That is not
done.** So parity, parts-bin independence, application retirement and release
certification move **in front of** STOP rather than after it.

**This adds no architecture tranche.** They are closure gates, not build phases. A red
closure gate is fixed by repairing the specific red thing and re-running it.

### Closure gate 1 — PARITY CERTIFICATION *(after T8, before STOP)*

One matrix over the donor contracts already written in the reference material. **Three
valid outcomes, and "deferred" is not one of them:**

| outcome | meaning |
| --- | --- |
| **Retained — direct** | produced today by tool X |
| **Retained — composed** | produced by chain X → Y → Z through the existing playbook machinery |
| **Superseded** | the old product deliberately no longer exists, because capability X replaces its useful outcome |

For every **retained** row, a representative fixture goes through the **current common
runtime** and the documented useful output is asserted. **Product parity, not UI parity,
not code parity, not internal-architecture parity.**

And the assertion that makes it mean something: **run the parity suite with the parts
bin renamed or absent.** If it still passes, the ancestors have genuinely been absorbed.
That is the prototype-scale version of E9.

**Do not turn every donor into a chain.** If `projectmapper` already takes a target and
produces the complete useful snapshot, it is atomic: re-home it to `tools/`, drop the
`apps/` registry path, gate it, done. A chain is justified only where the user-facing
product is genuinely multi-step. Parity closure should *reduce* the live architecture
while proving more capability.

### Closure gate 2 — RELEASE CERTIFICATION *(before STOP)*

The question, stated as narrowly as it can be:

> **Can this repository become an artifact another machine installs and uses without the
> development checkout?**

**Use the existing payload and vend mechanism first.** Build a new assembler only if a
real release attempt demonstrates the existing one cannot produce a clean release. Do
not build the governance-cartridge UI, the positive-manifest assembler, or any other
feature merely because an earlier plan imagined it.

The walk: clean clone → release artifact → fresh Windows *and* Linux environment →
choose a code, records or empty target → install → documented launcher → `attach`
produces awareness → external MCP agent connects → registry reachable → parity products
work → the T8 change loop works → update preserves UUID and state → deleting an
untouched sidecar leaves target-owned content unchanged.

And inspect the distribution itself: no parts bin, no harness, no development journal,
no accumulated evidence or state, no source git history, no build-machine absolute path.

Shippable does **not** mean signed, MSI-packaged, auto-updating or app-store polished.
It means a genuine distributable product rather than *"run this from my dev checkout."*

### Two safety debts that do not survive to STOP

- ~~**`patch` declares `writes: toolkit` while writing to a target path**~~ (0034).
  **CLOSED in T8.** The field was ABSENT, not wrong, so `toolkit` was inferred from
  authority. Correcting it exposed a second defect: the derived catalog `attach` reads
  regenerated only when MISSING, so it kept publishing the old declaration forever.
  A census recorded 26 Apply tools with no `writes` field; only `patch` was corrected,
  because only `patch` is on T8's Apply path. The rest are a **manifest-truth pass**
  and are listed below rather than absorbed into this tranche.
- ~~**Malformed governance fails open, audibly**~~ (0034). **CLOSED in T8.** A broken
  configuration continues to permit **Observe** and no longer grants **Apply**:
  `policy.DEGRADED_CEILING = "Observe"`. *Fail closed for mutation, inspectable enough
  to diagnose.* Absent, unspecified and valid configurations are unchanged and stay
  permissive — only *present and unreadable* degrades, because only that is a broken
  control. Observe rather than Sandbox because a control in an unknown state must be
  safe under **every** value the operator might have intended, and Observe is the only
  such value.

The `dev_server_manager` → `command_profile` import and the absent layering policy are
**not** STOP blockers unless the parity or acceptance walk actually exercises them and
exposes a problem.

### The architectural STOP assertion

Twelve steps are the *experience*. This is the *shape*, and it is a stop condition in
its own right:

> **The complete acceptance walk must not require any specialised application layer.**
>
> Every step above must be reachable through common runtime + primitive tools + tool
> chains + human/MCP projections. **If deleting the transitional `apps/` layer would
> break the walk, convergence is not finished.**

**Read that as semantics and ownership, not folder purity.** The condition is *no
dependency on specialised application architecture* — not *the directory must become
empty at all costs*. If the surviving `projectmapper` turns out to be an ordinary
registered tool that happens to live under `apps/`, **re-homing it satisfies the
architecture** and the assertion is met. What must not survive is a private backend,
a private project model, a private state store or a private workflow engine that the
walk depends on.

Retirement is by demonstrated parity, never by decree. An application is removed when
*all* of these hold:

1. its useful behaviour is identified
2. the enduring tool or chain owner is named
3. the bench reproduces the behaviour the prototype needs
4. no active human or agent entrance depends on it
5. tests and gates exercise the replacement path
6. no document still presents it as product architecture

Reference copies may remain in the explicit archive area. The **live** product
progressively loses application-level duplication.

At that point:

> **STOP BUILDING THE ARCHITECTURE. DOGFOOD IT.**
>
> Use Useful Helpers to work on Useful Helpers. Use it on unrelated projects.
> Collect concrete friction. **Resume architectural work only for problems
> demonstrated during actual use.**

The end-state conditions E1-E13 are not abandoned; they are deferred until real use
says which of them the product actually needs next. A `P-` candidate that dogfooding
never asks for is a subsystem this project was right not to build.

---

## `P-chains` — Chains · **NOT SCHEDULED** (post-STOP)

**Outcome.** The daily drivers exist as chains and produce their documented
output. **E7.**

**Work.** Author a chain per retained daily driver over existing tools. Build
only the tools a chain genuinely lacks, justified against the contract.

**Gate — `gates/p_chains.py`** (identifier reserved; `t07` now belongs to Shared Project Awareness)

- each retained daily driver is reachable as a chain from the surface and from MCP
- each produces its documented output against a fixture
- no chain bypasses the seam
- every new tool added is manifest-declared and authority-bearing

**Non-goals.** No feature parity with the original UIs; parity is of capability.

---

## `P-retire-apps` — Retire `apps/` · **NOT SCHEDULED** (post-STOP)

**Outcome.** One extension shape: tools and chains.

**Work.** Convert `apps/projectmapper` to a chain. Remove `apps/` from the
registry path.

**Gate — `gates/p_retire_apps.py`** (identifier reserved; `t08` now belongs to the Governed Work Loop)

- no registered capability originates from `apps/`
- project-mapper capability is reachable as a chain and passes its T7 assertions
- registry count matches the expected post-retirement figure

---

## `P-install-packaging` — Install and Packaging · **NOT SCHEDULED** (post-STOP)

**Outcome.** The sidecar installs into an arbitrary directory on a clean machine,
is fully reachable by an agent, and carries its governance contract as an **optional
cartridge**. **E1, E2, E4, E13.**

**Work.** Install path, fresh-environment verification, offline behavior, MCP
surface parity, Windows verification, and the governance cartridge toggle.

**The cartridge toggle.** A checkbox in the installer UI. When enabled, a set of
fields appears carrying the `BCC-CONFIG` values as editable defaults —
`TARGET_PROJECT_ROOT`, `SIDECAR_ROOT`, `CONTRACT_PATH`, `JOURNAL_PATH` — as text
fields that accept a pasted path and are also settable by folder picker. Enabling it
adds `.bcc/BUILDER-CONSTRAINT-CONTRACT.md`, `.bcc/TRANCHE_PROTOCOL.md` and
`gates/run.py`, and nothing else. Membership is declared in `src/core/payload.py`
as `GOVERNANCE_CARTRIDGE`; the installer reads it rather than restating it.

**Gate — `gates/p_install.py`**

- installs into an empty scratch directory and `attach` returns a map
- `attach` succeeds on code, data-curation and records targets
- the MCP tool list equals the registry
- no network is required by any core capability
- the target contains no sidecar artifact after uninstall
- **toggle off:** no contract, protocol or gate runner is present in the target
- **toggle on:** all three are present, and the installed contract's `BCC-CONFIG`
  values resolve to the **new** target
- **toggle on, blank:** the installed contract contains no value, path, journal
  reference or tranche number belonging to this build. Asserted by content scan,
  not by trusting the substitution — the substitution is the thing under test
- `payload.cartridge_conflicts()` is empty, and the cartridge is at most
  `MAX_CARTRIDGE_FILES`

**Note.** Windows verification cannot be performed in the development sandbox
and requires an operator-run check.

---

## `P-closure` — Closure · **NOT SCHEDULED** (post-STOP)

**Outcome.** The project is provably done. **E8, E9, E10.**

**Work.** Delete the parts bin. Run the full suite. Path-scrub and secret audit.
Final journal closeout.

**Gate — `gates/p_closure.py`**

- the parts bin is absent and the entire gate suite passes
- no runtime module references an archived or reference path
- `.bcc/` and `_docs/` can be removed without affecting runtime
- precept guard passes; read-only prevention passes where the host supports it
- no document asserts a behavior without a check behind it

On a green `P-closure`, the project is **closed** per charter §4. That is the END STATE, not the prototype stop — the prototype stop comes first and is the near-term target.

---

## Deferred

- **Derived visible-state (presence level 2).** Charter §6.4. Built after T5,
  when a real surface exists to derive from. Not load-bearing for the end state.
- **Read-only mount prevention on Windows/macOS.** No known strategy; reports
  UNAVAILABLE with a reason.

## Capability Gap — `lint` · **NOT SCHEDULED** (convergence rule C1.1)

Recorded 2026-08-06. Raised by the operator after noticing the review pass was
using `grep` and `ast.parse` rather than the sidecar.

**The gap.** There is no lint tool and no syntax-validation tool. Confirmed
against the live registry: searching 95 tools for lint/style/format/syntax
returns nothing — the apparent hits are `blocking_call_scan` (an async-safety
scanner) and `provenance`, both false matches.

**Why it matters more than convenience.** The toolkit's own charter states the
measure: *every time an agent reaches past the sidecar for its own hands, the
sidecar has a gap.* Over this session the most frequently reached-past verb was
"does this file still parse" — run by hand as `ast.parse` and `compileall` after
almost every edit, outside the seam, unlogged and ungoverned. That is the
highest-frequency ungoverned action in the whole engagement.

Static analysis is well covered — `dead_code`, `complexity_score`,
`domain_boundary_audit`, `blocking_call_scan`, `import_graph`, `symbol_graph`,
`secret_audit` all answer *"is this code sound?"* Nothing answers the cheaper,
far more frequent *"is this valid, and does it meet the bar?"*

### Corollary gaps — all verified, all closed or eased by the same tool

1. **Syntax validation is the cheapest mode and should be first-class.**
   `ast.parse` per edited file is the fastest possible correctness signal and was
   used constantly by hand. A lint tool whose cheapest mode is "does it parse"
   removes the single largest ungoverned action.

2. **`command_profile` does not detect lint commands.** Verified: with
   `ruff.toml` sitting at the repository root, it detects `smoke`, `unittest`,
   `run_bat` and `setup_env` — and no lint command. A project carrying a linter
   config obviously has a lint command. Fixing detection would let `project_run`
   reach it *even before* a dedicated tool exists, and is a smaller change.

3. **Lint has exactly one path, and it is the wrong one.** `test_self_lint_clean`
   is the only enforcement of the style bar. It lives in the test suite, shells
   out to `ruff`, and **skips silently when ruff is absent** — which it is in the
   development sandbox. So the bar goes unenforced there and no gate notices. This
   violates the one-capability-one-governed-path rule the whole project is built
   on: lint is reachable only through a test.

4. **Gates cannot assert lint cleanliness.** They would need the tool. Today a
   gate can only reach it by invoking the entire suite.

5. **Unavailability is invisible.** Nine tests skip in the sandbox, one of them
   the lint check, and nothing surfaces *which* capability is unavailable or why.
   The tool must report `UNAVAILABLE` with a reason — the harness's honest-skip
   contract — rather than pass or vanish.

6. **Dev dependencies are undeclared to the tooling.** `requirements-dev.txt`
   exists but `dependency_check` reports only `declarations`/`envs`/`host` and
   does not distinguish dev from runtime. A lint tool needs to know its own
   dependency is declared but optional.

7. **`ruff.toml` scope is gate-enforced, not derived.** T1 could not make the lint
   config import the manifest, because TOML cannot import, so a gate asserts
   agreement instead. A lint tool owning the scope — taking it from
   `payload.FOREIGN` — would remove that entire class of drift and make the
   exclude list generated rather than hand-maintained. **This is the strongest
   synergy: the tool would delete a gate assertion rather than add one.**

8. **Windows pipe encoding must be handled.** A `cp1252` `UnicodeDecodeError`
   destroyed a lint failure message earlier today, reducing the assertion to
   `1 != 0` with nothing actionable. Any tool shelling to a linter must force
   utf-8 with replacement.

### Shape when built

Observe authority, `writes: none`, structured findings, scope derived from
`payload.FOREIGN`, honest `UNAVAILABLE` when the linter is absent, utf-8 forced,
and a `syntax_only` fast mode. Small, high-frequency, and it closes a hole this
session fell through repeatedly.

**Priority: none during convergence.** Retained as an analysis, not as work. The
hole it was filling is closed: the raw command is reachable through `project_run`,
lint is asserted at gate level, and CI runs it as its own step. What remains is
ergonomics. **C1 rule 1 governs it** — it earns a slot only if a T7/T8 end-to-end
attempt demonstrates that no existing tool supplies the capability. The section
heading previously read `PRIORITY` while its own closing paragraph read `Medium`;
that contradiction is what this correction removes.

---

## Backlog

| Item | Origin | Priority |
| --- | --- | --- |
| **`lint` tool** — see the capability gap above | Review pass, 2026-08-06 | **Not scheduled** — C1 rule 1 |
| `dependency_check` does not distinguish dev from runtime deps | Corollary 6 | Low — post-STOP |
| `VERSION` does not move when tools change | Charter §7.4 | Medium — `P-install-packaging` owns it |
| Precept-guard cost unmeasured on large targets | Charter §7.3 | **Medium — T8 touches it.** T8 reuses `_target_manifest` on the Apply path, so its cost stops being hypothetical. `_GUARD_MAX_FILES = 20000` with an honest `complete=False` is the existing bound; T8 must measure, not assume |
| `test_d1_p1` slow: `attach` re-maps ~18k files twice | 0004 | **Still open — T7 did NOT close it.** T7 avoided *adding* cost (re-engage reads the persisted revision rather than recomposing) but did not remove the existing double map. Recorded honestly rather than counted as collateral |
| **`patch` declares `writes: toolkit` but writes to a target path** | §11 census, 2026-08-14 | **High — T8 owns it.** A tool that mutates the target while declaring it does not is a hole in the precept guard's own gating. Found by census, not by failure |
| ~~**Malformed tool output fails OPEN at the seam**~~ | Charter §7.4, re-confirmed 2026-08-19 | **CLOSED in T8.** Three distinct seam failures now, each naming which case occurred, with `raw_stdout` preserved in every branch. The point is not that garbage is ugly: **exit 0 does not mean "did nothing"** — a tool can mutate the target and then fail to describe what it did, and calling that success is how an unreviewed change enters a target while the ledger records a clean run. The correct report is "outcome unknown", which a human can act on |
| **`edit` preview does not bind Apply to the reviewed state** — `apply_with` carries only `{"apply": true}`, so an approved diff against state A can land against state B if the file changes in between | 2026-08-19 review | **HIGH — T8 precondition.** Classic stale-preview/TOCTOU. Minimal close: preview returns a source SHA-256 and carries it in `apply_with`; Apply refuses when the current hash differs. Belongs in `edit`, not a framework |
| **`_instance_module` docstring and call order disagree** — it says the identity authority is loaded *"FROM THE PAYLOAD JUST INSTALLED"*, but the update path calls it before the copy and loads the **old** tree's copy | 0028, third finding | **Medium.** Reading an old manifest with the code that wrote it may well be correct; the point is that the comment and the behaviour cannot both be. Deliberately **out of scope** for the T6 reopening, which is bounded to two defects |
| ~~`docs-refresh` prints `_docs/TOOLS.md` while writing `docs/`~~ | T6 closeout | **CLOSED 0034 sweep.** The reported path is now DERIVED from where the write landed, so the one field a caller reads to find the output cannot name the wrong place again |
| ~~**`attach` cannot see `.github/` or any `.git*` directory**~~ | 0032 (C1b) | **CLOSED — T7 increment 1.** The prefix test was REMOVED rather than narrowed: `PRUNE` already contained `.git`, so it added nothing there and only swallowed siblings. Verified behaviourally — `_probe` now returns `.github/workflows/ci.yml` and still excludes `.git` |
| ~~**`report` declares a `modules` field its output omits**~~ | 0032 (C1b) | **CLOSED 0035** — the directory branch computed the structure, rendered it to prose and discarded it. Now returned as declared, which is what let awareness select module purposes without re-parsing markdown |
| **`report` now returns `modules` AND `markdown` — the same information twice** | 0035 | Low. Measured on `src/`: 15,675 B + 14,772 B = 30,577 B, roughly double the previous payload. Both fields are declared and both are consumed (`playbooks/ground_report.json` binds `@report.markdown`), so this is the cost of honouring the contract rather than a defect. Rendering markdown on request would remove it, but that is an API change and not T7's business |
| **No tool reports file modification time** | 0032 (C1b) | **ANSWERED by T7: no tool is needed.** `awareness_shared` never references `newest_mtime` — freshness is a projection over `attach`'s existing staleness signature, and the evidence fingerprint is content-anchored, so nothing in the composition wanted an mtime primitive. C1 rule 1 discharged the honest way: the end-to-end attempt demonstrated the gap was not real. `newest_mtime` stays front-door logic until a **second** consumer independently needs it |
| **`projectmapper` re-home** — `apps/` → `tools/`, then retire `apps/` and its registry scan path | 0032 (C1b) | Low — satisfies the STOP assertion by semantics; needs an operator decision, not urgent |
| **ProjectMapper snapshots are not self-reproducible** — `regenerate_command` records only `action`/`root`/`name`, and the manifest's `generation` block records the ordinary folder-exclusion set but NOT user `exclude_paths`, `out` or `markdown`. Verified 2026-08-19 against a real snapshot | **PARITY closure gate** | *Retained-product requirement:* a snapshot must preserve enough generation-selection metadata to reproduce the same capture scope — including user deselections and output forms — without reconstructing the invocation from memory. A portable self-describing artifact that cannot describe its own scope is not yet portable. **Not repaired during T8** |
| **ProjectMapper prunes ALL dot-directories unconditionally** — so a snapshot of this repository cannot capture `.bcc/`, which is normative product authority. Defensible for an ordinary user target; wrong for reviewing this repo's complete truth state | **PARITY closure gate** | Eventually: distinguish default-hidden dot infrastructure from explicitly includable dot folders, while ALWAYS hard-excluding `.git` and the installed sidecar **by identity**. **Not repaired during T8** |
| ~~**Should the governance ceiling fail open or closed?**~~ | 0034 | **ANSWERED in T8: closed for mutation.** The 0034 review deliberately fixed only the invisibility, on the grounds that a security posture is the operator's decision and not a review's. T8's declaration made that decision — a bench that can rewrite arbitrary target files must not read an unreadable mutation control as permission to mutate. The audibility work was the right first move: it is what made the posture question askable |
| **Manifest-truth pass: 26 Apply tools declare no `writes` field** — measured 2026-08-19 against 94 manifests; 8 declare `target`. Several plainly write into the target (`git`, `test_scaffold`, `bd_index`, the `pdf_*` family) and are inferred `toolkit` | T8 (census only) | Medium. The declaration is the INPUT to measurement, so a mis-declared tool is invisible to anything keyed on `writes: target`. `patch` was corrected in T8 because it is on the Apply path; correcting the other 25 is a bounded audit of what each tool actually touches, and is **not** T8's business. Recorded so the class is not rediscovered later as if it were news |
| **`dev_server_manager` imports `tools.command_profile.cli` directly** — route via `seam_call`, or extract a `*_shared` module? | 0034 | Medium. The call produces no ledger entry, so a capability is exercised without attribution. Behaviour-changing, and unrelated to T7 |
| **`cartridge_conflicts` is referenced only in its own file** — built in T5 for the governance cartridge | 0034 | Low — `P-install-packaging` owns the decision; deleting work already done for a scheduled tranche is not a review's call |
| **No layering policy declared**, so `domain_boundary_audit` can only report crossings as neutral facts rather than pass/fail | 0034 | Low — a `.uh-policy.json` would make it enforceable, but that is new architecture |
| ~~**CI workflow unverified**~~ | Alignment, 2026-08-08 | **CLOSED** — the workflow has run; Windows is the primary job and has caught two Windows-only defects |
| ~~**E8 may be a mechanism-exists claim**~~ | Alignment, 2026-08-08 | **CLOSED** — re-derived and demoted to NOT MET, 2026-08-09 |
| **Shipped contract must arrive blank** — our copy carries resolved `BCC-CONFIG` values and project-specific bootstrap notes | 0016 | **`P-install-packaging` owns it — E13** |
| ~~**Windows process-group kill unverified**~~ | T4 | **CLOSED 0023** — Job Object containment, with causation established by the `SUITE_DISABLE_CONTAINMENT` kill-switch mutation |
| **Canonical payload assembler** — the payload is still defined by subtraction, not by a positive manifest (Charter §5.4) | T6 deferred | **`P-install-packaging` owns it.** Deliberately NOT carried into T7/T8 |
| `developer_cert.pfx` should leave the tree | Operator action | Operator |
| `_trash/` needs emptying (66 swept lock files) | Operator action | Operator |

**Closed since last review**, removed rather than left to clutter the list:
`command_profile` lint detection (T2); lint enforcement living only in the suite
(now a gate assertion, and `ruff` is installed in the sandbox); presence
read-modify-write (made unreachable by T3's single-writer decision); the suite
failing three tests in its default configuration (0014).

**On backlog priority during convergence.** Two items were *raised* here rather than
lowered, because T7 and T8 actually touch them — the precept-guard cost and the
`attach` double-map. An item is high-priority when a scheduled tranche will make it
load-bearing, not when it is merely unresolved.
