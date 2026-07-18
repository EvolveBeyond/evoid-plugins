"""Smart Storage Engine for EVOID.

Routes data to different backends based on:
- Data type (credentials, session, permissions)
- Intent level (CRITICAL → PostgreSQL, STANDARD → SQLite)
- Intent metadata (storage_preference override)
- User ID (multi-tenancy)

IOP: Plugin registry pattern — register, resolve, use.
"""

from __future__ import annotations

from .engine import SmartStorage
from .schema_enforcer import SchemaEnforcer

# Plugin manifest
MANIFEST = {
    "name": "evoid-smart-storage",
    "version": "0.1.0",
    "type": "engine",
    "description": "Smart storage with data-type routing, multi-tenancy, schema enforcement",
    "entry_point": "evoid_smart_storage:register_plugin",
    "dependencies": ["evoid>=0.4.0"],
    "evoid_version": ">=0.4.0",
    "tags": ["storage", "multi-db", "smart-routing"],
}


def register_plugin():
    """Called when the plugin is loaded."""
    from evoid.engines.plugin import register

    register(
        name="smart_storage",
        type="engine",
        factory=SmartStorage,
        version="0.1.0",
        description="Smart storage engine with data-type routing",
    )
