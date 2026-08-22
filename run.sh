#!/bin/sh
# FILE:   run.sh
# ROLE:   POSIX launcher for an installed instance.
# DOES:   Runs Useful Helpers from ANYWHERE, including the target root.
# NOTES:  `run.bat` shipped and this did not, so on Linux and macOS there was no
#         launcher at all - the operator had to know to `cd` into the sidecar and use
#         `python -m src.app`. For a product whose whole premise is operating on the
#         folder it lives in, requiring a `cd` INTO the sidecar first is backwards.
#
#         Resolves its own directory, so `sh .useful-helpers/run.sh list` works from
#         the target root and `./run.sh list` works from inside. It does not care
#         where you stand.
set -eu

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$HERE"

PYTHON_EXE=python3
[ -x ".venv/bin/python" ] && PYTHON_EXE=".venv/bin/python"
command -v "$PYTHON_EXE" >/dev/null 2>&1 || PYTHON_EXE=python

case "${1:-help}" in
  list)   exec "$PYTHON_EXE" -m src.app cli tool-list ;;
  attach) exec "$PYTHON_EXE" -m src.app cli tool-call --tool attach --args-json '{}' ;;
  call)   shift; exec "$PYTHON_EXE" -m src.app cli tool-call "$@" ;;
  # PARITY IS ADDED HERE, NOT IN run.bat. The two launchers named the same act differently
  # - `run.sh call --tool X --args-json J` against `run.bat tool X J` - and the obvious fix
  # was to teach run.bat the word `call`. It is the wrong direction: cmd.exe cannot forward
  # an argument vector, so a `call` alias there has to re-expand JSON through the command
  # line, and `&`, `<`, `>`, `|` and `^` in a payload stop being data. That trades a naming
  # difference for silent corruption. A shell that CAN forward argv exactly is the safe
  # place to add the other platform's verb, so `tool` is the portable spelling and works
  # identically on both.
  tool)
          [ -n "${2:-}" ] || { echo "usage: run.sh tool <tool_id> <args-json>" >&2; exit 2; }
          _args=${3:-}
          [ -n "$_args" ] || _args='{}'
          exec "$PYTHON_EXE" -m src.app cli tool-call --tool "$2" --args-json "$_args" ;;
  mcp)    exec "$PYTHON_EXE" -m src.app mcp ;;
  ui)     exec "$PYTHON_EXE" -m src.app ui ;;
  smoke)  exec "$PYTHON_EXE" smoke_test.py ;;
  cli)    shift; exec "$PYTHON_EXE" -m src.app cli "$@" ;;
  help|-h|--help)
    cat <<'USAGE'
Useful Helpers - a governed sidecar for the folder it lives in.

  run.sh attach            what is this target, and what should I do next
  run.sh list              every tool available here
  run.sh call --tool X --args-json '{}'
  run.sh tool X '{}'       the same thing, spelled the way run.bat spells it
  run.sh tool X @args.json a payload too large for a command line (Windows caps
                           one at 32,767 characters; this route has no limit)
  run.sh mcp               serve an agent over MCP (stdio)
  run.sh ui                the graphical surface
  run.sh smoke             verify this installation

Invoke it BY PATH - it is not on PATH, but it resolves its own directory, so the
working directory you start from does not matter:

  sh .useful-helpers/run.sh attach      from the target root
  sh run.sh attach                      from inside the instance

Installing a sidecar is the setup application's job. This instance is bound to the
folder it lives in and does not install others.
USAGE
    ;;
  *) exec "$PYTHON_EXE" -m src.app "$@" ;;
esac
