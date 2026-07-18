"""Tests for evoid-redis plugin."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from evoid_redis import RedisCache, create_cache


class TestRedisCache:
    @pytest.fixture
    def cache(self):
        c = RedisCache(url="redis://localhost:6379", prefix="test:")
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=None)
        mock_client.set = AsyncMock(return_value=True)
        mock_client.setex = AsyncMock(return_value=True)
        mock_client.delete = AsyncMock(return_value=1)
        mock_client.exists = AsyncMock(return_value=0)
        mock_client.ping = AsyncMock(return_value=True)
        c._client = mock_client
        return c

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        import json
        cache._client.get = AsyncMock(return_value=json.dumps({"name": "Alice"}))

        await cache.set("user:1", {"name": "Alice"})
        cache._client.set.assert_called_once()

        result = await cache.get("user:1")
        assert result == {"name": "Alice"}

    @pytest.mark.asyncio
    async def test_get_missing(self, cache):
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, cache):
        result = await cache.delete("key1")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists(self, cache):
        cache._client.exists = AsyncMock(return_value=1)
        assert await cache.exists("key1") is True

        cache._client.exists = AsyncMock(return_value=0)
        assert await cache.exists("key1") is False

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, cache):
        await cache.set("session:abc", {"user": "bob"}, ttl=300)
        cache._client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_health(self, cache):
        assert await cache.health() is True

    @pytest.mark.asyncio
    async def test_prefix(self, cache):
        await cache.set("mykey", "myval")
        call_args = cache._client.set.call_args[0]
        assert call_args[0] == "test:mykey"
