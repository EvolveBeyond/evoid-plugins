"""Admin API — cluster management endpoints."""

from __future__ import annotations

from typing import Any


def register_admin_intents(bridge) -> None:
    """Register admin intents for cluster management.

    These are IOP-compatible endpoints that can be called
    via the evoid message bus or HTTP.
    """
    from evoid import Intent, Level, execute
    from evoid.core.extend import add_intent_with_pipeline

    async def _handle_list_nodes(ctx) -> dict:
        nodes = bridge.get_all_nodes()
        return {"nodes": [n.to_dict() for n in nodes]}

    async def _handle_list_services(ctx) -> dict:
        services = bridge.get_all_services()
        return {"services": services}

    async def _handle_health_check(ctx) -> dict:
        return bridge.health()

    async def _handle_register_node(ctx) -> dict:
        from .node import ClusterNode
        data = ctx.metadata.get("body", {})
        node = ClusterNode(
            node_id=data["node_id"],
            name=data.get("name", data["node_id"]),
            host=data["host"],
            port=data["port"],
            roles=data.get("roles", []),
            services=data.get("services", []),
        )
        bridge.register_node(node)
        return {"status": "ok", "node_id": node.node_id}

    async def _handle_unregister_node(ctx) -> dict:
        node_id = ctx.metadata.get("params", {}).get("node_id", "")
        bridge.unregister_node(node_id)
        return {"status": "ok", "removed": node_id}

    add_intent_with_pipeline("cluster:list_nodes", ("intent_extractor",), _handle_list_nodes)
    add_intent_with_pipeline("cluster:list_services", ("intent_extractor",), _handle_list_services)
    add_intent_with_pipeline("cluster:health", ("intent_extractor",), _handle_health_check)
    add_intent_with_pipeline("cluster:register_node", ("intent_extractor",), _handle_register_node)
    add_intent_with_pipeline("cluster:unregister_node", ("intent_extractor",), _handle_unregister_node)
