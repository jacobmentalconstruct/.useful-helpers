# Charter — Useful Helpers Sidecar

Status: **ACTIVE AUTHORITY.** T0-T6 parked and built against this document; T5 amended it.
Date: 2026-08-06, amended 2026-08-09 (T5), 2026-08-14 (convergence phase).
Authority: this document, with `.bcc/BUILDER-CONSTRAINT-CONTRACT.md`, supersedes
all prior framing. The former governing blueprint is retired to `_trash/`.

**Development mode as of 2026-08-14: CONVERGENCE.** The project is no longer missing
broad capability; see §1.3. Sequencing, the convergence rules and the prototype STOP
are owned by `TRANCHE_PLAN.md`, not restated here.

---

## 0. Two Deliverables

The product is **an installer and a payload**, not one application.

1. **The installer.** A GUI that lets the operator pick a folder and vend a
   sidecar into it. That folder becomes the sidecar's root, parent, and entire
   reality.
2. **The sidecar payload.** What gets installed, and what then operates on the
   bound target through its single surface.

They have different lifetimes and different users. **The setup application is the
first** — today `packaging/installer/install.py`, which carries its own Tkinter flow
and runs on a bare machine with stdlib only. `registry_view` and the unified surface
are the second. They do **not** merge.

*Corrected 2026-08-14:* this sentence named `src/ui/installer_view.py`, which no
longer exists. The runtime shell surfaces are `registry_view`, `mapper_view` and
`planner_view`; setup is not among them, which is the boundary this section states.

The sidecar can be deleted or archived at any time without affecting its target.
The target stays ignorant of it throughout, so when the target ships to its own
users, removing the sidecar leaves it clean.

### 0.1 It vends blank

The packaged product carries **no history of any kind**. No journal entry, no
event log, no evidence, no development document, no git history, no absolute
path from a build machine, no reference to any predecessor project.

The sidecar's record structures ship **present and empty**, and fill in the
field. Our own development record lives in those same structures while we build
and is purged at vend. This is condition E11 and it is gated.

---

## 1. What This Is

**One sidecar.**

It installs into any directory, on any drive, on any machine that can run
CPython. It maps the directory it is installed in. It operates on that directory
safely, through one governed seam. It is driven either by a human through a
single Tkinter surface, or by an agent through MCP — and both drive it through
the same seam, each able to see what the other is doing.

Where it has no tool for a task, another tool is added. Where a task is a
sequence, it becomes a chain.

It is a **sysop instrument with app-shaped workflows.** It is not a coding tool
that happens to touch files.

### 1.1 The one non-negotiable

Every action crosses `invoke()` — human GUI click, agent MCP call, CLI command,
chain step, and test alike. Authority-checked, containment-checked, audit-logged,
in one place.

No capability may have a second path. A GUI implementation plus an agent
implementation plus a CLI implementation of the same capability is the specific
failure this project exists to prevent.

### 1.2 The precept

The target never learns the sidecar exists. No pointer file, no `.gitignore`
line, no config key. The sidecar reads the target and writes only its own home.

Test: delete the sidecar folder. The target must not notice.

**The precept governs the sidecar's own footprint, not the user's work.** A governed
Apply operation may deliberately modify target-owned content — that is what the
product is for. What it may never do is leave a trace of *itself*. The exact rule,
by lifecycle phase and operation authority, is §3.2; the ownership boundary is §5.6.
*Never writes to the target* is a misstatement of the precept, and where a surface
says it plainly it is wrong.

### 1.3 The prototype objective

[OWNS: SIDECAR:PROTOTYPE-OBJECTIVE]

Adopted 2026-08-14, after the `_theCELL` dogfood run showed the existing toolbox
already understanding and operating on a real, unfamiliar target.

> Install Useful Helpers into a target of nearly any kind; use local compute and
> existing deterministic tools to understand that target deeply; expose **one compact
> current understanding** to both human and agent; and let either safely inspect,
> transform, verify and re-understand the target through the governed toolbox.

Three consequences, each of which overturns an earlier framing:

1. **The remaining gap is composition, not capability.** Ninety-four tools already
   produce the evidence. What does not exist is one compact synthesis of it, one
   shared presentation of that synthesis, and a closed change loop over it.
2. **Existing tools remain evidence producers.** Awareness is their compact
   composition, never their replacement. Project Mapper stays a snapshot compiler;
   code-intel stays code-intel; SQLite inspection stays SQLite inspection. `attach`
   becomes the front door that composes the appropriate evidence.
3. **Local compute is cheap; model context is expensive.** Scan and analyse richly on
   the user's machine, retain the evidence locally, and send the model only compact
   summaries, canonical identifiers and requested drill-down. Measured basis: on
   `_theCELL`, `report` plus `dead_code` returned ~49 KB of envelope to supply seven
   summary integers of actual signal.

The end-state conditions E1-E13 remain the invariants. §3.3 is the experience.
`TRANCHE_PLAN.md` owns the convergence sequence and the point at which architectural
development stops and dogfooding begins.

### 1.4 The enduring product shape

[OWNS: SIDECAR:PRODUCT-SHAPE]

Declared 2026-08-14. This is the layering the product converges to, and the thing
§2's ten prohibitions were always circling without naming.

```text
    mechanical tools  ->  governed tool chains  ->  common runtime/seam  ->  human + agent
```

**not**

```text
    mechanical tools  ->  specialised applications  ->  human + agent
```

| Layer | What lives there | Test |
| --- | --- | --- |
| **primitive tools** | small capabilities, narrow contracts: filesystem inspection, read/search, AST/symbol/import analysis, SQLite inspection, diff/edit/patch, run/test, snapshot, PDF and data operations, provenance/audit, local inference | independently useful and directly callable |
| **tool chains** | reusable compositions that accomplish a user-level job: orient, capture, build awareness, inspect impact, preview/review/change, verify, refresh | coordinates tools; **never becomes an application** |
| **common governed runtime** | registry → policy → `invoke()` → tools and chains | one seam, no second path (§1.1) |
| **projections** | CLI, MCP, the shared GUI shell | render the *same* underlying state; never construct competing models |

**`apps/` is a transitional layer.** Its members are re-homed implementations kept as
reference and as parity oracles. The *behaviours* they embody are valuable and must be
preserved; their *structure* is not part of the intended prototype. An application is
retired when the bench reproduces its behaviour — never merely because a plan says the
directory should disappear. §2.2 already refused twelve apps behind twelve buttons;
this states the positive form of the same rule.

#### A large tool is not an application

The distinction is **ownership, not size.** Line count is not the smell and must never
be cited as one.

| | |
| --- | --- |
| **acceptable** | a 1,000-line deterministic snapshot compiler with **one narrow contract** — target in, canonical artifact out |
| **not acceptable** | a 300-line "tool" that owns a private project model, its own parser suite, its own state store and its own workflow |

The test is whether a surface has taken **private ownership of capabilities, state or
workflows that belong to the common bench.** A big honest primitive is fine. A small
surface with its own ontology is the defect.

Two corollaries follow, and both cut against reflexive decomposition:

- **Location is not architecture.** A normal registered tool that happens to live in
  `apps/` is a *classification* defect. Re-homing it satisfies this section; the
  directory does not have to become empty for its own sake.
- **Removal of duplicated ownership is the goal, not maximum decomposition.** Do not
  split a coherent atomic operation into six tools and a playbook to satisfy an
  abstract preference for chains.

The governing design test, applied to any proposed structure:

> **Is this something a tool does, something a chain of tools accomplishes, shared
> state the whole bench needs, or a projection for a human or agent?**
>
> If it cannot be justified as one of those four, it does not belong in the prototype.

The finished product is **one governed box of capable hands**, not a launcher for a
collection of mini-products.

---

## 2. What This Will Never Be

Each entry is a real temptation this project has already faced or inherited.

1. **Not a second application.** There is one runtime: `toolkit/`. No parallel
   `src/` workbench, no bridge between two apps. The sidecar *is* the product.
2. **Not twelve apps behind twelve buttons.** The daily drivers become
   declarative chains over existing tools, not twelve reimplemented backends.
3. **Not code-only.** Data curation, records research, and workspace tasks are
   first-class. Cartridges for these already exist and must keep working.
4. **Not dependent on a local model.** Every deterministic capability works with
   no inference available. Local models are opt-in leverage, never a requirement.
5. **Not a trainer.** No fine-tuning, no GPU workloads, no external-environment
   launchers. Removed by decision, 2026-08-06.
6. **Not a plugin host.** No directory is scanned for executable Python.
   Registration is manifest-declared and explicit, always.
7. **Not an agent framework.** No recursive lifecycles, no child spawning, no
   implicit prompt inheritance.
8. **Not a graph engine, message bus, or event-sourcing system.** Coordination is
   explicit typed interfaces. The event log is an audit and trace ledger, and
   will not be described as event sourcing unless replay and state
   reconstruction actually exist.
9. **Not a web service.** Local, offline-capable, no network requirement for any
   core capability.
10. **Not self-modifying in the dark.** The sidecar may build tools; it may not
    silently alter its own governance, authority ceiling, or seam.

---

## 3. End State

The project is complete when all of the following hold **and are demonstrated by
a passing check**, not asserted.

| # | Condition | How it is proven |
| --- | --- | --- |
| E1 | Installs into an arbitrary empty directory on a machine with only CPython, and runs | Install to a scratch dir on a clean environment; `attach` returns a map |
| E2 | Maps any directory it is installed in, across domains | `attach` succeeds on a code target, a data-curation target, and a records target |
| E3 | One GUI surface reaches every tool and every chain | No capability requires a second command or a second window to reach |
| E4 | An agent reaches every tool and every chain through MCP | Tool list from MCP equals the registry |
| E5 | Human and agent actions are indistinguishable to the seam | One event stream contains both, attributed by client, same schema |
| E6a | Each can see the other **act**, live | A GUI action appears to an agent, and an agent action appears in the GUI, without restart or manual refresh |
| E6b | Each can query the other's current **context** | An agent asks what the human is working on and gets an accurate answer |
| E7 | Daily-driver workflows exist as chains | Each retained daily driver is reachable as a chain and produces its documented output |
| E8 | Sidecar lifecycle and self-management never silently mutate target-owned content; runtime target mutation requires an explicit governed operation whose authority and declared write scope permit it | Phase x authority matrix, §3.2. Install/update/uninstall/startup/verify/self-maintenance each leave target-owned content byte-identical; Observe reads only; Apply mutates only inside its declared write scope under the governed confirmation path; Sandbox only in its declared copy scope. Read-only mount prevention remains independent evidence where the host supports it |
| E9 | The parts bin can be deleted and everything still passes | Delete the bin, run the full gate suite green |
| E10 | Every claim in the docs is executable | No document asserts a behavior with no check behind it |
| E11 | The setup distribution and canonical payload carry product identity and required **self-knowledge**, but no development-instance history or lineage | Build the payload; assert it CONTAINS product name, instance manifest, reserved namespace, generic documentation, tool manifests, version/schema, self-verification rules and the generic contract seed - and CONTAINS NO journal, evidence, tranche history, source git history, builder identity, build-machine path, predecessor-project identity, parts-bin residue or accumulated runtime state. Lineage terms are derived from this project's own manifest, not hardcoded |
| E12 | An installed sidecar is removable without trace | Vend, use, delete the sidecar folder; the target is byte-identical to before the vend |
| E13 | The governance cartridge installs **optionally and blank** | Install with the toggle off: no contract, protocol or gate runner arrives. Install with it on: all three arrive, `BCC-CONFIG` values resolved for the **new** target, and no value, path, journal reference or tranche number from this build survives |

### 3.3 The prototype acceptance walk

The end-state conditions E1-E13 are invariants. This is the **experience** they exist
to make possible, and it is the thing to judge a tranche against.

A completely new user can:

```text
 1. obtain the setup application
 2. choose any folder - code, records, documents, mixed files, or empty
 3. install Useful Helpers into it
 4. launch it
 5. it identifies itself and its target
 6. it maps the target
 7. the user can inspect that map
 8. an agent connects over MCP and receives the SAME project awareness
 9. human or agent inspects the target through governed tools
10. an authorized Apply operation deliberately modifies the target
11. the modification is attributable and auditable
12. project awareness refreshes to reflect the new reality
13. restarting destroys neither identity nor durable awareness/state
14. moving the target together with its sidecar does not break the relationship
15. removing the sidecar does not damage target-owned content
```

**Every tranche states which of these fifteen becomes materially more true when it
parks.** If that cannot be answered, the tranche is drifting.

The sidecar does not need to know the target's domain before installation:
**install first, observe second, interpret third, operate afterward.** Awareness is
evidence-sensitive - a folder of PDFs and an empty directory are legitimate targets
whose maps are legitimately thinner, not failures to force into a software ontology.

### 3.2 The phase x authority matrix (E8)

"The target is never modified" was never the product invariant. An Apply tool exists
precisely to modify it. The real rule has two axes - **lifecycle phase** and
**operation authority** - and neither alone is sufficient.

| Phase / operation | May mutate | May not mutate |
| --- | --- | --- |
| setup **install** | creates `INSTANCE_ROOT` | target-owned content |
| setup **update** | `INSTANCE_ROOT`; migrates instance state by explicit rules | target-owned content |
| setup **uninstall** | removes `INSTANCE_ROOT`, and only that | target-owned content |
| **startup / verify / self-maintenance** | sidecar-owned state | target-owned content |
| **Observe** operation | nothing | the target is read-only |
| **Apply** operation | target content **inside its declared write scope**, under the governed authorization and confirmation path | anything outside that scope |
| **Sandbox** operation | its declared sandbox or copy scope | the target |

The word doing the work is **silently**. Lifecycle and self-management never mutate
target-owned content at all; runtime mutation is permitted, attributable, scoped and
confirmed.

### 3.5 What is already true

Recorded so the remaining work is not overstated. All verified this session by
execution, not inspection.

- **94 registered tools** (`config/registry.json`, live count 2026-08-14); control
  plane is standard-library only; runs on Linux and Windows. *The figure read 95 from
  2026-08-06 until this correction; the generated registry is the authority, and this
  line is a dated observation of it, not a second one.*
- One governed seam with authority ceiling, path containment, and audit log.
- The GUI already crosses the seam. *The original citation was
  `installer_view.py:131`; that file has since been deleted. The live evidence is
  `src/ui/registry_view.py`, and `gates/t02` asserts the property by census over all
  of `src/` rather than by pointing at one line — which is why deleting the cited
  file did not cost the assertion.*
- MCP entrance exists.
- Domain cartridges exist for data-curation and records-research.
- `THEME_SPEC.md` is fully implemented in `src/lib/theme.py` — five colours and
  both fonts match exactly.
- Chains exist as `playbooks/` with a `run-playbook` runner.
- Tool creation is supported and safe: `_template/`, `stamp`, `registry-refresh`.
- 79 distinct tools were exercised against the real daily-driver tree on
  2026-07-18: 124 ok, 19 failed. Preserved in `.bcc/evidence/`.

### 3.6 What was genuinely unbuilt — dispositions

Written 2026-08-06 as the short list of missing substrate. Kept because the
dispositions are the evidence for §1.3's claim that broad capability is no longer
what is missing. **Superseded as a work list**; `TRANCHE_PLAN.md` owns what is next.

1. ~~**A live event channel.**~~ **BUILT — T3.** Ledger read, tail and watch exist;
   measured presence read cost 0.29 ms. E6a and E6b are MET.
2. **One surface.** Still four views behind four commands. **Deliberately out of
   scope for the convergence phase** — the prototype needs the *smallest* legible
   human projection of shared awareness, not a redesigned shell. E3 is post-STOP.
3. **Chains for the daily drivers.** Three playbooks exist; the app-shaped ones do
   not. E7, post-STOP.
4. ~~**Cancellation and progress.**~~ **BUILT — T4, hardened in 0023.** Cancellable
   dispatch, per-call timeout, progress announcements, and Windows Job Object
   containment of the whole process tree.
5. ~~**Explicit-target install.**~~ **RESOLVED 2026-08-06, then SUPERSEDED by T6.**
   The 2026-08-06 fix removed a folder-name heuristic and made a `.suite_sidecar`
   marker bind to the parent. **That marker no longer exists.** T6 replaced all
   marker, basename and environment inference with one canonical identity manifest
   (`src/core/instance.py`); `resolve()` returns `None` when a directory is not an
   instance and **raises** when it claims to be one and is broken. Any surface still
   describing marker-based resolution is stale, not authoritative.
6. **The vend manifest.** One declared manifest now exists (`src/core/payload.py`),
   and every consumer derives from it — but it still defines the payload by
   *subtracting exclusions from the source tree*. §5.4 requires a **positive install
   manifest**. Recorded as deferred lifecycle/distribution work: the **canonical
   payload assembler**. It is not carried by any convergence tranche.

---

## 4. Stopping Conditions

The project stops when §3 holds. At that point it is **closed**, and the
following are explicitly *not* reasons to reopen it:

- A tool could be faster.
- The UI could be prettier.
- A subsystem could be decomposed further.
- A newer library exists.
- More tools could be added — new tools are ordinary use of a finished sidecar,
  not continued construction of it.

Reopening requires a correctness, security, containment, data-loss, or
maintainability justification, stated in the journal before work begins.

A tranche that has parked is closed. Polish after parking is prohibited.

---

## 5. Ownership and Distribution Model

This section is the **owner** of this product's topology and ownership semantics.
Every other surface cites these identifiers rather than restating them, per
`BCC-ONE-AUTHORITY`.

```text
[OWNS: SIDECAR:SOURCE-FACTORY]
[OWNS: SIDECAR:SETUP-DISTRIBUTION]
[OWNS: SIDECAR:INSTALLABLE-PAYLOAD]
[OWNS: SIDECAR:INSTANCE-OWNERSHIP]
[OWNS: SIDECAR:TARGET-OWNERSHIP]
[OWNS: SIDECAR:EXTERNAL-CORPUS]
```

### 5.0 The topology

```text
PUBLIC SOURCE / DEVELOPMENT REPOSITORY
        |  build / package
        v
OS-SPECIFIC SETUP APPLICATION  +  CANONICAL INSTALLABLE PAYLOAD
        |  one explicit user-selected target
        v
TARGET_ROOT
|-- target-owned content
`-- INSTANCE_ROOT  (default `.useful-helpers/`)
    `-- exactly ONE installed sidecar instance
```

A user receives a **setup application**, not the running product. They point it at
exactly one location — an existing codebase, a folder of data to curate, an empty
directory, a documents workspace, anything that is to become the one target. It
creates one instance, permanently associated with that target.

**There is no central sidecar that opens many projects.**

### 5.1 The four roots

One word was doing four jobs. `SIDECAR_ROOT` meant the BCC's governance root in the
contract and the product's instance root in architecture prose, and those are not
the same abstraction.

| Term | Meaning |
| --- | --- |
| `TARGET_ROOT` | the directory the user selected; the sidecar's entire reality |
| `INSTANCE_ROOT` | the installed sidecar's own home inside it — the **reserved namespace** |
| `GOVERNANCE_ROOT` | where builder-control artefacts live (the BCC's `SIDECAR_ROOT`) |
| `STATE_ROOT` | the instance's mutable runtime state |

`INSTANCE_ROOT` and `GOVERNANCE_ROOT` are distinct concepts and must not share a
name in prose, configuration, or code.

### 5.2 SIDECAR:SOURCE-FACTORY

The public development repository. It may legitimately contain development
governance, tests, tranche gates, the harness, build machinery, CI, and packaging
definitions.

**Presence in the source repository is not evidence that something should be
installed.** `.github/` in the source repository is correct; `.github/` in a payload
is a packaging error.

The root is a factory and has no runtime of its own.

### 5.3 SIDECAR:SETUP-DISTRIBUTION

The standalone OS-specific setup application. Its only job is to install, update,
reinstall and uninstall an instance.

**`packaging/installer/` is the product's installation entrance.** It is the
authority for what installation means.

~~`tools/sidecar_install` is a *runtime tool that installs another sidecar*.~~
**DISPOSED — T6.** It was deleted, along with the harness's two private installers.
Nine surfaces claiming installation authority were classified; one remains, and it is
`packaging/installer/`. The installed runtime does not expose installing a sidecar as
a product capability.

### 5.4 SIDECAR:INSTALLABLE-PAYLOAD

The materialised sidecar content the setup application consumes — a real build
artifact, independent of platform wrapping.

Membership is declared by a **positive install manifest**: these components
constitute an installable sidecar. Negative exclusion sets remain as
defence-in-depth and are **not** what defines the product.

```text
positive inclusion  = authority
negative exclusion  = safety net
```

Conformance is proven by inspecting the **built payload**, not by inferring
cleanliness from the source tree.

*Today's implementation inverts this — `src/core/payload.py` derives the payload by
subtracting exclusions from the source tree. That is a recorded nonconformity, and
`payload.py` is the current owner of concrete membership until the positive manifest
replaces it.*

### 5.5 SIDECAR:INSTANCE-OWNERSHIP

One installed instance, belonging to one target.

**It may know itself** — its own home, which files are its own, its manifests, its
state, its contract, its bindings, its tool inventory, its exclusions, its health,
and the reserved namespace it occupies. This is required behaviour, not
contamination.

**It does not vend additional instances.** The source factory knows how to build a
sidecar; an installed instance has no business reproducing itself. The chain is
`source → payload → setup → instance`, never `instance → instance`.

The instance must have a **durable identity** resolved from its actual runtime
location plus a recorded relative relationship to its target — not a basename guess,
not an environment variable, and not a frozen absolute path that breaks when the
target is moved.

### 5.6 SIDECAR:TARGET-OWNERSHIP

Everything in `TARGET_ROOT` outside `INSTANCE_ROOT`.

```text
TARGET_ROOT
|-- INSTANCE_ROOT     sidecar may freely maintain this
`-- target-owned      installation and self-maintenance may not mutate this
```

*The project knows nothing* does **not** mean the filesystem contains no sidecar. It
means target-owned content has no dependency on the sidecar and is not made to
participate in its existence. The installer may create the reserved namespace. The
sidecar must exclude its own namespace when interpreting the target.

Runtime work **may** modify target-owned content — that is what the product is for —
but only as an explicit governed operation. See E8.

### 5.7 SIDECAR:EXTERNAL-CORPUS

Real predecessor and representative targets used for regression. **Not product
source, not setup distribution, not payload.**

Small sanitised deterministic fixtures may live with the source. The large
real-world corpus is an external development resource, identified by a manifest with
provenance and hashes so a regression run is reproducible. A missing corpus means
*full regression not performed*; it must never read as *full regression passed*.

*Today `_harness/targets/` holds 639 committed files duplicating seven parts-bin
applications. That is a recorded nonconformity.*

### 5.8 The governance cartridge

The contract is one of the tools the sidecar carries, installable by an opt-in
checkbox with the `BCC-CONFIG` values as editable fields. A target that wants
tranche discipline can have it; a target that does not is never colonised by it.

**Invariant:** enabling the cartridge does not expand sidecar ownership into
target-owned content. Its `TARGET_PROJECT_ROOT` may name the real parent target, but
its control artefacts — journal, evidence, plans — remain inside `INSTANCE_ROOT`.
Enabling it must not create `TARGET_ROOT/_docs/AppJOURNAL/`. **E13.**

### 5.9 Historical note

Until 2026-08-06 the product lived at `toolkit/` inside the factory with charter and
plan at `_design/`. The sidecar has since collapsed to the root: `TOOLKIT ==
FACTORY`, and neither directory exists. A zone table here described the old shape for
three tranches after the change, which is why this section now names its facts.

---

## 6. The Seam Contract

Agreed 2026-08-06. This resolves how human and agent share one machine through
different interfaces.

### 6.1 Two channels, one seam

The mistake to avoid is one log serving two needs with opposite requirements.

**The ledger answers "what happened."** Append-only, durable, permanent. Every
entry is a governed action with an authority behind it. This exists today.

**Presence answers "what is true right now."** What is selected, what is
included, what has focus, which chain step is running. It matters only while
both parties are present.

Presence is **queryable state, not accumulated events.** An agent asking what
the human is working on gets an answer, rather than replaying four hundred
selection events to reconstruct one. State does not grow; that dissolves the
log-size problem structurally instead of compressing it.

| | Ledger | Presence |
| --- | --- | --- |
| Shape | Events, append-only | Current state plus a change tick |
| Lifetime | Permanent | Dropped on restart |
| Loss tolerance | None | Lossy is acceptable |
| Growth | Hundreds per engagement | Constant — a snapshot |
| Audited | Yes | No |

### 6.2 The boundary test

**If it would still matter after a restart, it is a ledger event. If it only
matters while someone is watching, it is presence.**

- **Ledger:** every `invoke()` call including Observe; authority denials;
  precept violations; project open and close with target root; registry changes.
- **Presence:** selection, inclusion set, focus, scroll, progress within a
  running chain.

Measured basis: a real engagement produced 143 events across 79 tools — tens of
kilobytes. Tool calls are inherently coarse and deliberate, so the ledger is
self-limiting. The growth risk was never tool calls; it is UI events at
thousands per hour. Those are never ledgered.

Deduplication is rejected as the wrong lever: it destroys the temporal
information that makes an audit log worth keeping, and distinct events with
distinct payloads do not dedupe. The existing schema already carries the right
instinct — `args_hash` and `arg_keys`, not the arguments themselves. Hash, do
not store.

### 6.3 Confirmation is a first-class event

When a human approves or refuses an Apply operation, that is the human's
equivalent of a tool call — the moment authority is actually exercised.
*"The agent proposed rewriting 400 files and the human declined"* belongs in the
ledger permanently.

Today confirmation is a boolean argument inside a tool call, so the decision is
not distinct or attributable. It must become its own ledger event. This, not
selection tracking, is the human-side gap.

### 6.4 Derived visible state — specified now, built later

Presence has two levels.

**Level 1, in scope for the end state (E6b):** a minimal context query — target
root, selection, inclusion set, active chain.

**Level 2, deferred:** a derived report of what the human's UI is actually
*showing*, so an agent can speak to what the human sees. Not what was selected —
what is visible: which panel is open, which rows are on screen, which file is in
the viewer at which range, what error is displayed.

Three constraints on Level 2 when it is built:

- **Derived, not authored.** Produced from the live widget tree on request, never
  maintained alongside it. A hand-updated snapshot drifts within a week, and a
  confidently wrong answer about what the human sees is worse than none.
- **Pulled, not pushed.** Generated when asked. Tk fires events constantly; a
  pushed snapshot means either a firehose or a stale file.
- **Semantic, not pixels.** Describable and citable, not coordinates or images.

The toolkit already ships `tkinter_widget_tree` and `ui_callback_graph`, built to
map other people's Tk applications. Pointed inward at the running surface, most
of the derivation already exists — subject to verification.

Deferred because it must be designed against a real unified surface, which does
not yet exist. It is not load-bearing for the end state; it is what makes E6b
good rather than merely satisfied.

### 6.5 Remaining open decision

**Transport for the live channel** — polling the SQLite ledger, a local socket,
or an append-only tail. Determines whether an out-of-process agent can subscribe
or only an in-process one. Splitting presence from the ledger makes this easier,
since presence needs no durable storage at all. To be settled in the tranche
that builds the channel.

### 6.6 Decisions closed (continued below)

- **Daily drivers retained as chains:** ten. The seven with contracts, plus
  `_TempServerMAKER`, `_MicroserviceLIBRARY` and `_NoStringsPDF`, which receive
  contracts written from their filedumps.
  `_UsefulHelperScriptsMENU` is the sample for the surface itself, not a chain.
  `_LoRA_TRAIN` is removed.
- **`apps/` does not survive.** Chains are the app shape. `apps/projectmapper`
  is retired into a chain. *The 2026-08-06 note predicted the count moving 95 → 94
  when it goes; the live count is already 94 while `apps/` still contributes, so the
  arithmetic is stale and the expected post-retirement figure must be re-derived from
  the generated registry at the time `P-retire-apps` runs, not carried from here.*

---

## 7. Verified Findings Carried Forward

Obtained by **execution** on 2026-08-06, not inspection. Carried here because
the documents that originally held them are archived, and re-obtaining them
costs real time. Full evidence in `.bcc/evidence/`.

### 7.1 The seam works

| Check | Result |
| --- | --- |
| Toolkit runs; registry count | PASS — 95 tools, VERSION 1.1.0 |
| `SUITE_PROJECT_ROOT` binds an arbitrary target | PASS |
| Observe tool leaves target byte-identical | PASS |
| Precept violation fails the call | PASS, with the caveat in 7.3 |
| Invalid target root | **FAIL** — see 7.2 |
| Timeout | PASS — clean at 120 s, no orphaned child |
| `SUITE_STATE_ROOT` / `SUITE_HOME` redirect | PASS — including the seam's own event log |

Also verified: stdout is pure JSON and parses directly, logs go to stderr. The
control plane is standard-library only, which is why it runs unmodified on Linux
despite being a Windows product.

### 7.2 The most dangerous defect — **HISTORICAL. SUPERSEDED BY T6.**

> **This describes 2026-08-06 behaviour and no current mechanism.** Both halves of it
> are gone. There is no `.suite_sidecar` marker, no dot-prefixed-name inference and no
> parent fallthrough: an installed instance resolves its target from `instance.json`
> structurally, and a manifest that is present but broken **raises** rather than
> falling through to a guess. The "required mitigation" below was superseded by
> something stronger than validation — the guess it was validating no longer exists.
>
> Retained unedited because the *class* of defect it names is the one this project
> keeps rediscovering: **a wrong answer that is indistinguishable from a right one.**
> Delete the account and the lesson goes with it.

Pointing `SUITE_PROJECT_ROOT` at a path that does not exist **does not error.**
It silently resolves to the sidecar's parent and reports `ok: true`. In this
repository that meant the toolkit reported operating on the factory root while
claiming success.

Compounding it: `toolkit/.suite_sidecar` exists, and a dot-prefixed home also
triggers parent inference. A typo in a target root is therefore indistinguishable
from success.

**Required mitigation:** validate the root before launch, and assert the root
echoed in the result equals the root requested. Treat any mismatch as a hard
failure. This is why the sidecar must require an explicit target (§3.2 item 5).

### 7.3 The precept guard detects; it does not prevent

A fixture declaring `authority: Observe` / `writes: none` that writes into the
target was run against a scratch tree. The seam returned `ok: false` and named
the exact file — **and the file was on disk afterwards.** The seam cannot sandbox
a subprocess, so the write lands and is then reported.

Consequences:

- A precept violation is a **damage event**, not a failed call. It must be
  surfaced as *"this tool modified your project when it said it would not."*
- `SUITE_STRICT_OBSERVE=0` disables the guard entirely and silently — verified,
  the same fixture returned `ok: true`. It must be set to `1` explicitly on every
  invocation, never inherited from the ambient environment.
- Prevention exists in the factory harness via read-only mount, Linux only. On
  Windows and macOS it reports UNAVAILABLE with a reason rather than a false pass.

### 7.4 Other recorded frailties

- ~~A tool emitting unparseable output is treated as **success** with
  `{"raw_stdout": ...}`. A silent tool passes. Must be treated as failure.~~
  **CLOSED in T8 (2026-08-19).** Empty stdout, invalid JSON, and valid JSON that is
  not an object are now three distinct seam failures, each naming which one occurred.
  `raw_stdout` is preserved in every branch — refusing to interpret output is not a
  reason to discard the only evidence of what the tool was trying to say. Swept all
  52 Observe tools: none emits uninterpretable output. The 42 Apply/Sandbox tools
  were not swept, because firing them blindly is not a safe audit.
- `DEFAULT_TIMEOUT_S = 120` is module-level, not a per-call parameter. Too short
  for large snapshot compiles.
- The seam blocks on `subprocess.run`: no cancellation, no progress streaming.
- Raw stderr is returned and may carry absolute host paths; redact before display.
- `VERSION` does not move when tools are added. A stale copy was found declaring
  `1.1.0` while carrying 78 tools against the canonical 95. Version tells you
  nothing about tool coverage.

### 7.5 Environment constraints

- **SQLite over a mounted host folder is unreliable** — `disk I/O error` observed,
  with a stale journal file. Runtime state belongs in a platform user-data
  location, not inside the project. This is evidence, not preference.
- **The development mount denies unlink.** Create, write, overwrite and rename
  all work; delete does not. Removals are staged in `_trash/` for the operator.
  Every git *write* strands a lock file that must be moved aside.
- ~~**All Windows-specific behavior is unverified.**~~ **CORRECTED 2026-08-13.**
  Windows is now the primary CI job (`.github/workflows/verify.yml`) and the
  authority for a zero-skip run; `run.bat`, path handling and venv resolution are
  exercised there. Two Windows-only defects were found and fixed that no Linux run
  could see: `taskkill /T` skipped when the direct child exited cleanly, and
  `CreateJobObjectW` silently truncating a 64-bit HANDLE because ctypes defaults
  `restype` to `c_int`. What remains unverified is stated per tranche, not globally.
