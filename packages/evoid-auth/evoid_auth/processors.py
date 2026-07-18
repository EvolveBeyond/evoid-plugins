"""Auth processors — pipeline-ready for EVOID.

authenticate: extract token from request, call provider, set ctx.state
authorize: check role/permission from ctx.state
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
    """
    metadata = ctx.intent.metadata

    # Extract token from various sources
    token = _extract_token(metadata)

    if not token:
        raise PermissionError("No authentication token provided")

    # Resolve provider
    provider_name = metadata.get("auth_provider", "default")
    try:
        provider = resolve_provider(provider_name)
    except ValueError:
        raise PermissionError(f"Auth provider '{provider_name}' not configured")

    # Call provider
    try:
        user_info = await provider(token)
    except Exception as e:
        raise PermissionError(f"Authentication failed: {e}")

    # Set context
    ctx.state["user"] = user_info.get("user", user_info)
    ctx.state["role"] = user_info.get("role", "user")
    ctx.state["auth_method"] = provider_name
    ctx.state["authenticated"] = True

    return {"authenticated": True, "user": ctx.state["user"]}


async def authorize(ctx: Any) -> dict:
    """Authorize request — check role/permissions.

    Reads from ctx.state:
        - role: set by authenticate processor

    Reads from ctx.intent.metadata:
        - required_role: minimum role needed
        - required_roles: list of acceptable roles

    Raises PermissionError if not authorized.
    """
    # Must be authenticated first
    if not ctx.state.get("authenticated"):
        raise PermissionError("Not authenticated — run 'authenticate' first")

    role = ctx.state.get("role", "user")
    metadata = ctx.intent.metadata

    # Check single role requirement
    required_role = metadata.get("required_role")
    if required_role:
        if not _role_has_permission(role, required_role):
            raise PermissionError(
                f"Insufficient permissions: need '{required_role}', have '{role}'"
            )

    # Check multiple roles
    required_roles = metadata.get("required_roles")
    if required_roles:
        if role not in required_roles:
            raise PermissionError(
                f"Role '{role}' not in allowed roles: {required_roles}"
            )

    return {"authorized": True, "role": role}


def _extract_token(metadata: dict[str, Any]) -> str | None:
    """Extract auth token from request metadata."""
    # 1. Explicit token
    if "token" in metadata:
        return metadata["token"]

    # 2. Authorization header
    headers = metadata.get("headers", {})
    auth_header = headers.get("authorization", "")

    if auth_header.startswith("Bearer "):
        return auth_header[7:]

    if auth_header.startswith("Token "):
        return auth_header[6:]

    # 3. API Key header
    api_key = headers.get("x-api-key")
    if api_key:
        return api_key

    # 4. Query parameter
    token = metadata.get("token")
    if token:
        return token

    return None


def _role_has_permission(user_role: str, required: str) -> bool:
    """Check if user role has permission for required role.

    Hierarchy: admin > editor > viewer > guest
    """
    hierarchy = {"admin": 4, "editor": 3, "viewer": 2, "guest": 1}
    user_level = hierarchy.get(user_role, 0)
    required_level = hierarchy.get(required, 0)
    return user_level >= required_level
