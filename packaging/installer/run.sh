#!/usr/bin/env bash
# FILE:  run.sh
# ROLE:  Unix/macOS launcher for the Useful Helpers sidecar installer.
# DOES:  Finds Python 3, then runs install.py (folder-picker GUI + HITL confirm),
#        which installs the sidecar into the project folder you choose.
# USAGE: ./run.sh   (headless: ./run.sh --target /path/to/proj --mode update)
set -eu
cd "$(dirname "$0")"

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
    echo "Python 3 is required but was not found on PATH." >&2
    echo "Install it from your package manager or https://www.python.org/downloads/." >&2
    exit 1
fi

# Tkinter is needed for the folder-picker GUI; a headless --target run does not need it.
if [ "$#" -eq 0 ] && ! "$PY" -c "import tkinter" >/dev/null 2>&1; then
    echo "Note: Tkinter is not available, so the folder-picker GUI cannot open." >&2
    echo "Install it (e.g. 'sudo apt install python3-tk'), or run headless:" >&2
    echo "  ./run.sh --target /path/to/project --mode install" >&2
    exit 1
fi

exec "$PY" install.py "$@"
