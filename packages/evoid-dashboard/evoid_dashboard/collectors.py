"""Data collectors — gather info from EVOID ecosystem."""

from __future__ import annotations

from typing import Any


def collect_services(intents=None, processors=None) -> list[dict[str, Any]]:
    """Collect all registered services and their intents."""
    from evoid import all_intents, all_processors

    if intents is None:
        intents = all_intents()
    if processors is None:
        processors = all_processors()

    # Group by service (intent name prefix)
    services: dict[str, dict] = {}
    for name, intent in intents.items():
        parts = name.split(":", 1)
        service = parts[0] if len(parts) > 1 else "default"

        if service not in services:
            services[service] = {
                "name": service,
                "intents": [],
                "processors": [],
            }

        services[service]["intents"].append({
            "name": name,
            "level": intent.level.value if hasattr(intent.level, "value") else str(intent.level),
            "metadata": intent.metadata,
        })

    for name in processors:
        parts = name.split(":", 1)
        service = parts[0] if len(parts) > 1 else "default"
        if service in services:
            services[service]["processors"].append(name)

    return list(services.values())


def collect_intents(intents=None) -> list[dict[str, Any]]:
    """Collect all registered intents with full details."""
    from evoid import all_intents

    if intents is None:
        intents = all_intents()
    return [
        {
            "name": name,
            "level": intent.level.value if hasattr(intent.level, "value") else str(intent.level),
            "metadata": intent.metadata,
            "timeout": intent.timeout,
            "priority": intent.priority,
        }
        for name, intent in intents.items()
    ]


def collect_processors(processors=None) -> list[dict[str, Any]]:
    """Collect all registered processors."""
    from evoid import all_processors

    if processors is None:
        processors = all_processors()
    return [
        {
            "name": name,
            "is_coroutine": hasattr(func, "__code__") and func.__code__.co_flags & 0x100,
        }
        for name, func in processors.items()
    ]


def collect_message_history() -> list[dict[str, Any]]:
    """Collect message bus history."""
    try:
        from evoid.core.message_bus import get_history
        history = get_history()
        return [
            {
                "source": msg.source,
                "intent": msg.intent.name if hasattr(msg.intent, "name") else str(msg.intent),
                "target": msg.target,
                "metadata": msg.metadata,
            }
            for msg in history
        ]
    except Exception:
        return []


def collect_db_tables() -> dict[str, list[dict[str, Any]]]:
    """Collect database schemas from storage engines."""
    from evoid.engines.plugin import list_plugins, resolve

    tables: dict[str, list] = {}

    for plugin in list_plugins():
        if plugin.type == "engine":
            try:
                engine = resolve(plugin.name, "engine")
                if engine and hasattr(engine, "list_keys"):
                    # This is a storage engine
                    tables[plugin.name] = [
                        {"name": plugin.name, "type": plugin.type}
                    ]
            except Exception:
                pass

    return tables


def collect_pipeline_overrides() -> dict[str, list[str]]:
    """Collect pipeline overrides."""
    from evoid.core.extend import list_overrides
    return list_overrides()


def collect_system_info() -> dict[str, Any]:
    """Collect system information."""
    import sys
    import platform

    return {
        "python": sys.version,
        "platform": platform.platform(),
        "evoid_version": _get_evoid_version(),
    }


def _get_evoid_version() -> str:
    try:
        import evoid
        return getattr(evoid, "__version__", "unknown")
    except Exception:
        return "unknown"
