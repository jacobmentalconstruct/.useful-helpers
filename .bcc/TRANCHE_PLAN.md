# Tranche Plan

Status: **DRAFT for operator agreement.**
Date: 2026-08-06.
Authority: subordinate to `CHARTER.md`; procedure defined by `TRANCHE_PROTOCOL.md`.

Numbering starts at **T0** and is this project's only valid numbering. Every
identifier in archived material belongs to a predecessor project.

Each tranche states its outcome, its gate, and its non-goals. The gate is
written during declaration, before implementation.

---

## Sequence

| # | Tranche | Proves |
| --- | --- | --- |
| T0 | Foundation and Reset | **CLOSED** — a blank, unified project with one authority |
| T1 | One Ship Manifest | The sidecar vends only itself, and blank |
| T2 | Ledger and Presence | The seam contract exists in code |
| T3 | Live Channel | E6a, E6b |
| T4 | Cancellation and Progress | Long work is observable and stoppable |
| T5 | One Surface | E3 |
| T6 | Contracts for Uncontracted Daily Drivers | Ten contracts exist |
| T7 | Chains | E7 |
| T8 | Retire `apps/` | One extension shape, not two |
| T9 | Install and Packaging | E1, E2, E4 |
| T10 | Closure | E8, E9, E10 |

Ordering rationale: safety before capability (T1 precedes everything that acts);
the seam contract before the surface that displays it (T2–T4 precede T5); the
surface before the chains that live in it (T5 precedes T7).

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

1. Declare the manifest once, in one module, as the single source of truth.
2. Derive `vendor_export`'s exclusion sets from it.
3. Derive the harness's `_PAYLOAD_EXCLUDE` from it.
4. Derive both test scoping sets from it.
5. `ruff.toml` is static TOML and cannot import — so the **gate** asserts it
   remains consistent with the manifest rather than silently drifting.
6. Ship a minimal payload `.gitignore` covering the sidecar's own `_state`,
   `_artifacts` and `logs` — not the development one, which names the parts bin
   and harness.
7. Resolve `packaging/`: it is stripped from the vend while the installer is
   deliverable #1. Record the decision explicitly rather than leaving it implied.
8. Implement charter condition **E11** — vends blank.

**Gate — `gates/t01_ship_manifest.py`**

- one manifest module exists and declares the payload boundary
- every consumer derives from it; no independent literal exclusion lists remain
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

## T3 — Live Channel

**Outcome.** Each party sees the other act, live, and can query the other's
context. **E6a and E6b.**

**Work.** Settle the transport (charter §6.5). Publish ledger appends and
presence changes to subscribers. Both an in-process GUI client and an
out-of-process agent client.

**Gate — `gates/t03_live_channel.py`**

- an action by client A is observed by client B without restart or manual refresh
- a context query returns the other party's current target, selection and
  inclusion set
- a dropped subscriber does not block or corrupt the seam
- presence loss does not affect ledger integrity

**Non-goals.** No derived visible-state (deferred; charter §6.4 level 2).

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

## T5 — One Surface

**Outcome.** A single Tkinter shell reaches every tool and every chain. **E3.**

**Work.** Unify `registry_view`, `mapper_view`, `planner_view` and
`installer_view` into one shell: explorer, context, tool workspace, event view.
Theme is already implemented in `src/lib/theme.py`. UX intent is supplied by the
`_UsefulHelperScriptsMENU` filedump — `minsize(900, 600)`, double-click launch,
mousewheel binding on all scrollables, non-truncating button rows.

**Gate — `gates/t05_surface.py`**

- every registered tool and chain is reachable from one shell
- no capability requires a second command or window
- the shell renders live ledger and presence
- startup and clean shutdown succeed headlessly
- browse selection and operation inclusion are separate state domains

**Non-goals.** No new capability. No chains yet.

---

## T6 — Contracts for Uncontracted Daily Drivers

**Outcome.** All ten retained daily drivers have contracts.

**Work.** Write contracts for `_TempServerMAKER`, `_MicroserviceLIBRARY` and
`_NoStringsPDF` from their filedumps and READMEs, in the shape of the existing
twelve. Record measured toolkit coverage per capability.

**Gate — `gates/t06_contracts.py`**

- ten contracts exist, each naming capabilities, safety rules and non-goals
- every capability maps to an existing tool, a named gap, or an explicit
  out-of-scope decision

**Non-goals.** No implementation.

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

**Outcome.** The sidecar installs into an arbitrary directory on a clean machine
and is fully reachable by an agent. **E1, E2, E4.**

**Work.** Install path, fresh-environment verification, offline behavior, MCP
surface parity, Windows verification.

**Gate — `gates/t09_install.py`**

- installs into an empty scratch directory and `attach` returns a map
- `attach` succeeds on code, data-curation and records targets
- the MCP tool list equals the registry
- no network is required by any core capability
- the target contains no sidecar artifact after uninstall

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

## Backlog

| Item | Origin |
| --- | --- |
| `VERSION` does not move when tools change | Charter §7.4 |
| Precept-guard cost unmeasured on large targets | Charter §7.3 |
| Windows behavior wholly unverified | Charter §7.5 |
| `developer_cert.pfx` should leave the tree | Operator action |
