# Tranche Plan

Status: **ACTIVE.** T0-T5 parked; T6 awaiting operator review.
Date: 2026-08-06, amended 2026-08-09.
Authority: subordinate to `CHARTER.md`; procedure defined by `TRANCHE_PROTOCOL.md`.
This document owns **sequencing only**. Product topology and ownership semantics
belong to the Charter - cite `SIDECAR:*` identifiers here, never restate them.

Numbering starts at **T0** and is this project's only valid numbering. Every
identifier in archived material belongs to a predecessor project.

Each tranche states its outcome, its gate, and its non-goals. The gate is
written during declaration, before implementation.

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
| E1 | Installs into an arbitrary directory, CPython only | partial | vend verified; fresh-machine install is T9 |
| E2 | Maps any directory, across domains | partial | `attach` works; cross-domain unproven |
| E3 | One GUI surface reaches every tool and chain | **not started** | One Surface, redeclared after the awareness tranche |
| E4 | An agent reaches everything through MCP | partial | MCP entrance exists; parity unasserted |
| E5 | Human and agent indistinguishable to the seam | **MET** | t02 gate: census over all of `src/`, every call site attributed |
| E6a | Each sees the other **act**, live | **MET** | T3 — measured poll cost 0.29 ms; resync on shrunken ledger |
| E6b | Each can query the other's **context** | **MET** | T2 presence; CLI no longer wipes it |
| E7 | Daily-driver workflows exist as chains | **not started** | T7 |
| E8 | Lifecycle never silently mutates target-owned content; runtime mutation is governed and scoped | **NOT MET** — restated by T5 | **Reclassified 2026-08-09.** The old claim was proven against the old wording. The phase x authority matrix (Charter §3.2) has **no** assertion behind install/update/uninstall/startup/self-maintenance, and `packaging/installer/install.py` — the product's install entrance — has never been exercised by any gate. Harness PRECEPT/ENFORCEMENT remain valid partial evidence; mount prevention is Linux-only |
| E9 | Parts bin deletable, everything still passes | **not started** | T10 |
| E10 | Every documented claim is executable | partial | gates cover much, not all |
| E11 | Payload carries product identity and self-knowledge, no development history | **NOT MET** — restated by T5 | **Withdrawn 2026-08-09.** The claim rested on a lineage check searching for *another project's* vocabulary (`mindshard`, `appfoundry`, `bdneural`), in both `_harness` and `t01`. A scan of the real 280-file payload for this project's own terms found `_ProjectMAPPER`, `_UsefulHelperSCRIPTS`, `_NoStringsPDF` and a builder identity. Self-hosting evidence is superseded **Two retained `t01` assertions carry declared PARTIAL coverage** and are printed as `[PARTIAL]` by `gates/run.py`: (1) the predecessor sentinel set is incomplete and cannot detect this project's own predecessors; (2) the payload fixture is materialised by `tools/sidecar_install`, a legacy runtime tool that is a fixture producer only, conferring no product authority and proving nothing about canonical installation. Neither contributes to closing E11 |
| E12 | Installed sidecar removable without trace | partial | vend clean; removal untested |
| E13 | Governance cartridge installs optionally and blank | **not started** | Charter §5.8 states the invariant: enabling it must not expand ownership into target-owned content. Wiring is Install and Packaging |

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
| T6 | Instance Identity and the Installation Core | **AWAITING APPROVAL** — one canonical instance identity, created by the standalone setup application, resolved structurally |
| — | *the sequence below is provisional and renumbers when T6 is declared* | |
| P | One Surface (redeclared) | E3 — the operational surface of one installed instance on one bound target |
| P | Contracts for Uncontracted Daily Drivers | Ten contracts exist |
| P | Chains | E7 |
| P | Retire `apps/` | One extension shape, not two |
| P | Install and Packaging | E1, E2, E4, E13 |
| P | Closure | E8, E9, E10 |

Ordering rationale: safety before capability (T1 precedes everything that acts);
the seam contract before the surface that displays it (T2-T4 precede any surface);
**the ownership model before anything that depends on where a boundary falls** (T5
precedes the rest).

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


## T7 — Chains

**Outcome.** The daily drivers exist as chains and produce their documented
output. **E7.**

**Work.** Author a chain per retained daily driver over existing tools. Build
only the tools a chain genuinely lacks, justified against the contract.

**Gate — `gates/t07_chains.py`**

- each retained daily driver is reachable as a chain from the surface and from MCP
- each produces its documented output against a fixture
- no chain bypasses the seam
- every new tool added is manifest-declared and authority-bearing

**Non-goals.** No feature parity with the original UIs; parity is of capability.

---

## T8 — Retire `apps/`

**Outcome.** One extension shape: tools and chains.

**Work.** Convert `apps/projectmapper` to a chain. Remove `apps/` from the
registry path.

**Gate — `gates/t08_retire_apps.py`**

- no registered capability originates from `apps/`
- project-mapper capability is reachable as a chain and passes its T7 assertions
- registry count matches the expected post-retirement figure

---

## T9 — Install and Packaging

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

**Gate — `gates/t09_install.py`**

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

## T10 — Closure

**Outcome.** The project is provably done. **E8, E9, E10.**

**Work.** Delete the parts bin. Run the full suite. Path-scrub and secret audit.
Final journal closeout.

**Gate — `gates/t10_closure.py`**

- the parts bin is absent and the entire gate suite passes
- no runtime module references an archived or reference path
- `.bcc/` and `_docs/` can be removed without affecting runtime
- precept guard passes; read-only prevention passes where the host supports it
- no document asserts a behavior without a check behind it

On a green T10, the project is **closed** per charter §4.

---

## Deferred

- **Derived visible-state (presence level 2).** Charter §6.4. Built after T5,
  when a real surface exists to derive from. Not load-bearing for the end state.
- **Read-only mount prevention on Windows/macOS.** No known strategy; reports
  UNAVAILABLE with a reason.

## Capability Gap — `lint` · **PRIORITY**

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

**Priority: high.** Not scheduled into a tranche yet — inserting it mid-plan is
the scope creep the protocol warns against — but it should be considered before
T2 rather than after, because every tranche from here writes code, and the
cheapest check on that code is the one currently unavailable.

---

## Backlog

| Item | Origin | Priority |
| --- | --- | --- |
| **`lint` tool** — see the capability gap above | Review pass, 2026-08-06 | Medium — see note |
| `dependency_check` does not distinguish dev from runtime deps | Corollary 6 | Medium |
| `VERSION` does not move when tools change | Charter §7.4 | Medium — T9 owns it |
| Precept-guard cost unmeasured on large targets | Charter §7.3 | Low — resolves at E9 |
| `test_d1_p1` slow: `attach` re-maps ~18k files twice | 0004 | Low — resolves at E9 |
| **CI workflow unverified** — first run is on the runner | Alignment, 2026-08-08 | **Confirm at next push** — now the only path exercising the default config on Windows |
| **E8 may be a mechanism-exists claim** — re-derive with evidence | Alignment, 2026-08-08 | High — before T10 |
| **Shipped contract must arrive blank** — our copy carries resolved `BCC-CONFIG` values and project-specific bootstrap notes | 0016 | **T9 owns it — E13** |
| **Windows process-group kill unverified** — `taskkill /F /T` untested | T4 | **High before T5b** |
| `developer_cert.pfx` should leave the tree | Operator action | Operator |
| `_trash/` needs emptying (66 swept lock files) | Operator action | Operator |

**Closed since last review**, removed rather than left to clutter the list:
`command_profile` lint detection (T2); lint enforcement living only in the suite
(now a gate assertion, and `ruff` is installed in the sandbox); presence
read-modify-write (made unreachable by T3's single-writer decision); the suite
failing three tests in its default configuration (0014).

**On the `lint` tool's priority.** Downgraded from High to Medium — not because it
matters less, but because the *hole* it was filling is closed. The command is
reachable via `project_run`, lint is asserted at gate level, and CI runs it. What
remains is ergonomics: structured findings, Observe authority, manifest-derived
scope. Keeping it at High would have overstated the risk.
