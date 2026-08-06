# Cartridges — domain knowledge for `attach`

A **cartridge** is what the instrument knows about one *kind* of target. `attach` probes the
target, scores it against every cartridge here, and mounts the winner's tools as the workbench.

One JSON file per domain. Adding a domain means adding a file — no code changes.

## Schema

| Field | Meaning |
|---|---|
| `domain` | id; must match the filename stem |
| `summary` | one line, shown in the PROJECT_MAP |
| `detect.markers` | `{filename: weight}` — a marker file scores its weight once if present |
| `detect.extensions` | `{ext: weight}` — scored `weight × log-damped file count` |
| `entry_hints` | filenames that, if present, are reported as entry points |
| `mounted` | tool ids on the workbench for this domain — **the selection layer** |
| `policy` | `{tool_id: {confidence, note}}` — what this tool's output is worth *here* |

## The two rules

**1. Mount by relevance, not availability.** The agent should face the tools this target
needs, not all 77. A tool that cannot say anything true about this domain must not be mounted
— `import_graph` on a JS project would return an empty graph and read as a finding.

**2. Policy carries confidence, and confidence is honest.** Per `_design/CHARTER.md §4`,
opinionated tools emit *leads*, not verdicts. The `policy` block is where a cartridge states
what a tool's output is actually worth against this kind of target. `confidence: "none"` means
do not mount. If a note has to explain why a tool lies, that is the signal to leave it off.

Scoring is deliberately transparent — `attach` returns every cartridge's score, so a
misclassification is visible rather than silent, and `attach {"domain": "..."}` overrides it.
