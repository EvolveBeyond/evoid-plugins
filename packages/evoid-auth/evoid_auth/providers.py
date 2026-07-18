"""Auth providers — protocol + registry.

IOP: Provider is a function, not a class.
User defines the auth logic, EVOID calls it.
"""

from __future__ import annotations

from typing import Any, Callable, Protocol


class AuthProvider(Protocol):
    """Contract for auth providers.

    A provider is any async function that takes a token
    and returns user info dict.

    Example:
        async def my_provider(token: str) -> dict:
            return {"user": "alice", "role": "admin"}
    """

    async def __call__(self, token: str) -> dict[str, Any]: ...


# Provider registry: name -> callable
_providers: dict[str, Callable] = {}


def register_provider(name: str, provider: Callable) -> None:
    """Register an auth provider.

    Args:
        name: Provider name (e.g., "jwt", "api_key", "my_custom")
        provider: Async function(token: str) -> dict

    Example:
        async def jwt_provider(token: str) -> dict:
            payload = jwt.decode(token, SECRET)
            return {"user": payload["sub"], "role": payload["role"]}

        register_provider("jwt", jwt_provider)
    """
    _providers[name] = provider


def resolve_provider(name: str) -> Callable:
    """Get a registered provider by name.

    Raises ValueError if not found.
    """
    provider = _providers.get(name)
    if provider is None:
        available = ", ".join(_providers.keys()) or "none"
        raise ValueError(
            f"Auth provider '{name}' not registered. "
            f"Available: {available}"
        )
    return provider


def list_providers() -> list[str]:
    """List all registered provider names."""
    return list(_providers.keys())


def clear_providers() -> None:
    """Clear all registered providers (for testing)."""
    _providers.clear()
