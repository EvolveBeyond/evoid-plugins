"""EVOID Dashboard — Monitor services, data lineage, databases, logs.

IOP: Dashboard is a processor that reads from the event system and registry.

Usage:
    from evoid_dashboard import create_dashboard

    # Mount alongside your app
    app = create_dashboard(port=8001)
"""

from .app import create_dashboard
from . collectors import (
    collect_services,
    collect_intents,
    collect_processors,
    collect_message_history,
    collect_db_tables,
)

__all__ = [
    "create_dashboard",
    "collect_services",
    "collect_intents",
    "collect_processors",
    "collect_message_history",
    "collect_db_tables",
]

MANIFEST = {
    "name": "evoid-dashboard",
    "version": "0.1.0",
    "type": "adapter",
    "description": "Monitoring dashboard for EVOID ecosystem",
    "entry_point": "evoid_dashboard:register_plugin",
    "dependencies": ["evoid>=0.4.0"],
    "evoid_version": ">=0.4.0",
    "tags": ["dashboard", "monitoring", "ui"],
}


def register_plugin():
    """Called when the plugin is loaded (legacy path)."""
    from evoid.engines.plugin import register
    register(
        name="dashboard",
        type="adapter",
        factory=create_dashboard,
        version="0.1.0",
        description="Monitoring dashboard for EVOID",
    )


def register_handlers(host: str = "0.0.0.0", port: int = 8001) -> None:
    """Register dashboard as an adapter handler.

    IOP: Dashboard is an adapter that exposes monitoring data.
    """
    # Dashboard doesn't use standard storage/cache Intents
    # It's an adapter that creates its own ASGI app
