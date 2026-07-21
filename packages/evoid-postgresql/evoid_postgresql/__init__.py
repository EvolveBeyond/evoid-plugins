"""PostgreSQL Storage Engine for EVOID via SQLAlchemy.

IOP: Plugin registry pattern — register, resolve, use.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text

from evoid.engines.plugin import register

MANIFEST = {
    "name": "evoid-postgresql",
    "version": "0.1.0",
    "type": "engine",
    "description": "PostgreSQL storage engine via SQLAlchemy for EVOID",
    "entry_point": "evoid_postgresql:register_plugin",
    "dependencies": ["sqlalchemy[asyncio]>=2.0.0", "asyncpg>=0.29.0"],
    "evoid_version": ">=0.4.0",
    "tags": ["storage", "postgresql", "database", "sqlalchemy"],
}


class PostgresStorage:
    """PostgreSQL-backed storage engine via SQLAlchemy async."""

    def __init__(self, url: str = "postgresql+asyncpg://localhost/evoid"):
        self.url = url
        self._engine = None
        self._session_factory = None

    async def _setup(self):
        if self._engine is not None:
            return

        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

        self._engine = create_async_engine(self.url, echo=False)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

        async with self._engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS kv_store (
                    key TEXT NOT NULL,
                    namespace TEXT NOT NULL DEFAULT 'default',
                    value JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (key, namespace)
                )
            """))

    async def write(self, key: str, data: dict[str, Any], **kwargs) -> bool:
        namespace = kwargs.get("namespace", "default")
        await self._setup()

        async with self._engine.begin() as conn:
            await conn.execute(
                text("""
                    INSERT INTO kv_store (key, namespace, value)
                    VALUES (:key, :ns, :val)
                    ON CONFLICT (key, namespace) DO UPDATE SET value = :val
                """),
                {"key": key, "ns": namespace, "val": json.dumps(data)},
            )
        return True

    async def read(self, key: str, **kwargs) -> Any | None:
        namespace = kwargs.get("namespace", "default")
        await self._setup()

        async with self._engine.begin() as conn:
            result = await conn.execute(
                text("SELECT value FROM kv_store WHERE key = :key AND namespace = :ns"),
                {"key": key, "ns": namespace},
            )
            row = result.fetchone()
            if row:
                return json.loads(row[0]) if isinstance(row[0], str) else row[0]
        return None

    async def delete(self, key: str, **kwargs) -> bool:
        namespace = kwargs.get("namespace", "default")
        await self._setup()

        async with self._engine.begin() as conn:
            result = await conn.execute(
                text("DELETE FROM kv_store WHERE key = :key AND namespace = :ns"),
                {"key": key, "ns": namespace},
            )
            return result.rowcount > 0

    async def health(self) -> bool:
        try:
            await self._setup()
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def close(self):
        if self._engine:
            await self._engine.dispose()
            self._engine = None


def create_storage(url: str = "postgresql+asyncpg://localhost/evoid") -> PostgresStorage:
    """Factory: create a PostgreSQL storage instance."""
    return PostgresStorage(url=url)


def register_plugin():
    """Called when the plugin is loaded (legacy path)."""
    register(
        name="postgresql",
        type="engine",
        factory=create_storage,
        version="0.1.0",
        description="PostgreSQL storage engine via SQLAlchemy",
    )


def register_handlers(url: str = "postgresql+asyncpg://localhost/evoid") -> None:
    """Register PostgreSQL storage as Intent handlers."""
    from evoid.core import register as register_intent, register_processor
    from evoid.core.intents import STORAGE_READ, STORAGE_WRITE, STORAGE_DELETE, STORAGE_HEALTH

    _storage = PostgresStorage(url=url)

    async def handle_read(ctx):
        return await _storage.read(ctx.intent.metadata.get("key"))

    async def handle_write(ctx):
        return await _storage.write(
            ctx.intent.metadata.get("key"),
            ctx.intent.metadata.get("value"),
        )

    async def handle_delete(ctx):
        return await _storage.delete(ctx.intent.metadata.get("key"))

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
