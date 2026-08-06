"""
Owns: simple JSON load and save helpers with explicit defaults.
Does not own: schema normalization, domain validation, or logging policy.
Collaborates with: config and state managers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
