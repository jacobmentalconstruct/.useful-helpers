# AGENTS.md  -  Start Here (any agent)

You are an agent of any kind, holding a toolkit that works on a **target**: a codebase, a folder,
a dataset, a body of records - or an empty workspace with only an intention. The toolkit is your
instrument. The target is the work.

**Do this first. It is one call, and it is the whole onboarding:**

```
.useful-helpers\run.bat attach       :: Windows, from the target root
sh .useful-helpers/run.sh attach     :: Linux / macOS, from the target root
run.bat attach  /  sh run.sh attach  :: from inside the instance directory
```

**Invoke the launcher by path.** It is not on `PATH`. Each launcher resolves its own
directory and changes into it, so the working directory you start from does not matter
 -  but the path you type has to reach the file. The raw form is
`python -m src.app cli tool-call --tool attach --args-json "{}"`, which additionally
requires the instance directory as the working directory  -  prefer the launcher.

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

> **Use the identifier the tool gave you. Never reconstruct one from prose.**
> These tools answer on exact identities  -  `src.backend::Backend`, a real table name, a real
> relative path  -  and refuse politely when you invent something plausible instead. If a summary
> says "the backend module is the hub", do not query `CellBackend` because the project is called
> `_theCELL`; query the handle the summary carried. A tool that refuses a name you made up is
> working correctly, and reading that refusal as a missing capability wastes a whole
> investigation. When you are unsure of a handle, list before you query.

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

Concretely: **leave no trace of the instrument.** No pointer file, no `.gitignore` line, no
config key, not even a helpful one. If this toolkit needs to be invisible to the target's own
tooling, **it hides itself**  -  it does not ask the target to accommodate it. Generated state and
artifacts belong to the instrument and stay here.

**This is not "never write to the target."** A governed Apply operation modifies target content
deliberately  -  that is what `write_file`, `edit`, `fs_op` and the rest are *for*. The rule is
about *whose* content it is:

| | May be written | |
|---|---|---|
| the instrument's own state, artifacts, journal, evidence | **here**, inside this folder | always |
| the work you were asked to do | **the target** | only through a governed Apply, inside its declared write scope, preview-first, recorded in the ledger |
| a trace of the instrument's existence | **nowhere in the target** | never, under any authority |

Installation, update, uninstall, startup and self-maintenance never touch target-owned content
at all. Runtime Apply may, and is audited when it does.

Test: *delete this folder. Does the target notice?* The answer must be no  -  aside from the
deliverables you were explicitly asked to produce, which are the user's, not the sidecar's.

## The three roots

The seam runs every tool with `cwd` = the **work target**, so relative inputs default to the
target. The sidecar's own home is `SUITE_HOME`. Generated output defaults to the sidecar home.

- **inputs** read from the work target
- **state + generated output** write to the sidecar home
- an explicit path argument always overrides

Each `tool.json` declares `operates_on: project | toolkit`.

### How the work target is decided

**By canonical identity, structurally.** An installed instance carries an
`instance.json` manifest naming its own schema, a durable UUID, and the target's
path *relative to the instance*. Nothing absolute is written down, so moving the
target and its sidecar together keeps the relationship intact.

| Situation | Evidence | Target |
|---|---|---|
| Installed instance | `instance.json` present and valid | the recorded relative target (the instance's parent) |
| Installed, manifest broken | `instance.json` present and invalid | **hard error** - never a fallback guess |
| Not installed, explicit root | `SUITE_PROJECT_ROOT` names a real directory | that directory |
| Not installed, invalid root | `SUITE_PROJECT_ROOT` names nothing | **hard error** |
| Neither | no manifest, no variable | **no target - every call refuses** |

Two rules do the work here. **Absent is not malformed:** no manifest means "this is
not a canonical instance", which is an answer, not a failure. **Identity outranks
the environment:** where an instance exists, a conflicting `SUITE_PROJECT_ROOT`
raises and names the instance UUID rather than silently rebinding it. The variable
governs only the uninstalled case.

There is **no marker file and no basename inference**. Earlier builds bound to the
parent on sight of a `.suite_sidecar` marker or a dot-prefixed folder name; both are
gone. If you find a surface still describing them, it is stale.

If you are working in the sidecar's own source repository rather than in an installed
copy, there is no target and tool calls refuse with `no work target bound`. That is
correct behaviour, not a fault. Supply an explicit `SUITE_PROJECT_ROOT`, or work in an
installed sidecar.

### Scope is not rebinding

Passing a `target` argument narrower than the bound target is a **narrower view of
the same reality** and is allowed. Passing one outside it is asking this instance to
be a different instance, and is refused. The rule is containment, not equality.

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

## You are not working alone

A human may be working on this same target at the same time, through the GUI. The
seam keeps you both visible to each other, and neither of you is privileged.

**Everything you do is attributed.** Your calls are recorded as `client=agent`, the
operator's as `gui`. That is for visibility, not permission - you meet the same
authority ceiling they do.

**You can see what they did.** The ledger is readable, oldest first, and includes
their actions alongside yours. It also records **decisions** - when a human approves
or refuses an Apply operation. If your proposal was declined, that is a fact you can
read rather than infer from silence.

**You can see what they are doing now.** Presence answers the current question -
which project is bound, what they have selected, what is included for the next
operation, which chain is running. It is a snapshot, not a history: ask and get an
answer.

**And you can notice a change without polling blindly.** `watch` hands you a cursor
and tells you what has happened since it. A quiet channel returns nothing, so a poll
loop stays cheap.

The practical consequence: before assuming a file is untouched or a decision is
still open, look. The record is shared on purpose.

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
