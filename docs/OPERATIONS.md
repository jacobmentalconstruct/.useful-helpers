# Operations  -  how to actually drive the tools

`TOOLS.md` documents **what** each tool does. This page is the **directional** knowledge  -  the
sequencing, the flags, the escaping realities, and which outputs to trust. It exists because a
real field deployment proved this is where all the friction lives.

## 1. Calling the seam (humans vs programs)

Every call goes through one governed, audit-logged seam:

```
python -m src.app cli tool-call --tool <id> --args-json "{...}"     # humans, simple args
python -m src.app cli tool-call --tool <id> --args-file <path>     # programs, real args
<some-process> | python -m src.app cli tool-call --tool <id> --args-file -    # stdin
python -m src.app mcp                                              # agents: native JSON, no shell
```

**The rule:** the moment args contain arrays, nested objects, quotes, or Windows paths, do NOT
hand-escape JSON in a shell  -  write it to a file (or pipe it) and use `--args-file`, or use the
MCP entrance. The CLI `--args-json` form is for humans typing `{"action":"list"}`.

## 2. One confirm flag: `apply: true`

Every Apply-authority tool is **preview-first**: it does nothing real until confirmed.
Historically each tool had its own flag (`confirm`, `write`, `dry_run:false`)  -  those all still
work, but you never need to guess again:

- **`{"apply": true}` executes for real on every gated tool.**
- Every preview and every "requires confirm" refusal now includes
  `"apply_with": {"apply": true}`  -  the response tells you the exact flag.

## 3. Pointing tools at the work target (roots contract)

Tools run with `cwd = the project` (the sidecar's parent when installed  -  see
[ARCHITECTURE.md](ARCHITECTURE.md) sec 4, the four roots). So:

- **Default is the project.** `{"root": "."}` (or omit it) analyzes the whole project.
- The toolkit's own home is auto-pruned from project scans; state (journal/evidence/audit) and
  generated artifacts stay under the toolkit home. Explicit paths override.
- Each tool declares its subject in `tool.json`  -  `operates_on: "project" | "toolkit"`.

## 4. Understanding an unfamiliar project (the tool-chain, in order, with trust levels)

Run the *deterministic structural* tools first and believe them; treat the *opinionated* tools
as **leads, not verdicts**, and verify every finding by hand before acting.

| # | Tool | What it gives you | Trust |
|---|------|-------------------|-------|
| 1 | `report {"path":"."}` | macro structure  -  purpose/classes/functions/imports per file | **high**  -  orient here first |
| 2 | `import_graph {"root":"<pkg>"}` | internal edges, fan-in/out, **cycles** | **high**  -  cycles are real, high-value |
| 3 | `complexity_score {"root":"<pkg>"}` | function/module hotspots | **high**  -  points at risk directly |
| 4 | `module_decomp_plan {"root":"<pkg>"}` | oversized modules | **high**  -  size is objective |
| 5 | `symbol_graph {"action":"refs","symbol":"X"}` | X's RESOLVED callers/callees + module summary | **high**  -  edges are bound through imports, not name matches; the honesty ledger bounds the rest |
| 6 | `dead_code {"root":"<pkg>"}` | symbols unreachable from every live root | **high** findings are proven over resolved edges (incl. dead clusters); **medium/low** = alive only under a dynamic-dispatch assumption. Verify before deleting |
| 7 | `blocking_call_scan {"root":"<pkg>"}` | blocking calls | **low** for web/CLI code  -  can't see sync-vs-async context |
| 8 | `domain_boundary_audit {"root":"<pkg>"}` | layer crossings (resolved, relative imports anchored) | **low** without a project layering policy  -  flags intended architecture |
| 9 | `secret_audit {"root":"."}` | credential scan | **high** for a first pass |

A less-skeptical agent taking tools 6-8 at face value would delete working commands and "fix"
correct architecture. Confirm findings with `symbol_graph refs` + reading the code before
touching anything.

### Analyzer semantics (why 6-8 are signals, not verdicts)
These now answer from the RESOLVED symbol graph (G6)  -  an edge exists only when a reference
actually binds to its target, so name coincidence is no longer evidence  -  but the labels are
still the point:

- **`dead_code`** proves reachability from live roots. `high` = unreachable under EVERY modelled
  assumption  -  including mutually-referencing dead clusters and name coincidences the old
  counting could not see. `medium` = alive only if a framework dispatches methods dynamically.
  `low` = a live class AND attribute-name matches agree  -  very likely dispatched. Framework
  entrypoints, `__all__` exports, and interface overrides (resolved base classes) are ROOTS:
  provably live, no longer listed as noise. The `honesty` ledger (dynamic dispatch, star
  imports) bounds what "unreachable" proves. Extend recognized decorators with
  `entrypoint_decorators: ["..."]`.
- **`blocking_call_scan`** splits `findings` (blocking call whose *nearest enclosing function* is
  `async def`  -  can stall the event loop) from `informational` (the same call in sync code, e.g.
  a CLI function or a FastAPI sync handler run in a threadpool  -  **not a defect**).
- **`domain_boundary_audit`** emits **no pass/fail without a policy**
  (`verdict: "none"`; crossings are neutral facts). Supply one inline or select a
  sidecar-owned profile:
  ```json
  { "layers": {"cli": "adapter", "web": "adapter"},
    "allowed_edges": ["adapter->application", "application->domain"] }
  ```
  Profiles live under `config/domain-boundary/<name>.json` in the toolkit and are selected
  with `policy_profile`. Project-specific JSON profiles are gitignored, so the work target
  remains unaware of the instrument. Same-layer and declared edges pass; reverse edges fail.
  Unmapped domains are reported and treated as strict distinct layers. The output includes
  `policy_source`, `policy_status`, available profiles, and layer names on crossings.
  The legacy project-root `.uh-policy.json` auto-read remains supported.

## 5. The bd-graph build -> inspect -> retrieve loop

```
bd_index   {"path":"<pkg>", "apply": true}      # split -> emit -> scribe into the graph DB
bd_status  {}                                   # table presence + row counts
bd_query   {"query":"<question>", "top_k":3, "hops":2}   # ranked anchors + projected subgraph
bd_project {"occurrence_ids":[...], "hops":2}   # neighborhood around known nodes
```
The DB lives under the toolkit home (`_artifacts/bd_graph/`). Read results as: `anchors` =
ranked entry points; the projected subgraph = the neighborhood to actually reason over.

## 6. Memory discipline (journal + evidence)

- **Record work:** `journal {"action":"add","title":..,"summary":..,"files":[..],"decisions":[..]}`
- **Ground claims:** `evidence {"action":"attach","kind":"tool_output","summary":..,"body":..,
  "attached_to":<journal_uid>,"attached_to_type":"journal"}`
- **Path-token discipline:** the journal exports a committed Markdown mirror. Never write an
  absolute machine path (a full `C:\...` path) into journal/evidence prose  -  use `<project>` /
  `<toolkit>` tokens. (The event log and suite.log scrub themselves; your prose is on you.)

## 7. Verifying a running app

The toolkit deliberately has no browser. For local servers, pair `dev_server_manager` with your
agent environment's own HTTP/browser capability, and record outcomes to `journal`/`evidence`.

## 8. Tuning a cartridge for YOUR target (policy overrides)

A cartridge encodes what is generally true of a domain. When it is wrong about *your* target,
override it instead of arguing with it - and the override **survives `attach {"refresh": true}`**.

Write `<state_root>/policy_overrides.json` (state root, not the workbench - the workbench is
rewritten by refresh, the state root is durable memory):

```json
{
  "*": {
    "dead_code": {
      "confidence": "low",
      "note": "OPERATOR: entrypoints are registered by decorator here; treat leads as suspect.",
      "tool_args": { "root": "src" }
    }
  }
}
```

- Key by absolute target path, or `*` for every target this sidecar attaches to.
- `tool_args` merges **key-wise**, so pinning one argument keeps the cartridge's others.
  Every other field replaces outright.
- Overridden entries come back marked `"overridden": true`, and `workbench.policy_overrides`
  lists which tools were touched - an agent can always see that it is reading operator policy
  rather than detected policy.
- Overrides apply at READ time and are never written into `profile.json`. The stored profile
  stays a faithful record of what was **detected**; the override is a separate, visible record of
  what you **decided**. That separation is exactly why refresh cannot clobber it.
- A malformed override file degrades to "no overrides" rather than taking the front door down.

## 9. What local inference has cost (`ollama_gov usage`)

Every local-model call in the toolkit - `attach`'s synopsis, `bd_index`'s embeddings, `delegate`'s
loop, and direct `ollama_gov run` calls - goes through one governed seam and is recorded with the
**purpose** that spent it.

```
ollama_gov {"action": "usage"}          -> totals by purpose + the recent call records
ollama_gov {"action": "usage", "limit": 0}  -> totals only
```

Chat calls are logged one record each (few, individually expensive). Embeddings are counted and
flushed as a single rollup line per process - an index run makes thousands, and a log nobody can
read is not governance. The embed count reflects **actual backend calls**, so it is lower than the
node count when the in-process cache absorbs duplicate text; that is the honest cost number.

`SUITE_LLM_DISABLE=1` disables all local inference globally; every caller degrades honestly
(structural map, lexical retrieval, no delegation) rather than failing opaquely.
