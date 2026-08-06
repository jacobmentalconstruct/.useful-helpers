# The Harness  -  a proving ground for the sidecar

**Factory, not product.** This never ships. It exists to point the sidecar at a real target and
record, mechanically, what happened. See `_design/CHARTER.md sec 7`.

## Why it exists

The `INTEGRATION_FIELD_REPORT` was one agent's manual observations from one engagement. It was
the most valuable artifact in the whole project  -  and it was a one-off, written by hand, after
the fact. **The harness makes that loop repeatable and automatic.**

It answers, per run, against `CHARTER.md sec 8`:

| Question | How it is answered |
|---|---|
| Did the sidecar leave a trace in the target? | sha256 manifest before/after; **any** delta outside the sidecar folder is a violation |
| Does the front door orient an agent in one call? | `attach` runs; its map/workbench/next are scored |
| Do the tools work on a target nobody tuned them for? | every mounted Observe tool is run with default args; ok/error/duration recorded |
| Do the tools lie? | planted ground truth (below) |
| Is the sidecar clean? | greps its own tree for prior-project lineage |

## Planted ground truth (the point)

Scaffolded targets deliberately contain **known false-positive bait**, drawn from the field
report's Part C  -  the places the old tools reported valid design as defects:

- a **decorator-registered command** with no static caller (`dead_code` will flag it; it is live)
- a **subprocess call in a sync function** (`blocking_call_scan` will flag it; it is correct)
- an **interface method** implemented but never directly called (live via the ABC)

Each scaffold ships a `_ground_truth.json` naming these. The harness scores the sidecar against
them: flagging planted bait is a **false positive**, and a tool that does so without a
`confidence` label is a **charter sec 4 violation**, not a bug in the target.

This is the difference between "the tools ran" and "the tools told the truth."

## Use

```bash
python _harness/harness.py scaffold demo --kind python-app   # build a dummy target
python _harness/harness.py adopt C:/path/to/real/project     # or drop a real one in
python _harness/harness.py list                              # targets + runs
python _harness/harness.py run demo                          # install sidecar, exercise, score
python _harness/harness.py report <run-id>                   # render the recorded run
```

`run` is non-destructive to the sidecar under test: it copies `toolkit/` into
`<target>/.useful-helpers/` fresh each time. Targets live in `_harness/targets/`, runs in
`_harness/runs/<run-id>/` (`run.json` = everything observed, `report.md` = readable).

Only **Observe**-authority tools are exercised. The harness never runs Apply tools against a
target  -  the point is to observe the instrument, not to let it modify the evidence.

### Install modes

- `--install copy` (default)  -  plain copy. Isolates tool behavior from installer behavior.
- `--install tool`  -  exercises `tools/sidecar_install` itself. **Expect precept violations**:
  it ships `write_agents: true` and `gitignore: true`, so it writes `AGENTS.md` into the target
  root and edits the target's `.gitignore`. The harness is what proves that, and what will prove
  it fixed. See `_design/SCRUB_AUDIT.md sec 3`.

## M1 - proving the precept by PREVENTION (`mount`)

Every other dimension measures the precept by **detection**: snapshot the target, run the tool,
diff. That catches a violation after it lands. `mount` closes the other half - it mounts the
target **read-only**, so the OS refuses the write and a violation cannot happen at all.

```bash
python3 _harness/harness.py mount s-python-app     # Linux only
```

It scores two things, and both must pass:

1. **Prevention** - a planted Observe tool that writes to the target fails, and the file never
   appears. (Detection mode expects the opposite: the write lands and the seam reports it.)
2. **Still usable** - `attach`, `glob`, `repo_search`, and `report` all still succeed against a
   target they physically cannot write. Prevention that breaks the instrument proves nothing.

Together those two are the roots contract stated mechanically: the sidecar reads the target,
writes only its own home, and the **OS** - not the author's discipline - is what enforces it.

### Strategies (both measured, not assumed)

| host | strategy | how |
|---|---|---|
| Linux, root (CI) | `bind` | `mount --bind` + `remount,ro,bind` - the REAL target, no copy |
| Linux, unprivileged | `userns-tmpfs` | `unshare -rm`, tmpfs inside the namespace, copy in, seal |
| Windows / macOS | none | reports **UNAVAILABLE with a reason** |

The `userns-tmpfs` detour is not arbitrary: mounts **inherited** by a user namespace are locked,
so a plain bind cannot be remounted read-only inside one. Unprivileged overlayfs fails there too.
A tmpfs created *inside* the namespace is the one thing you own well enough to seal. All three
behaviours were measured on this machine before the strategy was chosen.

Before trusting any result, the probe **self-tests the rig**: it writes a file, seals the mount,
and demands the write fail with `EROFS`. A probe that assumes its own instrument works is how you
ship a green light over a broken rig.

### The honest-skip contract

On a host without a strategy, `mount` prints `UNAVAILABLE` **and a reason**, and exits 0. A
skipped dimension must never read as a pass - that is the exact class of lie this project exists
to eliminate. It is also why there is no committed CI workflow yet: this tree is not a git repo,
so a workflow file could not be run or verified here, and shipping unverified config would be the
same failure in a different costume. When it becomes a repo, one job does it:

```yaml
# .github/workflows/precept.yml
jobs:
  precept:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - run: python _harness/harness.py scaffold ci-target --kind python-app --force
      - run: python _harness/harness.py mount ci-target      # fails the build on a violation
```

### Deployment note (found by building this)

A read-only target forces the sidecar **out of** the target directory. The normal
`<target>/.useful-helpers/` layout cannot work against a sealed target, because the sidecar must
write its own state. So `mount` models the **audit posture** - external sidecar,
`SUITE_PROJECT_ROOT` pointed at a read-only target - which is exactly what a CI check or a
forensic review wants. It does not model in-target deployment, and saying so is the point.
