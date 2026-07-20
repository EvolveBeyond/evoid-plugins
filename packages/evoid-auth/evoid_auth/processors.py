"""Auth processors — pipeline-ready for EVOID.

authenticate: extract token from request, call provider, set ctx.state
authorize: check role/permission from ctx.state

IOP: processors return dicts, never raise. Errors stored in ctx.state
for downstream processors to inspect.
"""

from __future__ import annotations

from typing import Any

from .providers import resolve_provider


async def authenticate(ctx: Any) -> dict:
    """Authenticate request — extract token, resolve provider, set user info.

    Reads:
        - ctx.intent.metadata["headers"]["authorization"]
        - ctx.intent.metadata["headers"]["x-api-key"]
        - ctx.intent.metadata["token"]

    Writes to ctx.state:
        - user: authenticated user info
        - role: user role
        - auth_method: which provider was used
        - authenticated: bool
        - auth_error: str | None (on failure)
    """
    metadata = ctx.intent.metadata

    token = _extract_token(metadata)

    if not token:
        ctx.state["authenticated"] = False
        ctx.state["auth_error"] = "No authentication token provided"
        return {"authenticated": False, "error": "no_token"}

    provider_name = metadata.get("auth_provider", "default")
    try:
        provider = resolve_provider(provider_name)
    except ValueError:
        ctx.state["authenticated"] = False
        ctx.state["auth_error"] = f"Auth provider '{provider_name}' not configured"
        return {"authenticated": False, "error": "provider_not_found"}

    try:
        user_info = await provider(token)
    except Exception as e:
        ctx.state["authenticated"] = False
        ctx.state["auth_error"] = f"Authentication failed: {e}"
        return {"authenticated": False, "error": "provider_failed"}

    ctx.state["user"] = user_info.get("user", user_info)
    ctx.state["role"] = user_info.get("role", "user")
    ctx.state["auth_method"] = provider_name
    ctx.state["authenticated"] = True
    ctx.state["auth_error"] = None

    return {"authenticated": True, "user": ctx.state["user"]}


async def authorize(ctx: Any) -> dict:
    """Authorize request — check role/permissions.

    Reads from ctx.state:
        - role: set by authenticate processor
        - authenticated: set by authenticate processor

    Reads from ctx.intent.metadata:
        - required_role: minimum role needed
        - required_roles: list of acceptable roles

    Returns error dict if not authorized (never raises).
    """
    if not ctx.state.get("authenticated"):
        return {"authorized": False, "error": "not_authenticated"}

    role = ctx.state.get("role", "user")
    metadata = ctx.intent.metadata

    required_role = metadata.get("required_role")
    if required_role:
        if not _role_has_permission(role, required_role):
            ctx.state["auth_error"] = f"Need '{required_role}', have '{role}'"
            return {"authorized": False, "error": "insufficient_permissions"}

    required_roles = metadata.get("required_roles")
    if required_roles:
        if role not in required_roles:
            ctx.state["auth_error"] = f"Role '{role}' not in {required_roles}"
            return {"authorized": False, "error": "role_not_allowed"}

    return {"authorized": True, "role": role}


def _extract_token(metadata: dict[str, Any]) -> str | None:
    """Extract auth token from request metadata."""
    if "token" in metadata:
        return metadata["token"]

    headers = metadata.get("headers", {})
    auth_header = headers.get("authorization", "")

    if auth_header.startswith("Bearer "):
        return auth_header[7:]

    if auth_header.startswith("Token "):
        return auth_header[6:]

    api_key = headers.get("x-api-key")
    if api_key:
        return api_key

    query_token = metadata.get("query_token")
    if query_token:
        return query_token

    return None


_ROLE_HIERARCHY = {"admin": 4, "editor": 3, "viewer": 2, "guest": 1}


def _role_has_permission(user_role: str, required: str) -> bool:
    """Check if user role has permission for required role.

    Hierarchy: admin > editor > viewer > guest
    """
    user_level = _ROLE_HIERARCHY.get(user_role, 0)
    required_level = _ROLE_HIERARCHY.get(required, 0)
    return user_level >= required_level
