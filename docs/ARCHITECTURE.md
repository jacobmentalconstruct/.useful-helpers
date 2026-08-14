# Architecture  -  Useful Helpers (as built)

A local, governed toolkit an agent points at a **target**  -  a codebase, a dataset, a body of
records  -  to understand it, work on it, and stay coherent across sessions. Domain-neutral: the
same instrument serves software, data curation, and records/forensic work.

This describes the system as it is built. The founding precept and the intended design live in
the factory's charter (not shipped); this file is the shipped, accurate map.

---

## 1. The precept (the one rule)

**The sidecar is omni-aware of the target; the target stays totally ignorant of the sidecar.**
Awareness flows one direction only. The toolkit writes no trace of *itself* into the target  -  no
pointer file, no `.gitignore` line, nothing. Delete the sidecar folder and the target does not
notice; move the pair together and it still runs. This is enforced, not merely intended (sec 5).

**The precept is about the instrument's footprint, not about your work.** A governed Apply
operation modifies target content on purpose  -  preview-first, inside a declared write scope, and
recorded in the ledger. Lifecycle phases (install, update, uninstall, startup, self-maintenance)
never touch target-owned content at all; Observe operations never write; Apply may, and is
audited when it does. *"Never writes to the target"* is a misstatement of this rule.

## 2. Four layers

1. **The seam** (`src/core/invoke.py`)  -  the one chokepoint every call passes through.
   Domain- and tool-agnostic: it resolves the tool, enforces the authority ceiling, runs the
   tool as a subprocess, records a governance event, and enforces the precept guard. It never
   imports tool code.
2. **The adapters** (`tools/*/`, `apps/*/`)  -  each is a `tool.json` manifest + a `cli.py`
   exposing one `run(args) -> dict`. Tools never import each other. They are interchangeable,
   manifest-described capabilities.
3. **The cartridges** (`config/cartridges/*.json`)  -  domain knowledge: which tools to mount for
   a kind of target, and what each tool's output is worth there (policy + confidence). Adding a
   domain is adding a JSON file  -  no code.
4. **The front door** (`tools/attach/`)  -  one verb. Probe a target, score it against the
   cartridges, mount a per-target workbench, and hand back a PROJECT_MAP + the next steps. It
   re-engages an already-mapped target or maps a new one. Every workbench also unions a
   **base mount** of universal *hands* (read/glob/search/write/edit/fs/run/diff + memory), so an
   agent never has to leave the seam for ordinary file, search, or command work  -  see `AGENTS.md`.

```
  HUMAN   -> CLI / run.bat ----------+
  AGENT   -> MCP server (stdio) -----+-> core.invoke.invoke(tool_id, args)  <- THE SEAM
  WORKFLOW-> playbook runner --------+        |  authority check - precept guard - audit event
                                              v
                                   <interpreter> tools/<id>/cli.py --args-json {...}
                                        (subprocess; cwd = the work target)
```

## 2a. The two channels

Every call crosses the seam, and the seam feeds **two channels with deliberately
opposite properties.** They are separate because merging them was the mistake
waiting to happen: tool calls are coarse and deliberate, while UI state changes
thousands of times an hour, so a single log would have buried the governed actions
inside the noise.

| | Ledger (`src/core/event_log.py`) | Presence (`src/core/presence.py`) |
|---|---|---|
| Answers | what **happened** | what is **true now** |
| Shape | events, append-only | one overwritten snapshot |
| Lifetime | permanent | dropped on restart |
| Growth | one row per governed action | constant |
| Audited | yes | no |

**The ledger** records every invocation with the `client` that caused it — `cli`,
`agent`, `gui`, `test`. Attribution is *recorded, never used to grant privilege*: a
GUI click and an agent call take the same path and meet the same authority ceiling.
It also records **decisions** — a human granting or refusing an Apply operation —
because that is the moment authority is actually exercised.

**Presence** is state, not events. Asking what the operator is looking at returns an
answer rather than a history to replay. Its field vocabulary is closed, so it cannot
quietly become a second log.

**`src/core/watch.py`** is how a change announces itself. A client holds an opaque
**cursor** and polls; a poll costs well under a millisecond. Callers hold a position,
not a connection, so the transport underneath can change without touching them.

## 3. The registry

`config/registry.json` is discovered from every `tools/*/tool.json` and `apps/*/tool.json` and
is **derived**  -  regenerate it with `python -m src.app cli registry-refresh`. Each manifest
declares: `id`, `summary`, `category`, `authority`, `operates_on`, `writes`, `invocation`,
`input_schema`, `output_shape`. The full catalog is generated into
[TOOLS.md](TOOLS.md) (`docs-refresh`); how to drive the tools is in [OPERATIONS.md](OPERATIONS.md).

## 4. The four runtime roots (the contract that keeps the target clean)

**These are the four *runtime accessors*, not the product's four ownership roots.** The
product's `TARGET_ROOT` / `INSTANCE_ROOT` / `GOVERNANCE_ROOT` / `STATE_ROOT` are defined once, in
the factory's charter, and are not restated here. This table names what a *tool* calls to get a
path. Two of the names correspond; two do not, and conflating them is how one word came to do
four jobs.

`tools/_toolkit.py` is the shared API; no tool re-derives roots ad hoc, and it **transports**
resolved values rather than deciding them  -  a tool that read an environment variable and then
fell back to the working directory would be inferring, which is the defect this replaced.

| Root | What it is | Default for |
|---|---|---|
| **work target** (`project_root`) | what tools operate ON; the seam runs tools with `cwd` here | inputs (`operates_on: project`) |
| **toolkit home** (`suite_home`) | where the instrument lives: code, config, registry | `operates_on: toolkit` |
| **state root** (`state_root`) | durable memory: journal, evidence, event log, workbench  -  survives an update, never cleaned | all persistent state |
| **output root** (`output_root`) | disposable generated artifacts  -  safe to delete | tool outputs |

The rule: **inputs read from the work target; state and output write to the toolkit home; an
explicit path always overrides.** Installed as a sidecar, the work target is the parent project,
so analysis tools default to the whole project while the toolkit's own home is auto-pruned from
scans and its state stays inside the sidecar. Standalone (no install), the work target and
toolkit home coincide  -  which is why "everything inside the instance" and "everything in the
project" are the same set in a development checkout, and any exclusion written as if they differ
will prune the entire tree.

**Where the roots come from.** An installed instance resolves them from its own `instance.json`:
schema, a durable UUID, and the target recorded *relative* to the instance. Uninstalled, they
come from `SUITE_PROJECT_ROOT` / `SUITE_HOME` / `SUITE_STATE_ROOT`. Where an instance exists,
identity wins and a conflicting variable raises rather than rebinding. There is no marker file
and no basename inference.

## 5. Governance and the precept guard

Every call passes an **authority ceiling**  -  `Observe` (read-only) < `Sandbox` (temp/artifacts)
< `Apply` (writes for real)  -  and is appended to an audit event log at the seam. The ceiling
defaults to permissive (`Apply`); clamp it per session (`SUITE_MAX_AUTHORITY`) or per project
(`config/governance.json`). See [PROJECT_GOVERNANCE.md](PROJECT_GOVERNANCE.md).

The **precept guard** makes sec 1 mechanical. Each tool declares `writes: none | toolkit | target`
(inferred from authority when absent; never `target` by default). Under a real sidecar install,
the seam snapshots the target (stat-only) around every **Observe** call and, if a tool that may
not write the target changed it, **fails the call and names what changed**  -  turning a silent
violation into a hard error the instant it happens. Sandbox tools run the project's own code and
Apply tools write by deliberate invocation, so neither is guarded. Disable with
`SUITE_STRICT_OBSERVE=0`. On this platform the guard verifies after the fact (no OS sandbox); the
same `writes` declaration drives a true read-only mount where one is available - and one
is: the factory harness's `mount` command seals the target read-only on Linux, turning the
precept from DETECTION (a diff after the fact) into PREVENTION (the OS refuses the write).
It also proves the sidecar still works against a sealed target - prevention that breaks the
instrument would prove nothing. On hosts without the capability it reports UNAVAILABLE with
a reason, never a pass.

## 6. Memory is the target's memory

`journal` (durable, append-only) and `evidence` (content-addressed proof) live under the state
root and start empty on a fresh install. They accumulate the history of the target, which is what
lets the next agent  -  or you, after context loss  -  pick up the thread. Keep their prose
path-tokened (`<project>`, `<toolkit>`), never raw absolute paths.

## 7. Layout

```
.useful-helpers/                 the sidecar (this toolkit)
|- AGENTS.md                     the front door for agents  -  read first
|- src/                          the control plane
|  |- app.py                     boots cli | mcp | ui
|  |- core/                      registry - invoke (the seam) - policy - event_log - playbook - docs
|  |- interfaces/                mcp_server (agent entrance) - cli
|  |- ui/                        registry-driven GUI (human entrance)
|  `- lib/                       logging - theme - common
|- tools/                        the adapters (one dir each) + _toolkit + _template
|- apps/                         larger adapters (projectmapper)
|- config/                       registry.json (derived) - cartridges/ (domain knowledge)
|- playbooks/                    reusable tool chains (data)
|- _docs/                        this doc - TOOLS.md (generated) - OPERATIONS.md - ONBOARDING.md
|- _state/                       durable memory (journal/evidence/event-log/workbench,
|                                 policy_overrides.json, llm_usage.jsonl)  -  gitignored
|- _artifacts/                   disposable generated output  -  gitignored
`- requirements.txt  run.bat  smoke_test.py  README.md
```

## 8. Entrances

- **Agents:** `python -m src.app mcp` (JSON-RPC 2.0 over stdio)  -  native JSON, no shell escaping.
- **Humans:** `run.bat ui` (browse/run any tool) - `run.bat map` (shareable project snapshot) - `run.bat plan` (plan a new project).
- **CLI:** `python -m src.app cli <version|tool-list|registry-refresh|docs-refresh|tool-call|run-playbook>`.
- **Playbooks:** `python -m src.app cli run-playbook --file playbooks/<name>.json`.

## 9. Adding a capability

`stamp` a skeleton -> implement `run(args) -> dict` -> fill in `tool.json` (id, summary, category,
authority, `operates_on`, `writes`, schemas) -> it is auto-discovered by the registry. Regenerate
the catalog with `docs-refresh`. A capability isn't done until it has been exercised through a
real entrance  -  the smoke suite and the factory harness are how that is proven.
