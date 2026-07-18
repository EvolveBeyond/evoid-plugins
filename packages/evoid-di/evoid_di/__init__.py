"""DI Engine for EVOID — Simple to Advanced.

Three levels of complexity:

Level 1 (Simple): register/resolve by name
    di.register("db", create_db)
    db = di.resolve("db")

Level 2 (Scoped): singleton, transient, per_user
    di.register("db", create_db, scope="singleton")
    di.register("session", create_session, scope="per_user")

Level 3 (Advanced): context-aware routing rules
    di.register("notifier", email, when={"level": "critical"})
    di.register("notifier", memory, default=True)
"""

from .engine import DIEngine
from .rules import Rule, RuleSet
from .context_extractor import extract_context

__all__ = ["DIEngine", "Rule", "RuleSet", "extract_context"]

MANIFEST = {
    "name": "evoid-di",
    "version": "0.1.0",
    "type": "engine",
    "description": "Dependency injection engine for EVOID",
    "entry_point": "evoid_di:register_plugin",
    "dependencies": ["evoid>=0.4.0"],
    "evoid_version": ">=0.4.0",
    "tags": ["di", "dependency-injection"],
}


def register_plugin():
    """Called when the plugin is loaded."""
    from evoid.engines.plugin import register

    def factory(config: dict) -> DIEngine:
        rules_config = config.get("rules", {})
        impl_config = config.get("implementations", {})
        services_config = config.get("services", {})

        implementations = _load_implementations(impl_config)
        return DIEngine(rules_config, implementations, services_config)

    register(
        name="di",
        type="engine",
        factory=factory,
        version="0.1.0",
        description="Dependency injection engine for EVOID",
    )


def _load_implementations(impl_config: dict) -> dict:
    """Load implementation factories from config."""
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
