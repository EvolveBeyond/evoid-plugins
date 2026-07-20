"""ClusterNode — represents a node in the cluster."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class NodeStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


@dataclass
class ClusterNode:
    node_id: str
    name: str
    host: str
    port: int
    roles: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.OFFLINE
    last_heartbeat: float = 0.0

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "roles": self.roles,
            "services": self.services,
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ClusterNode:
        return cls(
            node_id=data["node_id"],
            name=data["name"],
            host=data["host"],
            port=data["port"],
            roles=data.get("roles", []),
            services=data.get("services", []),
            status=NodeStatus(data.get("status", "offline")),
            last_heartbeat=data.get("last_heartbeat", 0.0),
        )
