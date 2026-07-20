"""Dashboard extension — adds cluster panel to evoid-dashboard."""

from __future__ import annotations


def register_dashboard(bridge) -> None:
    """Register cluster endpoints with the evoid dashboard."""
    try:
        from evoid_dashboard import add_panel
        add_panel("cluster", {
            "title": "Cluster",
            "tabs": ["nodes", "services", "health"],
            "endpoints": {
                "nodes": "/api/cluster/nodes",
                "services": "/api/cluster/services",
                "health": "/api/cluster/health",
            },
        })
    except ImportError:
        pass
