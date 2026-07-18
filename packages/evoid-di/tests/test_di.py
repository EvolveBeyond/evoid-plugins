"""Tests for evoid-di — all 3 levels."""

import pytest
from unittest.mock import MagicMock
from evoid import Level
from evoid_di import DIEngine


# ============================================================
# Level 1: Simple register/resolve
# ============================================================


class TestLevel1Simple:
    def test_register_and_resolve(self):
        engine = DIEngine()
        engine.register("db", lambda: {"type": "sqlite"})
        result = engine.resolve("db")
        assert result == {"type": "sqlite"}

    def test_singleton_default(self):
        engine = DIEngine()
        engine.register("db", lambda: {"id": 1})
        r1 = engine.resolve("db")
        r2 = engine.resolve("db")
        assert r1 is r2

    def test_transient_new_each_time(self):
        engine = DIEngine()
        engine.register("counter", lambda: {"id": id(object())}, scope="transient")
        r1 = engine.resolve("counter")
        r2 = engine.resolve("counter")
        assert r1 is not r2

    def test_per_user_scoped(self):
        engine = DIEngine()
        engine.register("session", lambda: {"token": "abc"}, scope="per_user")
        r1 = engine.resolve("session", user_id="alice")
        r2 = engine.resolve("session", user_id="bob")
        r3 = engine.resolve("session", user_id="alice")
        assert r1 is not r2
        assert r1 is r3

    def test_per_user_requires_user_id(self):
        engine = DIEngine()
        engine.register("session", lambda: {}, scope="per_user")
        with pytest.raises(ValueError, match="requires user_id"):
            engine.resolve("session")

    def test_unregistered_raises(self):
        engine = DIEngine()
        with pytest.raises(ValueError, match="No dependency"):
            engine.resolve("nonexistent")

    def test_direct_instance(self):
        engine = DIEngine()
        engine.register("config", {"debug": True})
        result = engine.resolve("config")
        assert result == {"debug": True}

    def test_clear(self):
        engine = DIEngine()
        engine.register("db", lambda: {"id": 1})
        r1 = engine.resolve("db")
        engine.clear()
        r2 = engine.resolve("db")
        assert r1 is not r2

    def test_list_services(self):
        engine = DIEngine()
        engine.register("db", lambda: None)
        engine.register("cache", lambda: None)
        services = engine.list_services()
        assert "db" in services
        assert "cache" in services


# ============================================================
# Level 3: Context-aware routing
# ============================================================


def _mock_ctx(level=Level.STANDARD, user_role=None, user_id=None, metadata=None):
    ctx = MagicMock()
    ctx.intent = MagicMock()
    ctx.intent.level = level
    ctx.intent.name = "test"
    ctx.intent.metadata = metadata or {}
    ctx.state = {}
    if user_id:
        ctx.state["user_id"] = user_id
    if user_role:
        ctx.state["user_role"] = user_role
    ctx.deps = {}
    return ctx


class TestLevel3Advanced:
    @pytest.fixture
    def engine(self):
        rules = {
            "notifier": {
                "p1": {"when": {"level": Level.CRITICAL}, "then": "email"},
                "p2": {"when": {"user_role": "vip"}, "then": "vip"},
                "default": "memory",
            },
        }
        impls = {
            "email": lambda: {"type": "email"},
            "vip": lambda: {"type": "vip"},
            "memory": lambda: {"type": "memory"},
        }
        return DIEngine(rules_config=rules, implementations=impls)

    @pytest.mark.asyncio
    async def test_resolve_by_level(self, engine):
        ctx = _mock_ctx(level=Level.CRITICAL)
        result = await engine.resolve_async("notifier", ctx)
        assert result == {"type": "email"}

    @pytest.mark.asyncio
    async def test_resolve_by_role(self, engine):
        ctx = _mock_ctx(user_role="vip")
        result = await engine.resolve_async("notifier", ctx)
        assert result == {"type": "vip"}

    @pytest.mark.asyncio
    async def test_resolve_default(self, engine):
        ctx = _mock_ctx()
        result = await engine.resolve_async("notifier", ctx)
        assert result == {"type": "memory"}

    @pytest.mark.asyncio
    async def test_inject_to_ctx(self, engine):
        ctx = _mock_ctx()
        await engine.inject(ctx, "notifier")
        assert "notifier" in ctx.deps

    def test_simple_fallback(self, engine):
        # Level 1 still works alongside Level 3
        engine.register("db", lambda: {"type": "sqlite"})
        result = engine.resolve("db")
        assert result == {"type": "sqlite"}
