"""Tests for evoid-smart-storage plugin."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from evoid_smart_storage.engine import SmartStorage
from evoid_smart_storage.schema_enforcer import SchemaEnforcer


# --- SchemaEnforcer Tests ---


class TestSchemaEnforcer:
    def test_no_schema_passes_all(self):
        enforcer = SchemaEnforcer({})
        data = {"email": "a@b.com", "password": "x", "extra": True}
        result = enforcer.apply("credentials", data)
        assert result == data

    def test_filters_to_allowed_fields(self):
        enforcer = SchemaEnforcer({"credentials": ["email", "password_hash"]})
        data = {"email": "a@b.com", "password_hash": "abc", "secret": "nope"}
        result = enforcer.apply("credentials", data)
        assert result == {"email": "a@b.com", "password_hash": "abc"}

    def test_is_valid_true(self):
        enforcer = SchemaEnforcer({"session": ["uuid", "cookie"]})
        assert enforcer.is_valid("session", {"uuid": "123", "cookie": "tok"}) is True

    def test_is_valid_false(self):
        enforcer = SchemaEnforcer({"session": ["uuid"]})
        assert enforcer.is_valid("session", {"uuid": "123", "cookie": "tok"}) is False

    def test_get_allowed_fields(self):
        enforcer = SchemaEnforcer({"orders": ["id", "amount"]})
        assert enforcer.get_allowed_fields("orders") == ["id", "amount"]
        assert enforcer.get_allowed_fields("unknown") is None


# --- SmartStorage Routing Tests ---


def _make_mock_engine():
    eng = AsyncMock()
    eng.write = AsyncMock(return_value=True)
    eng.read = AsyncMock(return_value={"data": "ok"})
    eng.delete = AsyncMock(return_value=True)
    eng.health = AsyncMock(return_value=True)
    return eng


class TestSmartStorageRouting:
    @pytest.fixture
    def storage(self):
        """SmartStorage with pre-configured mock engines."""
        engines = {
            "memory": _make_mock_engine(),
            "sqlite": _make_mock_engine(),
            "redis": _make_mock_engine(),
        }

        config = {
            "mapping": {
                "credentials": "sqlite",
                "session": "redis",
                "logs": "memory",
            },
            "schemas": {
                "credentials": ["email", "password_hash"],
            },
            "user_connections": {
                "user_42": "sqlite",
            },
            "level_routing": {
                "critical": "sqlite",
            },
        }

        s = SmartStorage(config)
        s._engines = engines
        s._setup_complete = True
        return s

    @pytest.mark.asyncio
    async def test_write_routes_by_data_type(self, storage):
        await storage.write("session", {"uuid": "abc"})
        storage._engines["redis"].write.assert_called_once_with(
            "session", {"uuid": "abc"}
        )

    @pytest.mark.asyncio
    async def test_write_routes_by_user_id(self, storage):
        await storage.write("credentials", {"email": "a@b.com"}, user_id="user_42")
        storage._engines["sqlite"].write.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_routes_by_metadata(self, storage):
        intent = MagicMock()
        intent.metadata = {"storage_preference": "memory"}
        await storage.write("credentials", {"email": "a@b.com"}, intent=intent)
        storage._engines["memory"].write.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_schema_enforced(self, storage):
        await storage.write("credentials", {
            "email": "a@b.com",
            "password_hash": "abc",
            "secret_field": "should_be_removed",
        })
        call_args = storage._engines["sqlite"].write.call_args
        stored_data = call_args[0][1]
        assert "secret_field" not in stored_data
        assert "email" in stored_data

    @pytest.mark.asyncio
    async def test_read_routes_correctly(self, storage):
        result = await storage.read("session", {"uuid": "abc"})
        storage._engines["redis"].read.assert_called_once()
        assert result == {"data": "ok"}

    @pytest.mark.asyncio
    async def test_delete_routes_correctly(self, storage):
        await storage.delete("logs", {"level": "error"})
        storage._engines["memory"].delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_checks_all(self, storage):
        assert await storage.health() is True
        storage._engines["memory"].health.assert_called_once()
        storage._engines["sqlite"].health.assert_called_once()
        storage._engines["redis"].health.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_data_type_raises(self, storage):
        with pytest.raises(ValueError, match="No engine mapped"):
            await storage.write("nonexistent", {"key": "value"})

    @pytest.mark.asyncio
    async def test_level_routing(self, storage):
        intent = MagicMock()
        intent.level = MagicMock(value="critical")
        await storage.write("session", {"uuid": "abc"}, intent=intent)
        storage._engines["sqlite"].write.assert_called_once()
