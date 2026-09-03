from __future__ import annotations

import sys

sys.dont_write_bytecode = True

from .cli import main  # noqa: E402

raise SystemExit(main())
