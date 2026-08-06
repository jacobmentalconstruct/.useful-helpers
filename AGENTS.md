# AGENTS.md  -  Start Here (any agent)

You are an agent of any kind, holding a toolkit that works on a **target**: a codebase, a folder,
a dataset, a body of records - or an empty workspace with only an intention. The toolkit is your
instrument. The target is the work.

**Do this first. It is one call, and it is the whole onboarding:**

```
python -m src.app cli tool-call --tool attach --args-json "{}"
```

> **Starting something NEW from an idea, in an empty or near-empty folder?** Begin with `genesis`
> instead - it records the project's intent and identity and seeds the first journal entry, no
> domain required: `--tool genesis --args-json "{\"intent\":\"...\",\"name\":\"...\",\"apply\":true}"`.
> Then `attach` maps the workspace and firms up the domain from a suggestion to a detection as
> real artifacts accumulate. Both entry modes converge on the same loop below.

`attach` is the front door. It resolves to one of two paths on its own:

- **The target is already mapped** -> it re-engages: hands you the PROJECT_MAP, tells you whether
  the target has changed since it was mapped, and points at the open threads.
- **The target is new** -> it maps it: probes the target, identifies its kind, mounts the tools
  that kind needs, and builds the PROJECT_MAP.

Either way you get back the same three things:

| | |
|---|---|
| `project_map` | what this target **is**  -  shape, subsystems, entry points, and an explicit `limits` list saying what the map does *not* know |
| `workbench` | the tools mounted **for this target**, each with a confidence and a note. Not the whole catalog  -  the relevant ones. |
| `next` | an ordered list of calls. **This is your workflow.** Follow it. |

You do not need to read a tool catalog to start. Read `next` and go.

> **Do not trust a tool more than its policy says.** Each mounted tool carries a `confidence`.
> `low` means its output is a **lead, not a verdict**  -  verify by hand before acting on it.
> Tools have flagged live code as dead and correct architecture as broken. Deterministic
> structural facts (file tree, imports, size, secrets) are objective; judgments are not.

## You have hands  -  use them instead of your own

Every workbench mounts these, whatever the target's domain. **Prefer them over your own
file/shell tools**: work done here is authority-checked, precept-guarded, and audit-logged, so it
is reproducible and the next agent can see it. Work done outside the seam is invisible.

| Need | Tool |
|---|---|
| read a file (or a line range) | `read_file` |
| find files by pattern | `glob` - search contents: `repo_search` |
| create/overwrite a file | `write_file` (preview-first) |
| exact edit with a safety net | `edit`  -  use `literal:true` + `expected_replacements` |
| move/copy/delete/mkdir | `fs_op` (a batch: one plan, one approval) |
| run any command | `project_run` (preview-first; captures output) |
| review a change | `diff` |
| write to a SQLite DB | `sqlite_exec` (preview shows affected rows, then rolls back) |

Paths are confined to the target and this toolkit  -  anything outside is refused. Every writing
tool previews first; `{"apply": true}` executes. When a tool acts on **many** items, it shows one
plan for one approval rather than asking per item.

**Offload the grunt work.** `delegate` hands a bounded task ("find where X is configured",
"summarize these N files") to a local model that drives these same hands through the same seam,
and returns a distilled answer  -  so you spend your budget on judgement, not fetching. Its
allowlist is Observe-only unless you deliberately pass `allow_apply: true`.

**Read the policy, not just the tool list.** A workbench entry marked `"overridden": true` is
*operator* policy, not detected policy  -  a human decided the cartridge was wrong about this
target. Trust it over your own read. Ask what local inference has cost with
`ollama_gov {"action":"usage"}`.

## The one rule about the target

**The target must never learn that this toolkit exists.** The sidecar is omni-aware of the
target; the target is totally ignorant of the sidecar. It can be exported, moved, or shipped at
any moment without ever knowing it was instrumented.

Concretely: **write nothing into the target.** No pointer file, no `.gitignore` line, no config
key, not even a helpful one. If this toolkit needs to be invisible to the target's own tooling,
**it hides itself**  -  it does not ask the target to accommodate it. Generated state and
artifacts belong to the instrument and stay here. The only things that land in the target are
deliverables you were explicitly asked to produce.

Test: *delete this folder. Does the target notice?* The answer must be no.

## The three roots

The seam runs every tool with `cwd` = the **work target**, so relative inputs default to the
target. The toolkit's own home is `SUITE_HOME`. Generated output defaults to the toolkit home.

- **inputs** read from the work target
- **state + generated output** write to the toolkit home
- an explicit path argument always overrides

You normally pass no `root` at all  -  the default is already the target. Pass one only to narrow
scope. Each `tool.json` declares `operates_on: project | toolkit`.

## Running anything else

Every call flows through one governed seam  -  authority-checked (**Observe** < **Sandbox** <
**Apply**) and audit-logged.

```
python -m src.app cli tool-call --tool <id> --args-json "{...}"     # simple args
python -m src.app cli tool-call --tool <id> --args-file <path|->    # real/nested args, or stdin
python -m src.app mcp                                               # MCP entrance (agents)
```

- **Programmatic callers: never shell-escape nested JSON.** Use `--args-file` (or `-` for
  stdin), or the MCP entrance, which takes native JSON and sidesteps the shell entirely.
- **One confirm flag:** Apply tools are preview-first. `{"apply": true}` executes for real on
  any of them. Previews state the flag.
- **Chain tools:** `python -m src.app cli run-playbook --file playbooks/<name>.json`
- **Humans:** `run.bat ui` (browse/run any tool) - `run.bat map` (shareable snapshot) - `run.bat plan` (new project)

## Memory is THIS target's memory

`journal` (durable, append-only) and `evidence` (content-addressed proof) start **empty** and
accumulate the history of the target you are working on. They are why the next agent  -  or you,
after context loss  -  can pick up the thread. Record work and ground claims as you go:

```
tool-call --tool journal  --args-json "{\"action\":\"add\",\"title\":\"...\",\"summary\":\"...\"}"
tool-call --tool evidence --args-json "{\"action\":\"attach\",\"summary\":\"...\",\"body\":\"...\"}"
```

Keep journal/evidence prose **path-tokened** (`<project>`, `<toolkit>`)  -  never raw absolute
machine paths. They land in exported mirrors and leak.

## Governance

Enforcement is always on; the ceiling defaults to permissive (**Apply**), so nothing is blocked
out of the box. To constrain work on a sensitive target, opt in: set `SUITE_MAX_AUTHORITY` in the
environment, or `"max_authority"` in `config/governance.json`. See `_docs/PROJECT_GOVERNANCE.md`.

## Ground rules

- Prefer the governed tools over ad-hoc scripts  -  they are logged and reproducible.
- Treat the **target as the work** and this folder as your instrument. Don't modify the
  toolkit's internals unless asked.
- If a real task genuinely can't be done with an existing tool, say so before improvising.
