# Charter — Useful Helpers Sidecar

Status: **DRAFT for operator agreement.** Nothing is built against this yet.
Date: 2026-08-06.
Authority: this document, with `.bcc/BUILDER-CONSTRAINT-CONTRACT.md`, supersedes
all prior framing. The former governing blueprint is retired to `_trash/`.

---

## 0. Two Deliverables

The product is **an installer and a payload**, not one application.

1. **The installer.** A GUI that lets the operator pick a folder and vend a
   sidecar into it. That folder becomes the sidecar's root, parent, and entire
   reality.
2. **The sidecar payload.** What gets installed, and what then operates on the
   bound target through its single surface.

They have different lifetimes and different users. `installer_view` is the first;
`registry_view` and the unified surface are the second. They do **not** merge.

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
| E8 | The target is never modified without authority | Precept guard passes; read-only mount prevention passes where the host supports it |
| E9 | The parts bin can be deleted and everything still passes | Delete the bin, run the full gate suite green |
| E10 | Every claim in the docs is executable | No document asserts a behavior with no check behind it |
| E11 | It vends fully blank | Vend to a scratch dir; assert no journal, event log, evidence, development document, git history, build-machine path, or predecessor reference survives |
| E12 | An installed sidecar is removable without trace | Vend, use, delete the sidecar folder; the target is byte-identical to before the vend |

### 3.1 What is already true

Recorded so the remaining work is not overstated. All verified this session by
execution, not inspection.

- 95 registered tools; control plane is standard-library only; runs on Linux and
  Windows.
- One governed seam with authority ceiling, path containment, and audit log.
- The GUI already crosses the seam (`installer_view.py:131`).
- MCP entrance exists.
- Domain cartridges exist for data-curation and records-research.
- `THEME_SPEC.md` is fully implemented in `src/lib/theme.py` — five colours and
  both fonts match exactly.
- Chains exist as `playbooks/` with a `run-playbook` runner.
- Tool creation is supported and safe: `_template/`, `stamp`, `registry-refresh`.
- 79 distinct tools were exercised against the real daily-driver tree on
  2026-07-18: 124 ok, 19 failed. Preserved in `.bcc/evidence/`.

### 3.2 What is genuinely unbuilt

Short list, deliberately.

1. **A live event channel.** `event_log.py` exposes only `record()`. There is no
   read, tail, or subscribe. E6 has nothing under it today, and it constrains
   the GUI's shape, chain progress reporting, and agent observation. **This is
   the load-bearing gap.**
2. **One surface.** Four views exist and are reached by four separate commands.
   They must become one shell. Theme and UX intent are already supplied.
3. **Chains for the daily drivers.** Three playbooks exist; the app-shaped ones
   do not.
4. **Cancellation and progress.** The seam blocks on `subprocess.run` with a
   fixed 120 s timeout and no cancel path.
5. ~~**Explicit-target install.**~~ **RESOLVED 2026-08-06.** Root resolution now
   works by evidence only, in four cases with no fallthrough: an explicit valid
   root binds to it; an explicit *invalid* root is a hard error; a `.suite_sidecar`
   marker binds to the parent — correct, because an installed sidecar's parent
   genuinely is its whole reality; and otherwise there is **no target** and calls
   refuse rather than guess. The folder-name heuristic is removed: a dot-prefixed
   name was making this repository bind to its own parent staging folder.
   Verified end to end — vend into a scratch folder, the sidecar binds to it,
   sees its files, and leaves no trace.

6. **The vend manifest.** `_PAYLOAD_EXCLUDE` in the harness and
   `CLEAN_APP_STRIP` in `vendor_export` both describe what ships. They must
   become one declared manifest, and it must satisfy E11.

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

## 5. Zones

| Zone | Role | Ships? |
| --- | --- | --- |
| `toolkit/` | **The sidecar.** The product. | **Yes** — this is the deliverable |
| `_design/` | Charter, plan, audits governing the sidecar | No |
| `_harness/` | Proving ground; installs the sidecar into targets and measures | No |
| `.bcc/` | Builder contract, plan, evidence, this charter | No |
| `_docs/` | Builder journal | No |
| `.plans-and-parts_FOR-REFERENCE-ONLY/` | Parts bin — daily drivers and their contracts | No — deleted at E9 |
| `_trash/` | Removal staging; the mount denies unlink | No |

The repository root is a **factory**. It has no runtime of its own and must
never acquire one. `harness.py` encodes this: `FACTORY = HERE.parent`,
`TOOLKIT = FACTORY / "toolkit"`.

The toolkit stays nested because it depends on the factory for its verification,
and the factory never travels with it.

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
  is retired into a chain; note the registry currently draws one registered tool
  from `apps/`, so the count moves from 95 to 94 when it goes.

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

### 7.2 The most dangerous defect

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

- A tool emitting unparseable output is treated as **success** with
  `{"raw_stdout": ...}`. A silent tool passes. Must be treated as failure.
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
- **All Windows-specific behavior is unverified**: `run.bat`, the Tk entrances,
  venv interpreter resolution, Windows path handling. A Windows shell is required
  and the development environment cannot supply one.
