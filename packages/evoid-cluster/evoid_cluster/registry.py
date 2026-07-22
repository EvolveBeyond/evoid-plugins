"""ServiceRegistry — maps service patterns to nodes with failover and load balancing."""

from __future__ import annotations

import logging
import random

from .node import ClusterNode, NodeStatus

logger = logging.getLogger("evoid.cluster.registry")


class ServiceRegistry:
    """Maps Intent patterns to cluster nodes.

    Features:
    - Multiple nodes per service (for failover + load balancing)
    - Auto-fallback to healthy nodes when primary is offline
    - Round-robin load balancing across healthy nodes
    - Dynamic service discovery via announcements
    """

    def __init__(self):
        self._nodes: dict[str, ClusterNode] = {}
        self._service_map: dict[str, list[str]] = {}  # pattern → [node_ids]
        self._rr_index: dict[str, int] = {}  # round-robin counter per service

    def register_node(self, node: ClusterNode) -> None:
        self._nodes[node.node_id] = node
        for svc in node.services:
            if svc not in self._service_map:
                self._service_map[svc] = []
            if node.node_id not in self._service_map[svc]:
                self._service_map[svc].append(node.node_id)
        logger.info(f"Node '{node.node_id}' registered with services: {node.services}")

    def unregister_node(self, node_id: str) -> None:
        node = self._nodes.pop(node_id, None)
        if node:
            for svc in node.services:
                if svc in self._service_map:
                    self._service_map[svc] = [
                        nid for nid in self._service_map[svc] if nid != node_id
                    ]
                    if not self._service_map[svc]:
                        del self._service_map[svc]
            logger.info(f"Node '{node_id}' unregistered")

    def update_services(self, node_id: str, services: list[str]) -> None:
        node = self._nodes.get(node_id)
        if not node:
            return
        old = set(node.services)
        new = set(services)
        for removed in old - new:
            if removed in self._service_map:
                self._service_map[removed] = [
                    nid for nid in self._service_map[removed] if nid != node_id
                ]
                if not self._service_map[removed]:
                    del self._service_map[removed]
        for added in new - old:
            if added not in self._service_map:
                self._service_map[added] = []
            if node_id not in self._service_map[added]:
                self._service_map[added].append(node_id)
        node.services = list(services)
        logger.debug(f"Node '{node_id}' services updated: {services}")

    def resolve(self, intent_name: str) -> ClusterNode | None:
        """Resolve with failover — returns first healthy node."""
        # Exact match
        node_ids = self._service_map.get(intent_name, [])
        node = self._find_healthy(node_ids)
        if node:
            return node

        # Wildcard match
        prefix = intent_name.split(":")[0] + ":*"
        node_ids = self._service_map.get(prefix, [])
        return self._find_healthy(node_ids)

    def resolve_load_balanced(self, intent_name: str) -> ClusterNode | None:
        """Resolve with round-robin load balancing across healthy nodes."""
        node_ids = self._service_map.get(intent_name, [])
        if not node_ids:
            prefix = intent_name.split(":")[0] + ":*"
            node_ids = self._service_map.get(prefix, [])
        if not node_ids:
            return None

        healthy = [nid for nid in node_ids if self._is_healthy(nid)]
        if not healthy:
            return None

        idx = self._rr_index.get(intent_name, 0) % len(healthy)
        self._rr_index[intent_name] = idx + 1
        return self._nodes.get(healthy[idx])

    def resolve_all(self, intent_name: str) -> list[ClusterNode]:
        """Return all healthy nodes for a service."""
        node_ids = self._service_map.get(intent_name, [])
        if not node_ids:
            prefix = intent_name.split(":")[0] + ":*"
            node_ids = self._service_map.get(prefix, [])
        return [self._nodes[nid] for nid in node_ids if self._is_healthy(nid)]

    def _find_healthy(self, node_ids: list[str]) -> ClusterNode | None:
        """Find first healthy node from list."""
        for nid in node_ids:
            if self._is_healthy(nid):
                return self._nodes.get(nid)
        return None

    def _is_healthy(self, node_id: str) -> bool:
        """Check if node is online."""
        node = self._nodes.get(node_id)
        return node is not None and node.status == NodeStatus.ONLINE

    def mark_node_offline(self, node_id: str) -> None:
        """Mark a node as offline."""
        node = self._nodes.get(node_id)
        if node:
            node.status = NodeStatus.OFFLINE
            logger.warning(f"Node '{node_id}' marked OFFLINE")

    def mark_node_online(self, node_id: str) -> None:
        """Mark a node as online."""
        node = self._nodes.get(node_id)
        if node:
            node.status = NodeStatus.ONLINE
            logger.info(f"Node '{node_id}' marked ONLINE")

    def get_node(self, node_id: str) -> ClusterNode | None:
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> list[ClusterNode]:
        return list(self._nodes.values())

    def get_all_services(self) -> dict[str, list[str]]:
        """Return all service → node_ids mappings."""
        return dict(self._service_map)

    def get_nodes_by_role(self, role: str) -> list[ClusterNode]:
        return [n for n in self._nodes.values() if role in n.roles]

    def is_local(self, intent_name: str, local_node_id: str) -> bool:
        node = self.resolve(intent_name)
        return node is not None and node.node_id == local_node_id
