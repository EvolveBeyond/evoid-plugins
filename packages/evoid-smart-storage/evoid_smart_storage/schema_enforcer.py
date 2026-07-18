"""Schema enforcement — restrict which fields are stored per data type."""

from __future__ import annotations

from typing import Any


class SchemaEnforcer:
    """Enforce column restrictions per data type.

    If a schema is defined for a data type, only allowed fields are stored.
    If no schema is defined, all fields pass through.

    Config example:
        [engines.smart_storage.schemas]
        credentials = ["email", "password_hash"]
        session = ["username", "uuid", "cookie"]
    """

    def __init__(self, schemas: dict[str, list[str]]):
        self.schemas = schemas

    def apply(self, data_type: str, data: dict[str, Any]) -> dict[str, Any]:
        """Filter data to only include allowed fields.

        Args:
            data_type: The type of data being stored
            data: The data dict to filter

        Returns:
            Filtered dict with only allowed fields
        """
        allowed = self.schemas.get(data_type)
        if not allowed:
            return data  # No restriction defined — pass through
        return {k: v for k, v in data.items() if k in allowed}

    def get_allowed_fields(self, data_type: str) -> list[str] | None:
        """Get the allowed fields for a data type, or None if unrestricted."""
        return self.schemas.get(data_type)

    def is_valid(self, data_type: str, data: dict[str, Any]) -> bool:
        """Check if all fields in data are allowed for this data type."""
        allowed = self.schemas.get(data_type)
        if not allowed:
            return True
        return all(k in allowed for k in data.keys())
