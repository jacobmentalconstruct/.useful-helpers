"""Development-time assembly for the installed sidecar product."""

import sys

sys.dont_write_bytecode = True

from .installer import AttachError, attach  # noqa: E402

__all__ = ["AttachError", "attach"]
