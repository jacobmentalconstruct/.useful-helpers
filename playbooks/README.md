# playbooks/

A **playbook is data** — an ordered list of steps run through the control plane's single
`invoke()` seam. Compose the registered tools into repeatable workflows.

**Run it:**
- CLI: `run.bat cli run-playbook --file playbooks/<name>.json`
  (or `--playbook-json '<json>'`; add `--continue-on-error true` to not stop on failure).
- MCP: method `playbook/run` with params `{ "steps": [...], "stopOnError": true }`.

**Step shape:** `{ "id"?: str, "tool": str, "args": {...} }`. `id` defaults to the step index.

**Piping:** a later step references an earlier step's structured output with a **whole-string**
arg value `"@<id>.<dotted.path>"` (e.g. `"@report.markdown"`, `"@snap.outputs.snapshot_db"`).
`"@@"` escapes a literal leading `@`. The runner stops on the first failed step unless
continue-on-error.

**Report:** `{ ok, count, completed, failed_at, steps: [{id, tool, ok, output, error}] }`.

Examples: `survey.json` (host + python file tree + structural report), `ground_report.json`
(report → attach it as verifiable evidence → verify).
