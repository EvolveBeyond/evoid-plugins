"""evoid-cluster — connect multiple evoid nodes into a unified system.

Each node announces its services via Intent through the message bus.
ClusterBridge hooks into the local bus and forwards intents to remote nodes.
No direct data access between nodes — only Intent and Result flow.
"""

from __future__ import annotations

from .bridge import ClusterBridge, ClusterConfig
from .node import ClusterNode, NodeStatus
from .registry import ServiceRegistry
from .router import IntentRouter
from .health import HealthChecker
from .tls import ClusterTLS
from .protocol import ClusterMessage, MessageType, generate_id

__all__ = [
    "ClusterBridge",
    "ClusterConfig",
    "ClusterNode",
    "NodeStatus",
    "ServiceRegistry",
    "IntentRouter",
    "HealthChecker",
    "ClusterTLS",
    "ClusterMessage",
    "MessageType",
    "generate_id",
    "register_plugin",
]

MANIFEST = {
    "name": "evoid-cluster",
    "version": "0.1.1",
    "type": "engine",
    "description": "Cluster plugin — connect multiple evoid nodes into a unified system",
    "entry_point": "evoid_cluster:register_plugin",
    "dependencies": ["evoid>=0.4.3", "websockets>=12.0"],
    "evoid_version": ">=0.4.3",
    "tags": ["cluster", "distributed", "multi-node", "mesh"],
}


def register_plugin():
    """Register evoid-cluster with the evoid plugin registry (legacy path)."""
    try:
        from evoid.engines.plugin import register
        register(
            name="cluster",
            type="engine",
            factory=ClusterBridge,
            version="0.1.0",
            description="Cluster plugin for multi-node evoid systems",
        )
    except ImportError:
        pass


def register_handlers(config: dict | None = None) -> None:
    """Register cluster as Intent handlers.

    IOP: Cluster operations are Intents routed across nodes.
    Registers with DI as 'cluster' and connects registry for remote resolution.
    """
    from evoid_di import di

    def create_cluster():
        bridge = ClusterBridge(ClusterConfig(**config) if config else ClusterConfig())
        # Connect cluster registry to DI for remote fallback
        di.set_cluster_registry(bridge._registry)
        return bridge

    di.register("cluster", create_cluster, scope="singleton")
