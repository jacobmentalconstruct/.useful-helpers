# Architecture  -  Useful Helpers (as built)

A local, governed toolkit an agent points at a **target**  -  a codebase, a dataset, a body of
records  -  to understand it, work on it, and stay coherent across sessions. Domain-neutral: the
same instrument serves software, data curation, and records/forensic work.

This describes the system as it is built. The founding precept and the intended design live in
the factory's charter (not shipped); this file is the shipped, accurate map.

---

## 1. The precept (the one rule)

**The sidecar is omni-aware of the target; the target stays totally ignorant of the sidecar.**
Awareness flows one direction only. The toolkit writes nothing into the target  -  no pointer
file, no `.gitignore` line, nothing. Delete the sidecar folder and the target does not notice;
move the target and it still runs. This is enforced, not merely intended (see sec 5).

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

## 3. The registry

`config/registry.json` is discovered from every `tools/*/tool.json` and `apps/*/tool.json` and
is **derived**  -  regenerate it with `python -m src.app cli registry-refresh`. Each manifest
declares: `id`, `summary`, `category`, `authority`, `operates_on`, `writes`, `invocation`,
`input_schema`, `output_shape`. The full catalog is generated into
[TOOLS.md](TOOLS.md) (`docs-refresh`); how to drive the tools is in [OPERATIONS.md](OPERATIONS.md).

## 4. The four roots (the contract that keeps the target clean)

`tools/_toolkit.py` is the shared API; no tool re-derives roots ad hoc.

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
toolkit home coincide.

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
