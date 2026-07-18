"""Tests for evoid-auth — providers + processors."""

import pytest
from unittest.mock import MagicMock
from evoid_auth.providers import (
    register_provider,
    resolve_provider,
    list_providers,
    clear_providers,
)
from evoid_auth.processors import authenticate, authorize, _extract_token, _role_has_permission


# ============================================================
# Provider Registry
# ============================================================


class TestProviderRegistry:
    def setup_method(self):
        clear_providers()

    def test_register_and_resolve(self):
        async def my_auth(token):
            return {"user": "alice", "role": "admin"}

        register_provider("test", my_auth)
        provider = resolve_provider("test")
        assert provider is my_auth

    def test_resolve_unknown_raises(self):
        with pytest.raises(ValueError, match="not registered"):
            resolve_provider("nonexistent")

    def test_list_providers(self):
        register_provider("a", lambda t: {})
        register_provider("b", lambda t: {})
        assert sorted(list_providers()) == ["a", "b"]


# ============================================================
# Token Extraction
# ============================================================


class TestTokenExtraction:
    def test_bearer_token(self):
        metadata = {"headers": {"authorization": "Bearer abc123"}}
        assert _extract_token(metadata) == "abc123"

    def test_token_prefix(self):
        metadata = {"headers": {"authorization": "Token xyz789"}}
        assert _extract_token(metadata) == "xyz789"

    def test_api_key(self):
        metadata = {"headers": {"x-api-key": "key123"}}
        assert _extract_token(metadata) == "key123"

    def test_explicit_token(self):
        metadata = {"token": "explicit_token"}
        assert _extract_token(metadata) == "explicit_token"

    def test_no_token(self):
        metadata = {}
        assert _extract_token(metadata) is None


# ============================================================
# Authenticate Processor
# ============================================================


class TestAuthenticate:
    def setup_method(self):
        clear_providers()

    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        async def mock_auth(token):
            return {"user": "alice", "role": "admin"}

        register_provider("default", mock_auth)

        ctx = MagicMock()
        ctx.intent = MagicMock()
        ctx.intent.metadata = {"headers": {"authorization": "Bearer test123"}}
        ctx.state = {}

        result = await authenticate(ctx)

        assert result["authenticated"] is True
        assert ctx.state["user"] == "alice"
        assert ctx.state["role"] == "admin"
        assert ctx.state["authenticated"] is True

    @pytest.mark.asyncio
    async def test_authenticate_no_token(self):
        ctx = MagicMock()
        ctx.intent = MagicMock()
        ctx.intent.metadata = {}
        ctx.state = {}

        with pytest.raises(PermissionError, match="No authentication"):
            await authenticate(ctx)

    @pytest.mark.asyncio
    async def test_authenticate_wrong_provider(self):
        ctx = MagicMock()
        ctx.intent = MagicMock()
        ctx.intent.metadata = {
            "headers": {"authorization": "Bearer test"},
            "auth_provider": "nonexistent",
        }
        ctx.state = {}

        with pytest.raises(PermissionError, match="not configured"):
            await authenticate(ctx)


# ============================================================
# Authorize Processor
# ============================================================


class TestAuthorize:
    @pytest.mark.asyncio
    async def test_authorize_success(self):
        ctx = MagicMock()
        ctx.state = {"authenticated": True, "role": "admin"}
        ctx.intent = MagicMock()
        ctx.intent.metadata = {"required_role": "editor"}

        result = await authorize(ctx)
        assert result["authorized"] is True

    @pytest.mark.asyncio
    async def test_authorize_not_authenticated(self):
        ctx = MagicMock()
        ctx.state = {}
        ctx.intent = MagicMock()
        ctx.intent.metadata = {}

        with pytest.raises(PermissionError, match="Not authenticated"):
            await authorize(ctx)

    @pytest.mark.asyncio
    async def test_authorize_insufficient_role(self):
        ctx = MagicMock()
        ctx.state = {"authenticated": True, "role": "viewer"}
        ctx.intent = MagicMock()
        ctx.intent.metadata = {"required_role": "admin"}

        with pytest.raises(PermissionError, match="Insufficient"):
            await authorize(ctx)

    @pytest.mark.asyncio
    async def test_authorize_role_in_list(self):
        ctx = MagicMock()
        ctx.state = {"authenticated": True, "role": "editor"}
        ctx.intent = MagicMock()
        ctx.intent.metadata = {"required_roles": ["admin", "editor"]}

        result = await authorize(ctx)
        assert result["authorized"] is True

    @pytest.mark.asyncio
    async def test_authorize_role_not_in_list(self):
        ctx = MagicMock()
        ctx.state = {"authenticated": True, "role": "viewer"}
        ctx.intent = MagicMock()
        ctx.intent.metadata = {"required_roles": ["admin", "editor"]}

        with pytest.raises(PermissionError, match="not in allowed"):
            await authorize(ctx)


# ============================================================
# Role Hierarchy
# ============================================================


class TestRoleHierarchy:
    def test_admin_has_all(self):
        assert _role_has_permission("admin", "admin") is True
        assert _role_has_permission("admin", "editor") is True
        assert _role_has_permission("admin", "viewer") is True

    def test_viewer_limited(self):
        assert _role_has_permission("viewer", "admin") is False
        assert _role_has_permission("viewer", "editor") is False
        assert _role_has_permission("viewer", "viewer") is True

    def test_unknown_role(self):
        assert _role_has_permission("unknown", "guest") is False
