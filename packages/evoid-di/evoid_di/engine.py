"""DI Engine — simple registration to context-aware routing with fault tolerance.

Levels:
  1. register/resolve by name
  2. scoped: singleton, transient, per_user
  3. context-aware: routing rules based on Intent/Level/Metadata/User

Fault Tolerance:
  - Fallback chains: service.primary → service.secondary → None
  - Health checking: verify service before using
  - Graceful degradation: log errors, return defaults
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from .rules import RuleSet
from .context_extractor import extract_context

logger = logging.getLogger("evoid.di")


class DIEngine:
    """Unified DI engine supporting all complexity levels.

    Usage:
        # Level 1: Simple
        engine = DIEngine()
        engine.register("db", create_db)
        db = engine.resolve("db")

        # Level 2: Scoped
        engine.register("db", create_db, scope="singleton")
        engine.register("session", create_session, scope="per_user")

        # Level 3: Advanced (with rules from config)
        engine = DIEngine(rules_config, implementations)
        instance = await engine.resolve("notifier", ctx)

        # Batch registration
        engine.register_many({"db": create_db, "cache": create_cache})

        # Safe resolve
        engine.resolve_or_none("nonexistent")  # returns None
    """

    __slots__ = (
        "_factories", "_scopes", "_singletons", "_per_user", "_max_per_user",
        "_impl_registry", "_services_config", "_rule_sets",
        "_fallbacks", "_health_checks", "_unhealthy",
    )

    def __init__(
        self,
        rules_config: dict | None = None,
        implementations: dict[str, Any] | None = None,
        services_config: dict | None = None,
        max_per_user: int = 1000,
    ):
        # Level 1: Simple registry
        self._factories: dict[str, Any] = {}
        self._scopes: dict[str, str] = {}

        # Level 2: Cache
        self._singletons: dict[str, Any] = {}
        self._per_user: dict[tuple[str, str], Any] = {}
        self._max_per_user = max_per_user

        # Level 3: Advanced routing
        self._impl_registry = implementations or {}
        self._services_config = services_config or {}
        self._rule_sets: dict[str, RuleSet] = {}
        for name, rules in (rules_config or {}).items():
            self._rule_sets[name] = RuleSet(rules)

        # Fault tolerance
        self._fallbacks: dict[str, list[str]] = {}  # service → fallback chain
        self._health_checks: dict[str, Callable] = {}  # service → health check fn
        self._unhealthy: set[str] = set()  # currently unhealthy services

    # ============================================================
    # Level 1: Simple register/resolve
    # ============================================================

    def register(
        self,
        name: str,
        factory: Any,
        scope: str = "singleton",
    ) -> None:
        """Register a dependency.

        Args:
            name: Dependency name (e.g., "db", "cache", "notifier")
            factory: Factory function or instance
            scope: "singleton", "transient", or "per_user"
        """
        self._factories[name] = factory
        self._scopes[name] = scope

    def resolve(self, name: str, user_id: str | None = None) -> Any:
        """Resolve a dependency by name.

        For Level 1 (no rules): uses simple registry.
        For Level 3 (with rules): must use async resolve with context.
        """
        if name in self._rule_sets:
            raise ValueError(
                f"'{name}' has routing rules — use async resolve(name, ctx) instead"
            )

        factory = self._factories.get(name)
        if factory is None:
            raise ValueError(f"No dependency registered for '{name}'")

        scope = self._scopes.get(name, "singleton")

        if scope == "transient":
            return self._create(factory)

        if scope == "per_user":
            if user_id is None:
                raise ValueError(f"'{name}' requires user_id for per_user scope")
            key = (name, user_id)
            if key not in self._per_user:
                self._evict_per_user_if_needed()
                self._per_user[key] = self._create(factory)
            return self._per_user[key]

        # Default: singleton
        if name not in self._singletons:
            self._singletons[name] = self._create(factory)
        return self._singletons[name]

    # ============================================================
    # Level 3: Context-aware resolve
    # ============================================================

    async def resolve_async(
        self,
        name: str,
        ctx: Any,
        extra: dict | None = None,
    ) -> Any:
        """Resolve with context-aware routing rules.

        Args:
            name: Service name
            ctx: EVOID Context object
            extra: Additional context for rule matching
        """
        rule_set = self._rule_sets.get(name)
        if not rule_set:
            # Fallback to Level 1
            return self.resolve(name)

        context = extract_context(ctx, extra)
        impl_name = rule_set.resolve(context)
        if not impl_name:
            raise ValueError(f"No implementation resolved for '{name}'")

        # Check scoped cache
        scope = self._services_config.get(name, {}).get("scope", "singleton")
        user_id = context.get("user_id")

        if scope == "per_user" and user_id:
            key = (name, user_id)
            if key not in self._per_user:
                self._evict_per_user_if_needed()
                self._per_user[key] = self._create_impl(impl_name)
            return self._per_user[key]

        if scope == "transient":
            return self._create_impl(impl_name)

        # Singleton
        if name not in self._singletons:
            self._singletons[name] = self._create_impl(impl_name)
        return self._singletons[name]

    async def inject(
        self,
        ctx: Any,
        service_name: str,
        key: str | None = None,
    ) -> None:
        """Resolve a service and inject it into ctx.deps."""
        if key is None:
            key = service_name

        if service_name in self._rule_sets:
            instance = await self.resolve_async(service_name, ctx)
        else:
            instance = self.resolve(service_name)

        ctx.deps[key] = instance

    # ============================================================
    # Helpers
    # ============================================================

    def _create(self, factory: Any) -> Any:
        """Create instance from factory."""
        if callable(factory):
            return factory()
        return factory

    def _create_impl(self, impl_name: str) -> Any:
        """Create instance from named implementation."""
        factory = self._impl_registry.get(impl_name)
        if not factory:
            raise ValueError(f"Implementation '{impl_name}' not registered")
        if callable(factory):
            return factory()
        return factory

    def clear(self) -> None:
        """Clear all cached instances."""
        self._singletons.clear()
        self._per_user.clear()

    def clear_user(self, user_id: str) -> None:
        """Clear cached instances for a specific user."""
        keys_to_remove = [k for k in self._per_user if k[1] == user_id]
        for key in keys_to_remove:
            del self._per_user[key]

    def _evict_per_user_if_needed(self) -> None:
        """Evict oldest entries if per-user cache exceeds max."""
        if len(self._per_user) > self._max_per_user:
            excess = len(self._per_user) - self._max_per_user
            keys = iter(self._per_user)
            for _ in range(excess):
                del self._per_user[next(keys)]

    def list_services(self) -> list[str]:
        """List all registered services."""
        return list(self._factories.keys() | self._rule_sets.keys())

    def has(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._factories or name in self._rule_sets

    def register_many(self, services: dict[str, Any], scope: str = "singleton") -> None:
        """Batch register multiple services."""
        for name, factory in services.items():
            self.register(name, factory, scope=scope)

    def resolve_or_none(self, name: str, user_id: str | None = None) -> Any | None:
        """Resolve a dependency, returning None if not found."""
        if not self.has(name):
            return None
        return self.resolve(name, user_id=user_id)

    # ============================================================
    # Fault Tolerance
    # ============================================================

    def set_fallback(self, name: str, fallbacks: list[str]) -> None:
        """Define fallback chain for a service.

        Example:
            di.set_fallback("storage.postgresql", ["storage.sqlite", "cache.redis"])
            # If postgresql fails, try sqlite, then redis
        """
        self._fallbacks[name] = fallbacks

    def set_health_check(self, name: str, check_fn: Callable[[], bool]) -> None:
        """Register a health check function for a service.

        Example:
            di.set_health_check("cache.redis", lambda: redis.ping())
        """
        self._health_checks[name] = check_fn

    def is_healthy(self, name: str) -> bool:
        """Check if a service is healthy."""
        if name in self._unhealthy:
            return False
        check = self._health_checks.get(name)
        if check:
            try:
                return check()
            except Exception as e:
                logger.warning(f"Health check failed for '{name}': {e}")
                return False
        return True

    def mark_unhealthy(self, name: str) -> None:
        """Mark a service as unhealthy."""
        self._unhealthy.add(name)
        logger.warning(f"Service '{name}' marked as unhealthy")

    def mark_healthy(self, name: str) -> None:
        """Mark a service as healthy again."""
        self._unhealthy.discard(name)

    def resolve_with_fallback(self, name: str, user_id: str | None = None) -> Any | None:
        """Resolve with automatic fallback chain.

        Tries the primary service first, then fallbacks in order.
        Returns None if all fail (never raises).
        """
        # Try primary
        if self.has(name) and self.is_healthy(name):
            try:
                return self.resolve(name, user_id=user_id)
            except Exception as e:
                logger.error(f"Failed to resolve '{name}': {e}")
                self.mark_unhealthy(name)

        # Try fallbacks
        for fallback_name in self._fallbacks.get(name, []):
            if self.has(fallback_name) and self.is_healthy(fallback_name):
                try:
                    logger.info(f"Falling back from '{name}' to '{fallback_name}'")
                    return self.resolve(fallback_name, user_id=user_id)
                except Exception as e:
                    logger.error(f"Fallback '{fallback_name}' also failed: {e}")
                    self.mark_unhealthy(fallback_name)

        logger.warning(f"All services failed for '{name}', returning None")
        return None

    def resolve_any(self, *names: str, user_id: str | None = None) -> Any | None:
        """Resolve the first available service from a list.

        Example:
            di.resolve_any("cache.redis", "cache.memory", "storage.sqlite")
        """
        for name in names:
            result = self.resolve_with_fallback(name, user_id=user_id)
            if result is not None:
                return result
        return None
