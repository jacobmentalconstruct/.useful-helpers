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
  run.sh mcp               serve an agent over MCP (stdio)
  run.sh ui                the graphical surface
  run.sh smoke             verify this installation

Run it from anywhere:  sh .useful-helpers/run.sh attach
USAGE
    ;;
  *) exec "$PYTHON_EXE" -m src.app "$@" ;;
esac
