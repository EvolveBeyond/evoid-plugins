"""Advanced DI Engine — context-aware dependency resolution.

Routes service implementations based on Intent level, metadata, user role.
Supports scoped instances (singleton, per_user, transient).
"""

from __future__ import annotations

from typing import Any, Callable

from .rules import RuleSet
from .context_extractor import extract_context


class AdvancedDIEngine:
    """Context-aware DI engine with configurable routing rules.

    Usage:
        engine = AdvancedDIEngine(rules_config, implementations)
        instance = await engine.resolve("notifier", ctx)
        ctx.deps["notifier"] = instance
    """

    def __init__(
        self,
        rules_config: dict,
        implementations: dict[str, Any],
        services_config: dict | None = None,
    ):
        self.implementations = implementations
        self.services_config = services_config or {}
        self._scoped_cache: dict[tuple[str, str | None], Any] = {}

        # Build RuleSet for each service
        self.rule_sets: dict[str, RuleSet] = {}
        for service_name, rules in rules_config.items():
            self.rule_sets[service_name] = RuleSet(rules)

    async def resolve(
        self,
        service_name: str,
        ev_ctx: Any,
        extra: dict[str, Any] | None = None,
    ) -> Any:
        """Resolve the appropriate implementation for a service.

        Args:
            service_name: Service to resolve (e.g., "notifier", "auth")
            ev_ctx: EVOID Context object
            extra: Additional context for rule matching

        Returns:
            The resolved implementation instance
        """
        rule_set = self.rule_sets.get(service_name)
        if not rule_set:
            raise ValueError(f"No rules defined for service '{service_name}'")

        context = extract_context(ev_ctx, extra)
        impl_name = rule_set.resolve(context)
        if not impl_name:
            raise ValueError(
                f"No implementation resolved for '{service_name}' "
                f"with context level={context.get('level')}, "
                f"user_role={context.get('user_role')}"
            )

        # Check scope
        scope = self.services_config.get(service_name, {}).get("scope", "singleton")
        user_id = context.get("user_id")

        if scope == "per_user" and user_id:
            cache_key = (service_name, user_id)
            if cache_key in self._scoped_cache:
                return self._scoped_cache[cache_key]
            instance = await self._create_instance(impl_name, ev_ctx, extra)
            self._scoped_cache[cache_key] = instance
            return instance

        if scope == "transient":
            return await self._create_instance(impl_name, ev_ctx, extra)

        # Default: singleton (cache by service name only)
        cache_key = (service_name, None)
        if cache_key in self._scoped_cache:
            return self._scoped_cache[cache_key]
        instance = await self._create_instance(impl_name, ev_ctx, extra)
        self._scoped_cache[cache_key] = instance
        return instance

    async def _create_instance(
        self,
        impl_name: str,
        ev_ctx: Any,
        extra: dict | None,
    ) -> Any:
        """Create an instance from the registered factory."""
        factory = self.implementations.get(impl_name)
        if not factory:
            raise ValueError(f"Implementation '{impl_name}' not registered")

        if callable(factory):
            result = factory()
            if hasattr(result, "__await__"):
                result = await result
            return result
        return factory

    async def inject(
        self,
        ev_ctx: Any,
        service_name: str,
        key: str | None = None,
    ) -> None:
        """Resolve a service and inject it into ctx.deps."""
        if key is None:
            key = service_name
        instance = await self.resolve(service_name, ev_ctx)
        ev_ctx.deps[key] = instance

    def clear_cache(self) -> None:
        """Clear all cached instances."""
        self._scoped_cache.clear()

    def list_services(self) -> list[str]:
        """List all services with defined rules."""
        return list(self.rule_sets.keys())
