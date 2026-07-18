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
    """Called when the plugin is loaded."""
    register(
        name="redis",
        type="engine",
        factory=create_cache,
        version="0.1.0",
        description="Redis cache engine for EVOID",
    )
