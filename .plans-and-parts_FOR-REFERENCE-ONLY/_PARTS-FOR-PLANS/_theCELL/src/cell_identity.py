"""
Cell Identity for _theCELL (simplified for task-list runner)
"""

import uuid
from datetime import datetime


class CellIdentity:
    """Minimal identity for a single cell: unique ID and display name only."""

    def __init__(self, cell_id: str = None, cell_name: str = None):
        self.cell_id: str = cell_id if cell_id else self._generate_unique_id()
        self.cell_name: str = cell_name if cell_name else self._generate_default_name()
        self.created_at: str = datetime.now().isoformat()

    def _generate_unique_id(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        uuid_segment = uuid.uuid4().hex[:8]
        return f"cell_{timestamp}_{uuid_segment}"

    def _generate_default_name(self) -> str:
        short_id = self.cell_id.split('_')[-1]
        return f"Cell-{short_id.upper()}"

    def rename(self, new_name: str) -> None:
        self.cell_name = new_name.strip()

    def __repr__(self) -> str:
        return f"CellIdentity({self.cell_name!r}, id={self.cell_id})"
