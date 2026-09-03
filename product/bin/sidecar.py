from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True

INSTANCE_ROOT = Path(__file__).resolve().parents[1]
if str(INSTANCE_ROOT) not in sys.path:
    sys.path.insert(0, str(INSTANCE_ROOT))

from core.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(INSTANCE_ROOT, sys.argv[1:]))
