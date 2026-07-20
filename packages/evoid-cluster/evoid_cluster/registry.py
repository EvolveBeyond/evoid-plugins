"""ServiceRegistry — maps service patterns to nodes."""

from __future__ import annotations

from .node import ClusterNode


class ServiceRegistry:
    """Maps Intent patterns to cluster nodes.

    Each node announces its services via cluster:announce Intent.
    The registry keeps a live map of pattern → node_id.
    """

    def __init__(self):
        self._nodes: dict[str, ClusterNode] = {}
        self._service_map: dict[str, str] = {}  # pattern → node_id

    def register_node(self, node: ClusterNode) -> None:
        self._nodes[node.node_id] = node
        for svc in node.services:
            self._service_map[svc] = node.node_id

    def unregister_node(self, node_id: str) -> None:
        node = self._nodes.pop(node_id, None)
        if node:
            for svc in node.services:
                if self._service_map.get(svc) == node_id:
                    del self._service_map[svc]

    def update_services(self, node_id: str, services: list[str]) -> None:
        node = self._nodes.get(node_id)
        if not node:
            return
        old = set(node.services)
        new = set(services)
        for removed in old - new:
            if self._service_map.get(removed) == node_id:
                del self._service_map[removed]
        for added in new - old:
            self._service_map[added] = node_id
        node.services = list(services)

    def resolve(self, intent_name: str) -> ClusterNode | None:
        if intent_name in self._service_map:
            node_id = self._service_map[intent_name]
            return self._nodes.get(node_id)
        prefix = intent_name.split(":")[0] + ":*"
        if prefix in self._service_map:
            node_id = self._service_map[prefix]
            return self._nodes.get(node_id)
        return None

    def get_node(self, node_id: str) -> ClusterNode | None:
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> list[ClusterNode]:
        return list(self._nodes.values())

    def get_all_services(self) -> dict[str, str]:
        return dict(self._service_map)

    def get_nodes_by_role(self, role: str) -> list[ClusterNode]:
        return [n for n in self._nodes.values() if role in n.roles]

    def is_local(self, intent_name: str, local_node_id: str) -> bool:
        node = self.resolve(intent_name)
        return node is not None and node.node_id == local_node_id
