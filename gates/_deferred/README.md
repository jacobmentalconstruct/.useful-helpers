# Deferred gates

Gates for tranches that were **declared and then withdrawn** before implementation.

They are kept, with provenance, because their assertions cost real thought and most
of them survive the withdrawal. They are **not** in active discovery: the runner
globs `t[0-9][0-9]*_*.py` in `gates/`, and files here carry a `.deferred` suffix in a
subdirectory, so they cannot run.

That combination is deliberate. A plan that says *withdrawn* while the runner still
executes the gate is competing project state, which is the condition this project
was reset to remove.

## Contents

### `t05a_observe_select.py.deferred`

Declared 2026-08-09 (journal 0017), withdrawn the same day (journal 0019) when the
operator's deployment-topology correction changed what the runtime product is.

**Withdrawn, not invalidated.** These assertions are expected to be salvaged into
One Surface's gate once its runtime boundary is settled:

- one shell module; the worker pattern extracted into a controller
- the shell spawns no thread of its own and reaches the seam only via the controller
- builds and tears down headlessly through a real entrance
- opening a project populates the explorer and binds the target it was pointed at
- context renders for a file **and** for a folder
- browsing does not change inclusion, **and** inclusion does not move browsing
- rescan picks up a change
- presence reports both state domains accurately to an agent
- shutdown leaves nothing running

**Not salvageable as written** — these encode the superseded architecture:

- the four legacy views as the regression set. `installer_view` is setup-application
  capability, not installed-runtime capability, and it is independently stale: it
  offers "Host AGENTS.md pointer" and "Add to host .gitignore" checkboxes and passes
  `host_agents`/`gitignore` arguments that `sidecar_install` no longer accepts. It
  cannot serve as a regression oracle for the runtime shell.
- any assertion that inherits T5b's "every registered tool reachable from the shell",
  which would force the installed sidecar to expose *install another sidecar* as
  runtime functionality.
