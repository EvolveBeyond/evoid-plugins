"""Tests for Advanced DI engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from evoid import Level
from evoid_advanced_di.engine import AdvancedDIEngine


def _mock_ctx(level=Level.STANDARD, user_role=None, user_id=None, metadata=None):
    """Create a mock EVOID Context."""
    ctx = MagicMock()
    ctx.intent = MagicMock()
    ctx.intent.level = level
    ctx.intent.name = "test_intent"
    ctx.intent.metadata = metadata or {}
    ctx.state = {}
    if user_id:
        ctx.state["user_id"] = user_id
    if user_role:
        ctx.state["user_role"] = user_role
    ctx.deps = {}
    return ctx


class TestAdvancedDIEngine:
    @pytest.fixture
    def engine(self):
        """Engine with mock implementations."""
        rules_config = {
            "notifier": {
                "priority_1": {"when": {"level": Level.CRITICAL}, "then": "email"},
                "priority_2": {"when": {"user_role": "vip"}, "then": "vip"},
                "default": "memory",
            },
            "auth": {
                "oauth": {
                    "when": {"metadata_key": "auth_method", "metadata_value": "oauth2"},
                    "then": "oauth2",
                },
                "default": "simple",
            },
        }

        implementations = {
            "email": lambda: {"type": "email"},
            "vip": lambda: {"type": "vip"},
            "memory": lambda: {"type": "memory"},
            "oauth2": lambda: {"type": "oauth2"},
            "simple": lambda: {"type": "simple"},
        }

        return AdvancedDIEngine(rules_config, implementations)

    @pytest.mark.asyncio
    async def test_resolve_by_level(self, engine):
        ctx = _mock_ctx(level=Level.CRITICAL)
        result = await engine.resolve("notifier", ctx)
        assert result == {"type": "email"}

    @pytest.mark.asyncio
    async def test_resolve_by_user_role(self, engine):
        ctx = _mock_ctx(user_role="vip")
        result = await engine.resolve("notifier", ctx)
        assert result == {"type": "vip"}

    @pytest.mark.asyncio
    async def test_resolve_default(self, engine):
        ctx = _mock_ctx()
        result = await engine.resolve("notifier", ctx)
        assert result == {"type": "memory"}

    @pytest.mark.asyncio
    async def test_resolve_by_metadata(self, engine):
        ctx = _mock_ctx(metadata={"auth_method": "oauth2"})
        result = await engine.resolve("auth", ctx)
        assert result == {"type": "oauth2"}

    @pytest.mark.asyncio
    async def test_resolve_auth_default(self, engine):
        ctx = _mock_ctx()
        result = await engine.resolve("auth", ctx)
        assert result == {"type": "simple"}

    @pytest.mark.asyncio
    async def test_inject_adds_to_deps(self, engine):
        ctx = _mock_ctx()
        await engine.inject(ctx, "notifier")
        assert "notifier" in ctx.deps
        assert ctx.deps["notifier"] == {"type": "memory"}

    @pytest.mark.asyncio
    async def test_inject_with_custom_key(self, engine):
        ctx = _mock_ctx()
        await engine.inject(ctx, "notifier", key="my_notifier")
        assert "my_notifier" in ctx.deps

    @pytest.mark.asyncio
    async def test_unknown_service_raises(self, engine):
        ctx = _mock_ctx()
        with pytest.raises(ValueError, match="No rules defined"):
            await engine.resolve("nonexistent", ctx)

    @pytest.mark.asyncio
    async def test_singleton_caches(self, engine):
        ctx = _mock_ctx()
        r1 = await engine.resolve("notifier", ctx)
        r2 = await engine.resolve("notifier", ctx)
        assert r1 is r2  # Same instance

    @pytest.mark.asyncio
    async def test_clear_cache(self, engine):
        ctx = _mock_ctx()
        r1 = await engine.resolve("notifier", ctx)
        engine.clear_cache()
        r2 = await engine.resolve("notifier", ctx)
        assert r1 is not r2  # New instance after cache clear

    def test_list_services(self, engine):
        services = engine.list_services()
        assert "notifier" in services
        assert "auth" in services
