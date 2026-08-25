"""Development-time assembly for the installed sidecar product."""

from .installer import AttachError, attach

__all__ = ["AttachError", "attach"]
