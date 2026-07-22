"""Redis Cache Engine for EVOID.

IOP: Plugin registry pattern — register, resolve, use.
"""

from __future__ import annotations

import json
from typing import Any

from evoid.engines.plugin import register

MANIFEST = {
    "name": "evoid-redis",
    "version": "0.1.0",
    "type": "engine",
    "description": "Redis cache engine for EVOID",
    "entry_point": "evoid_redis:register_plugin",
    "dependencies": ["redis[hiredis]>=5.0.0"],
    "evoid_version": ">=0.4.0",
    "tags": ["cache", "redis"],
}


class RedisCache:
    """Redis-backed cache engine."""

    def __init__(self, url: str = "redis://localhost:6379", prefix: str = "evoid:"):
        self.url = url
        self.prefix = prefix
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(self.url, decode_responses=True)
        return self._client

    def _key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Any | None:
        client = await self._get_client()
        raw = await client.get(self._key(key))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        client = await self._get_client()
        data = json.dumps(value) if not isinstance(value, str) else value
        if ttl:
            await client.setex(self._key(key), ttl, data)
        else:
            await client.set(self._key(key), data)
        return True

    async def delete(self, key: str) -> bool:
        client = await self._get_client()
        result = await client.delete(self._key(key))
        return result > 0

    async def exists(self, key: str) -> bool:
        client = await self._get_client()
        return await client.exists(self._key(key)) > 0

    async def health(self) -> bool:
        try:
            client = await self._get_client()
            return await client.ping()
        except Exception:
            return False

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


def create_cache(url: str = "redis://localhost:6379", prefix: str = "evoid:") -> RedisCache:
    """Factory: create a Redis cache instance."""
    return RedisCache(url=url, prefix=prefix)


def register_plugin():
    """Called when the plugin is loaded (legacy path)."""
    register(
        name="redis",
        type="engine",
        factory=create_cache,
        version="0.1.0",
        description="Redis cache engine for EVOID",
    )


def register_handlers(url: str = "redis://localhost:6379", prefix: str = "evoid:") -> None:
    """Register Redis cache as Intent handlers.

    IOP: Each cache operation is an Intent.
    Registers with DI as 'cache.redis' for smart-storage routing.
    """
    from evoid_di import di
    from evoid.core import register as register_intent, register_processor
    from evoid.core.intents import CACHE_GET, CACHE_SET, CACHE_DELETE, CACHE_EXISTS, CACHE_HEALTH

    di.register("cache.redis", lambda: RedisCache(url=url, prefix=prefix), scope="singleton")

    async def handle_get(ctx):
        cache = di.resolve("cache.redis")
        key = ctx.intent.metadata.get("key")
        return await cache.get(key)

    async def handle_set(ctx):
        cache = di.resolve("cache.redis")
        key = ctx.intent.metadata.get("key")
        value = ctx.intent.metadata.get("value")
        ttl = ctx.intent.metadata.get("ttl")
        return await cache.set(key, value, ttl)

    async def handle_delete(ctx):
        cache = di.resolve("cache.redis")
        key = ctx.intent.metadata.get("key")
        return await cache.delete(key)

    async def handle_exists(ctx):
        cache = di.resolve("cache.redis")
        key = ctx.intent.metadata.get("key")
        return await cache.exists(key)

    async def handle_health(ctx):
        cache = di.resolve("cache.redis")
        return await cache.health()

    register_intent(CACHE_GET)
    register_intent(CACHE_SET)
    register_intent(CACHE_DELETE)
    register_intent(CACHE_EXISTS)
    register_intent(CACHE_HEALTH)
    register_processor("cache.get", handle_get)
    register_processor("cache.set", handle_set)
    register_processor("cache.delete", handle_delete)
    register_processor("cache.exists", handle_exists)
    register_processor("cache.health", handle_health)
