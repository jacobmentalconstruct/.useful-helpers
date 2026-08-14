# Tranche Plan

Status: **ACTIVE.** T0-T5 parked. **T6 REOPENED** 2026-08-14 (journal 0028) for two
updater correctness defects, bounded — identity continuity across update, and durable
memory surviving a failed update. Development mode: **CONVERGENCE** (see below).
**T7 is sketched, not declared, and is not declared while T6 is open.**
Date: 2026-08-06, amended 2026-08-09, mode changed 2026-08-14, T6 reopened 2026-08-14.
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

Adopted 2026-08-14, on the evidence of the `_theCELL` dogfood run. **It begins when T6
re-parks** (0028): the rules and the sequence below are settled, and no convergence
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
| T6 | Instance Identity and the Installation Core | **REOPENED 2026-08-14** (0028), bounded to two updater defects. Binding, identity, relocation and runtime context all hold; **update does not**, so the outcome claim *"survives relocation and update"* is not yet true |
| — | ***convergence phase begins after T6 re-parks*** | |
| T7 | Shared Project Awareness Prototype | One compact evidence-backed orientation, persisted against the instance, same revision to human and agent |
| T8 | Governed Work Loop Prototype | awareness → impact → preview/diff → approval → Apply → verification → refresh, using existing tools and the existing seam |
| **STOP** | **Prototype stop / dogfood** | Architectural development halts. See below |

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


## T7 — Shared Project Awareness Prototype · SKETCHED, NOT DECLARED

**Outcome.** Existing deterministic tools are composed into **one compact,
evidence-backed current orientation** of the bound target, persisted against the
instance, and exposed as the **same revision** to human and MCP agent.

**Walk steps advanced (Charter §3.3):** 6, 7, 8, and the awareness half of 13.
It stops before target mutation — that is T8.

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

### Gate — `gates/t07_shared_awareness.py` *(written at declaration, before implementation)*

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

**Non-goals.** No target mutation. No change-driven selective refresh. No One
Surface. No new tool unless C1 rule 1 is discharged. No awareness ontology framework.

**Stop condition.** Both projections resolve the same revision id on all three
acceptance targets, and the gate suite is green on both platforms.

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
| proposed transformation | `edit` / `patch` preview | returns `source` **and** `result`, `written:false`, `apply_with` |
| reviewable before/after | existing `diff` tool | takes the text pair the preview already returns |
| governed mutation | same call with `apply:true` | returns `written:true` and `path` |
| attribution / audit | `event_log` | records client, authority, args_hash |
| what can be verified | `command_profile` | returns commands with a `kind` — `run`, `setup`, `test` |
| verification | `smoke_runner` / `project_run` | selected by `kind`, mechanically |
| reorientation | `attach` refresh + staleness | exists, coarse |

**Explicitly do not build:** a new diff engine, a new approval engine, a new
verification framework, a new project runner. (C1 rules 1 and 2.)

### The three seams that are genuinely missing — all composition, none new subsystems

1. **The preview does not offer its own diff.** `edit` returns both sides and stops
   at `replacements: 1`, so approving means approving *a count*. The shortest current
   chain is `edit` → `diff {a_text: source, b_text: result}` → `edit {apply:true}`.
   Nothing new is required; the chain is simply not wired.
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
```

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
| `test_d1_p1` slow: `attach` re-maps ~18k files twice | 0004 | **Medium — T7 touches it.** `attach` is the composition point; re-mapping twice is exactly the cost C2 exists to control |
| **`patch` declares `writes: toolkit` but writes to a target path** | §11 census, 2026-08-14 | **High — T8 owns it.** A tool that mutates the target while declaring it does not is a hole in the precept guard's own gating. Found by census, not by failure |
| **`_instance_module` docstring and call order disagree** — it says the identity authority is loaded *"FROM THE PAYLOAD JUST INSTALLED"*, but the update path calls it before the copy and loads the **old** tree's copy | 0028, third finding | **Medium.** Reading an old manifest with the code that wrote it may well be correct; the point is that the comment and the behaviour cannot both be. Deliberately **out of scope** for the T6 reopening, which is bounded to two defects |
| `docs-refresh` prints `_docs/TOOLS.md` while writing `docs/` | T6 closeout | Low — documentation staleness, no behaviour change |
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
