"""HealthChecker — heartbeat, failover, and auto-reconnect for cluster nodes."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from .node import NodeStatus
from .protocol import ClusterMessage, MessageType, make_message

if TYPE_CHECKING:
    from .bridge import ClusterBridge

logger = logging.getLogger("evoid.cluster.health")


class HealthChecker:
    """Monitors node health with auto-reconnect.

    Features:
    - Heartbeat-based liveness detection
    - Auto-reconnect when nodes come back online
    - Graceful failover marking
    """

    def __init__(
        self,
        bridge: ClusterBridge,
        interval: float = 5.0,
        timeout: float = 15.0,
        reconnect_interval: float = 10.0,
    ):
        self._bridge = bridge
        self._interval = interval
        self._timeout = timeout
        self._reconnect_interval = reconnect_interval
        self._last_seen: dict[str, float] = {}
        self._running = False

    async def start(self) -> None:
        self._running = True
        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._reconnect_loop())

    def stop(self) -> None:
        self._running = False

    def record_heartbeat(self, node_id: str) -> None:
        self._last_seen[node_id] = time.time()
        node = self._bridge.registry.get_node(node_id)
        if node:
            node.last_heartbeat = time.time()
            if node.status != NodeStatus.ONLINE:
                logger.info(f"Node '{node_id}' is back ONLINE")
            node.status = NodeStatus.ONLINE
            self._bridge.registry.mark_node_online(node_id)

    async def _heartbeat_loop(self) -> None:
        while self._running:
            now = time.time()

            # Send heartbeat to all connected nodes
            for node_id in list(self._bridge._nodes_ws.keys()):
                msg = make_message(
                    MessageType.HEARTBEAT,
                    self._bridge.local_node_id,
                    node_id,
                    {"load": 0.0, "uptime": 0},
                )
                try:
                    await self._bridge.send(node_id, msg)
                except Exception:
                    pass

            # Check for dead nodes
            for node_id, last in list(self._last_seen.items()):
                if now - last > self._timeout:
                    await self._handle_node_offline(node_id)

            await asyncio.sleep(self._interval)

    async def _reconnect_loop(self) -> None:
        """Periodically try to reconnect to offline nodes."""
        while self._running:
            await asyncio.sleep(self._reconnect_interval)

            for peer_id, peer_config in self._bridge.config.peers.items():
                if peer_id in self._bridge._nodes_ws:
                    continue  # Already connected

                node = self._bridge.registry.get_node(peer_id)
                if node and node.status == NodeStatus.ONLINE:
                    continue  # Already online

                logger.info(f"Attempting reconnect to '{peer_id}'")
                try:
                    await self._bridge._connect_to_peer(peer_id, peer_config)
                    logger.info(f"Reconnected to '{peer_id}'")
                except Exception as e:
                    logger.debug(f"Reconnect to '{peer_id}' failed: {e}")

    async def _handle_node_offline(self, node_id: str) -> None:
        node = self._bridge.registry.get_node(node_id)
        if node and node.status == NodeStatus.ONLINE:
            logger.warning(f"Node '{node_id}' is OFFLINE (heartbeat timeout)")
            self._bridge.registry.mark_node_offline(node_id)
            # Disconnect WebSocket
            ws = self._bridge._nodes_ws.pop(node_id, None)
            if ws:
                try:
                    await ws.close()
                except Exception:
                    pass

    async def handle_heartbeat(self, msg: ClusterMessage) -> None:
        """Process incoming heartbeat from a remote node."""
        self.record_heartbeat(msg.source_node)
        # Send pong back
        if msg.target_node == self._bridge.local_node_id:
            pong = make_message(
                MessageType.HEARTBEAT,
                self._bridge.local_node_id,
                msg.source_node,
                {"load": 0.0, "uptime": 0},
            )
            await self._bridge.send(msg.source_node, pong)
