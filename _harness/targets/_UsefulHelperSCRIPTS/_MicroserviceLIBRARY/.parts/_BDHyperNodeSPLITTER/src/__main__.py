"""Entry point for `python -m src`.

Adds the local ``src/`` directory to ``sys.path`` so the Splitter's internal
``core.*`` imports resolve when the package is launched from its project root.
"""
import sys
from pathlib import Path

_this_dir = Path(__file__).parent

if str(_this_dir) not in sys.path:
    sys.path.insert(0, str(_this_dir))

from app import main  # noqa: E402

sys.exit(main())
