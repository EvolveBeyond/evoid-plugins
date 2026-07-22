"""Auth Engine for EVOID — bring your own provider.

IOP: Auth = Protocol + Pipeline processors.
User defines how to authenticate, EVOID handles when.

Usage:
    from evoid_auth import register_provider

    # Your auth logic — any method you want
    async def my_auth(token: str) -> dict:
        user = await db.find_by_token(token)
        return {"user": user.name, "role": user.role}

    register_provider("my_auth", my_auth)

    # Wire to pipeline
    from evoid.core.extend import before
    before("GET:/users", "authenticate")
"""

from .providers import (
    AuthProvider,
    register_provider,
    resolve_provider,
    list_providers,
)
from .processors import authenticate, authorize

__all__ = [
    "AuthProvider",
    "register_provider",
    "resolve_provider",
    "list_providers",
    "authenticate",
    "authorize",
]

MANIFEST = {
    "name": "evoid-auth",
    "version": "0.1.0",
    "type": "engine",
    "description": "Auth engine — bring your own provider",
    "entry_point": "evoid_auth:register_plugin",
    "dependencies": ["evoid>=0.4.0"],
    "evoid_version": ">=0.4.0",
    "tags": ["auth", "authentication", "authorization"],
}


def register_plugin():
    """Called when the plugin is loaded (legacy path)."""
    from evoid.engines.plugin import register
    from evoid import register_processor

    register_processor("authenticate", authenticate)
    register_processor("authorize", authorize)

    register(
        name="auth",
        type="engine",
        factory=lambda config: {"providers": list_providers()},
        version="0.1.0",
        description="Auth engine with pluggable providers",
    )


def register_handlers() -> None:
    """Register auth as Intent handlers.

    IOP: Auth operations are Intents.
    authenticate and authorize are registered as pipeline processors.
    Registers with DI as 'auth' for dependency resolution.
    """
    from evoid_di import di
    from evoid.core import register as register_intent, register_processor
    from evoid.core.intents import AUTH_AUTHENTICATE, AUTH_AUTHORIZE

    di.register("auth", lambda: {"providers": list_providers()}, scope="singleton")

    register_intent(AUTH_AUTHENTICATE)
    register_intent(AUTH_AUTHORIZE)
    register_processor("auth.authenticate", authenticate)
    register_processor("auth.authorize", authorize)
