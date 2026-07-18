"""DI Engine — simple registration to context-aware routing.

Levels:
  1. register/resolve by name
  2. scoped: singleton, transient, per_user
  3. context-aware: routing rules based on Intent/Level/Metadata/User
"""

from __future__ import annotations

from typing import Any, Callable

from .rules import RuleSet
from .context_extractor import extract_context


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
    """

    def __init__(
        self,
        rules_config: dict | None = None,
        implementations: dict[str, Any] | None = None,
        services_config: dict | None = None,
    ):
        # Level 1: Simple registry
        self._factories: dict[str, Any] = {}
        self._scopes: dict[str, str] = {}

        # Level 2: Cache
        self._singletons: dict[str, Any] = {}
        self._per_user: dict[tuple[str, str], Any] = {}

        # Level 3: Advanced routing
        self._impl_registry = implementations or {}
        self._services_config = services_config or {}
        self._rule_sets: dict[str, RuleSet] = {}
        for name, rules in (rules_config or {}).items():
            self._rule_sets[name] = RuleSet(rules)

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

    def list_services(self) -> list[str]:
        """List all registered services."""
        return list(set(list(self._factories.keys()) + list(self._rule_sets.keys())))
