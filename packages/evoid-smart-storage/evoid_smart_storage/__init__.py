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
    Registers with DI as 'storage' for unified access.
    """
    from evoid_di import di
    from evoid.core.extend import add_intent
    from evoid.core.intents import STORAGE_READ, STORAGE_WRITE, STORAGE_DELETE, STORAGE_HEALTH

    _config = config or {}
    di.register("storage", lambda: SmartStorage(_config), scope="singleton")

    async def handle_read(ctx):
        storage = di.resolve("storage")
        key = ctx.intent.metadata.get("key")
        return await storage.read(key)

    async def handle_write(ctx):
        storage = di.resolve("storage")
        key = ctx.intent.metadata.get("key")
        value = ctx.intent.metadata.get("value")
        return await storage.write(key, value)

    async def handle_delete(ctx):
        storage = di.resolve("storage")
        key = ctx.intent.metadata.get("key")
        return await storage.delete(key)

    async def handle_health(ctx):
        storage = di.resolve("storage")
        return await storage.health()

    add_intent(STORAGE_READ, handle_read)
    add_intent(STORAGE_WRITE, handle_write)
    add_intent(STORAGE_DELETE, handle_delete)
    add_intent(STORAGE_HEALTH, handle_health)
