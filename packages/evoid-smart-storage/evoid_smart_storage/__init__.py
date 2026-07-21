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
    """Called when the plugin is loaded (legacy path)."""
    from evoid.engines.plugin import register

    register(
        name="smart_storage",
        type="engine",
        factory=SmartStorage,
        version="0.1.0",
        description="Smart storage engine with data-type routing",
    )


def register_handlers(config: dict | None = None) -> None:
    """Register Smart Storage as Intent handlers.

    IOP: Smart Storage routes storage Intents to different backends
    based on data type, intent level, and metadata.
    """
    from evoid.core import register as register_intent, register_processor
    from evoid.core.intents import STORAGE_READ, STORAGE_WRITE, STORAGE_DELETE, STORAGE_HEALTH

    _config = config or {}
    _storage = SmartStorage(_config)

    async def handle_read(ctx):
        key = ctx.intent.metadata.get("key")
        return await _storage.read(key)

    async def handle_write(ctx):
        key = ctx.intent.metadata.get("key")
        value = ctx.intent.metadata.get("value")
        return await _storage.write(key, value)

    async def handle_delete(ctx):
        key = ctx.intent.metadata.get("key")
        return await _storage.delete(key)

    async def handle_health(ctx):
        return await _storage.health()

    register_intent(STORAGE_READ)
    register_intent(STORAGE_WRITE)
    register_intent(STORAGE_DELETE)
    register_intent(STORAGE_HEALTH)
    register_processor("storage.read", handle_read)
    register_processor("storage.write", handle_write)
    register_processor("storage.delete", handle_delete)
    register_processor("storage.health", handle_health)
