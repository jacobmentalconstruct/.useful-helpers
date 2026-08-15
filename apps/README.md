# apps/ — TRANSITIONAL. Not product architecture.

**This layer does not survive the prototype.** The intended shape is

```text
primitive tools  ->  governed tool chains  ->  common runtime/seam  ->  human + agent
```

not *tools → specialised applications → human + agent*. An application here is
re-homed implementation kept as **reference and as a parity oracle**, not as an
enduring authority.

**Preserve useful behaviour, not application structure.** Where an app's behaviour
already exists across primitives, compose those primitives; do not transplant the
app's backend, and do not create a tool merely because an app had a function with that
name.

An `apps/*` entry still satisfies the full **Tool Contract** (see `tools/README.md`):
a headless `cli.py` + a `tool.json`, so the agent entrance drives it without the GUI.

## Members
- `projectmapper` — Project Snapshot: a shareable, deterministic map/dump of a folder.
  Useful behaviour worth preserving: deterministic traversal, exclusions, tree capture,
  readable-content capture, manifest/schema, checksums, the SQLite snapshot artifact,
  and optional Markdown/tree/filedump exports. Conceptually
  *scope → deterministic scan → content capture → manifest/checksum → snapshot artifact
  → optional exports* — a **capture chain**, not an application.

## The atomicity test — before proposing any decomposition

> Is this one coherent deterministic operation with a useful independent contract, or
> merely an orchestration of independently useful existing primitives?

If it is **genuinely atomic from the caller's perspective** — target in, canonical
artifact out — it may remain **one tool**, and the right action is simply to **re-home
it**. If its internals duplicate canonical primitives, compose those instead.

**Location is not architecture.** `projectmapper` has no private backend and no
app-framework dependency, so its presence here is partly a *classification* defect. Do
not split snapshot compilation into six tools and a playbook to satisfy a preference
for chains. **The goal is removal of duplicated ownership, not maximum decomposition.**

Likewise, size is not the smell. A large deterministic compiler with one narrow
contract is acceptable; a small surface owning a private project model, parser suite,
state store or workflow is not. See `CHARTER.md` §1.4.

## Retirement or re-homing

By demonstrated parity only, never by decree. A member leaves this directory — for the
bench or for the archive — when its behaviour is identified, the enduring tool or chain
owner is named, the bench reproduces what the prototype needs, no live entrance depends
on the *application* shape, gates exercise the replacement path, and no document still
presents it as product architecture.

Scheduled diagnostic: the **Application Absorption Audit**, `.bcc/TRANCHE_PLAN.md`
§C1b. Nothing here is deleted or moved before it runs.
