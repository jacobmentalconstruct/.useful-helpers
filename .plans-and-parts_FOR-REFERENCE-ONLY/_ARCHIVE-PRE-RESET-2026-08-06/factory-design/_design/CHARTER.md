# Useful Helpers — Charter

**Status:** founding document · **Date:** 2026-07-16
**Audience:** the developer/agent building the toolkit. This file **never ships**.

---

## 1. The precept (non-negotiable)

> The sidecar lives, dies, and is omni-aware of the project, whilst the project remains in
> **total ignorance** of the sidecar. The sidecar is our presence in the project, BUT the
> project can be exported out at any moment without ever even realizing it was moved
> (pending an env install/update at the new location).

Awareness flows **one direction only**. Consequences, stated as hard rules:

- The sidecar writes **nothing** into the host project. Not a pointer file at the host root,
  not a `.gitignore` line, not a config key. Nothing.
- If the sidecar must be invisible to the host's tooling, **the sidecar hides itself** — it
  does not ask the host to accommodate it.
- Any design that requires editing a host file to function is **disqualified**, however
  convenient.
- Test of compliance: *delete the sidecar folder. Does the project notice?* If yes, we failed.
- Inverse test: *move the project. Does it still run?* If no, we failed.

**Every prior attempt violated this.** In the pre-scrub copy the violation was a shipped
default, not an accident: `tools/sidecar_install/tool.json` defaulted `write_agents: true`
(drop `AGENTS.md` into the host root) and `gitignore: true` (append the sidecar to the host's
`.gitignore`). The installer's out-of-the-box behavior was to brand the host.

---

## 2. The intent (what this is for)

An agent is pointed at a target — a codebase, a folder, a body of records, a dataset. It should
see **one door**, open it, and immediately be either:

- **re-engaged** with a target the sidecar has already mapped (it knows this place), or
- **mapping** a target it has never seen.

No reading a tool catalog. No choosing among 87 things. One door, two paths.

The purpose across time is **coherency and direction of development** — the sidecar is the
memory and the through-line that survives context loss, agent swaps, and long gaps.

### Domain generality is a first-class requirement

This is **not** a Python-development toolkit. The same instrument must serve:

- software development (Python apps, web design, ...)
- data curation
- comprehending a body of data / text / case files / records
- forensic and case work, research, report generation

A tool that hardcodes one domain's opinions cannot serve the others. See §4.

---

## 3. The architecture (translated from intent)

Four layers. Only layer 3 is genuinely new; layers 1–2 largely exist already.

### Layer 1 — The seam (the generic multitool)
`src/core/invoke.py`. Domain-agnostic, project-agnostic, never varies. It resolves roots,
enforces the authority ceiling, audit-logs the call, and runs the adapter as a subprocess.
It knows nothing about what any tool does.

### Layer 2 — The adapters (the tools)
Each tool is `tool.json` (id, category, authority, `operates_on`, input/output schema) plus a
`cli.py` exposing exactly one function, `run(args) -> dict`. Tools never import each other.
They are already interchangeable, manifest-described adapters — this was true before the scrub
and is the toolkit's best existing property.

**The adapter contract must gain:** declared *subject* (`operates_on: project | toolkit` —
already present, must be honored by defaults), declared *scoping class* (boundary-guarded vs
path-taking — currently you only learn this when it errors), and declared *policy surface*
(what config this tool reads instead of assuming).

### Layer 3 — The profile (the missing layer; the real work)
A per-target manifest that configures the instrument for **this** engagement:

- `mounted` — which tool ids are on the workbench. The agent faces 12 relevant tools, not 87.
- `policy` — per-tool configuration: the layer map, framework hints, ignore rules, thresholds.
  This is what makes an opinionated analyzer usable on an unfamiliar architecture.
- `domain` — what kind of engagement this is (`python-app`, `web-design`, `data-curation`,
  `records-research`, ...), which selects a base cartridge.

Profiles **compose**: base ← domain cartridge ← target overrides. They live in the sidecar,
never in the target (§1).

> **On the SQLite toolbox.** The original framing was "pack the toolbox into a SQLite db with
> a manifest; the agent unpacks the toolset it needs." The *need* underneath — one door, a
> manifest, a workbench assembled for this target — is exactly right and is met by the profile
> layer. The *mechanism* is rejected: packing tools into a database makes them opaque to grep,
> diff, and in-place edit, on an instrument whose whole job is to be inspected and modified by
> agents. Selection is orthogonal to storage. Tools stay as inspectable folders.
>
> **The instinct was aimed at the wrong target, not wrong.** There *is* one portable SQLite
> file at the heart of this — it holds the **project's map**, not the toolbox. See Layer 4.

### Layer 4 — The front door (`attach`)
**One verb.** The entry point an agent sees immediately.

```
attach(target)
  ├─ no profile + no map  →  MAP:       probe target → propose profile → index → build PROJECT_MAP
  └─ profile + map exist  →  RE-ENGAGE: load PROJECT_MAP → check staleness → surface journal → orient
```

`attach()` returns a **PROJECT_MAP**: purpose, shape, entry points, subsystems, open threads.
The acceptance bar: *a fresh agent calls `attach()` and can state the target's purpose,
architecture, entry points, and subsystems **without reading a file**.*

Behind `attach` sit a small, stable verb set (per field report §G8): `query`, `project`,
`expand`, `why`, `neighbors`. An agent binds to these once and reuses them on any target.

**The map is one portable SQLite file.** Content-addressed, incremental, self-contained. This
is the "external drive you plug in and wear" — and it is where the SQLite instinct actually
belongs.

---

## 4. Policies over verdicts (the generality mechanism)

From the field report's thesis: *"a strong idea trapped behind rigid, specific assumptions...
built as if it **is** the project."* Several analyzers encode **one** valid architecture and
report **other** valid architectures as defects — `dead_code` flagged live framework-invoked
CLI commands; `blocking_call_scan` flagged correct synchronous calls; `domain_boundary_audit`
reported intended layering as 239 violations.

An agent trusting them would have deleted working code and "fixed" a correct architecture.

**Rules:**
1. An opinionated tool reads its policy from the **profile**. Absent a policy it emits
   **signals with confidence**, never pass/fail verdicts.
2. Deterministic structural facts (file tree, import edges, size, complexity, secrets) may be
   stated plainly — they are objective.
3. Judgments (dead, blocking, violating) are **leads, not verdicts**, and must be labeled as
   such in the output itself, so a less-skeptical agent cannot mistake them.
4. A tool that cannot express its finding as either an objective fact or a confidence-ranked
   lead does not belong on the workbench.

**This is why the generality problem is a policy problem, not a packaging problem.** Packing
opinionated tools into a database yields opinionated tools in a database.

---

## 5. The three roots (the contract that prevents most bugs)

The field report's single highest-leverage recommendation. Three distinct roots, conflated
tool-by-tool in the old code, each conflation a bug:

| Root | Meaning | Default for |
|---|---|---|
| **work target** (`SUITE_PROJECT_ROOT`, tool `cwd`) | what we operate on | tools with `operates_on: project` |
| **toolkit home** (`SUITE_HOME`) | where the instrument lives | tools with `operates_on: toolkit` |
| **output root** | where generated state lands | **always** toolkit home unless explicitly overridden |

**Inputs read from the work target; outputs land in the toolkit home.** Outputs defaulting to
the work target is a §1 precept violation — it litters the project with sidecar artifacts.

This must be a **shared helper API** (`suite_home()`, `project_root()`, `output_root()`,
`toolkit_home_names()`) that every tool uses, so no tool re-derives roots ad hoc and a new tool
cannot regress it. In the old code this was applied by hand, per tool, with no shared
convention — which is exactly why it kept breaking.

---

## 6. Understand vs. operate

The field report's other structural finding: the toolkit is *"rich in understand / remember /
package verbs and nearly empty in execute-the-project verbs."* Every high-impact action
(running tests, driving the app, committing) happened **outside** the governed seam — meaning
the most consequential operations were the ones **not audit-logged**. A governance blind spot
precisely where governance matters most.

A later re-vend added `project_run`, `http_probe`, `fetch`, `git_inspect`, `dev_server_manager`.
Verify these against the contract during triage rather than assuming they are correct.

---

## 7. Factory vs. product (how this workspace is laid out)

```
.useful-helpers/                  <- the FACTORY (this sandbox; never ships)
  _design/                        <- charter, requirements, scrub audit
    prior-life/                   <- quarantined prior-project material (design input only)
  toolkit/                        <- the PRODUCT: the clean sidecar that gets vended
  .dirty-helpers-.../             <- the disembodied source; mined, then deleted
```

The factory knows all about the product; the product knows nothing of the factory — the same
asymmetry as §1, one level up. Nothing in `_design/` may be referenced by anything in
`toolkit/`.

---

## 8. Acceptance (how we know we're done)

1. **Precept:** deleting the sidecar leaves zero trace in the target. Moving the target breaks
   nothing. Verified by test, not by inspection.
2. **Front door:** a fresh agent with no context runs one command and is oriented — mapped or
   re-engaged — without reading a catalog.
3. **Generality:** the same instrument maps a Python app, a body of case records, and a
   dataset, and its analyzers produce no false verdicts on any of them.
4. **Roots:** no tool re-derives roots; outputs never land in the target.
5. **Honesty:** every judgment output is labeled a lead with a confidence, not a verdict.
6. **Cleanliness:** no reference to any prior project (MindSHARD, Forge) survives in `toolkit/`.
