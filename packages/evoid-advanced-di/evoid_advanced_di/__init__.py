"""Advanced DI Engine for EVOID.

Context-aware dependency injection that routes implementations based on:
- Intent level (EPHEMERAL/STANDARD/CRITICAL)
- Intent metadata
- User role and ID
- Custom rules from config

IOP: Plugin registry pattern — register, resolve, use.
"""

from __future__ import annotations

from .engine import AdvancedDIEngine
from .rules import Rule, RuleSet

MANIFEST = {
    "name": "evoid-advanced-di",
    "version": "0.1.0",
    "type": "engine",
    "description": "Advanced DI engine with context-aware routing",
    "entry_point": "evoid_advanced_di:register_plugin",
    "dependencies": ["evoid>=0.4.0"],
    "evoid_version": ">=0.4.0",
    "tags": ["di", "dependency-injection", "context-aware"],
}


def register_plugin():
    """Called when the plugin is loaded."""
    from evoid.engines.plugin import register

    def factory(config: dict) -> AdvancedDIEngine:
        rules_config = config.get("rules", {})
        impl_config = config.get("implementations", {})
        services_config = config.get("services", {})

        implementations = _load_implementations(impl_config)
        return AdvancedDIEngine(rules_config, implementations, services_config)

    register(
        name="advanced_di",
        type="engine",
        factory=factory,
        version="0.1.0",
        description="Advanced DI engine with context-aware routing",
    )


def _load_implementations(impl_config: dict) -> dict:
    """Load implementation factories from config.

    Config format:
        [engines.advanced_di.implementations]
        email_notifier = "my_project.notifiers:create_email_notifier"
        simple_auth = "my_project.auth:create_simple_auth"
    """
    import importlib

    implementations = {}
    for name, spec in impl_config.items():
        if ":" in spec:
            module_path, func_name = spec.rsplit(":", 1)
        else:
            module_path, func_name = spec, "create"

        mod = importlib.import_module(module_path)
        implementations[name] = getattr(mod, func_name)

    return implementations
