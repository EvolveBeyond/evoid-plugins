"""Shared utilities for EVOID plugins."""

from __future__ import annotations

from typing import Any

from evoid.engines.plugin import resolve as _resolve


def resolve_engine(name: str, engine_type: str = "engine") -> Any:
    """Resolve an engine from the plugin registry.

    Args:
        name: Engine name (e.g., "sqlite", "redis", "postgresql")
        engine_type: Plugin type (e.g., "engine", "storage", "cache")

    Returns:
        The engine factory or instance
    """
    return _resolve(name, engine_type)


async def inject_deps(ctx, engines: dict[str, str]) -> None:
    """Inject multiple engines into ctx.deps.

    Args:
        ctx: The Context object
        engines: Mapping of dep_name -> engine_name (e.g., {"storage": "sqlite", "cache": "redis"})

    Example:
        await inject_deps(ctx, {"storage": "sqlite", "cache": "redis"})
        # ctx.deps["storage"] = sqlite engine
        # ctx.deps["cache"] = redis engine
    """
    for dep_name, engine_name in engines.items():
        if dep_name not in ctx.deps:
            ctx.deps[dep_name] = resolve_engine(engine_name)
