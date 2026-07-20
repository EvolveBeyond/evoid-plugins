"""ClusterBridge — the core of evoid-cluster.

Hooks into the local message bus and bridges intents to remote nodes.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import websockets

from .node import ClusterNode, NodeStatus
from .registry import ServiceRegistry
from .router import IntentRouter
from .health import HealthChecker
from .tls import ClusterTLS
from .protocol import (
    ClusterMessage, MessageType, generate_id,
    encode_announce, decode_intent, _encode, _decode, make_message,
)


@dataclass
class ClusterConfig:
    node_id: str = "node-1"
    name: str = "EVOID Node"
    host: str = "0.0.0.0"
    port: int = 9100
    roles: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    secret: str = ""
    cert_dir: str | None = None
    heartbeat_interval: float = 5.0
    heartbeat_timeout: float = 15.0
    peers: dict[str, dict] = field(default_factory=dict)

    @classmethod
    def from_toml(cls, path: str) -> ClusterConfig:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        with open(path, "rb") as f:
            data = tomllib.load(f)
        node = data.get("node", {})
        cluster = data.get("cluster", {})
        services = data.get("services", {})
        peers = cluster.get("peers", {})
        return cls(
            node_id=node.get("id", "node-1"),
            name=node.get("name", "EVOID Node"),
            host=node.get("host", "0.0.0.0"),
            port=node.get("port", 9100),
            roles=node.get("roles", []),
            services=[k for k in services if services[k] == "local"],
            secret=cluster.get("secret", ""),
            cert_dir=cluster.get("cert_dir"),
            heartbeat_interval=cluster.get("heartbeat_interval", 5.0),
            heartbeat_timeout=cluster.get("heartbeat_timeout", 15.0),
            peers=peers,
        )


class ClusterBridge:
    """The core cluster bridge.

    Hooks into the local message bus and forwards intents
    to remote nodes based on service registry.
    """

    def __init__(self, config: ClusterConfig):
        self.config = config
        self.local_node_id = config.node_id
        self._registry = ServiceRegistry()
        self._router = IntentRouter(self._registry, config.node_id, self.send)
        self._tls = ClusterTLS(config.cert_dir, config.secret)
        self._health = HealthChecker(self, config.heartbeat_interval, config.heartbeat_timeout)
        self._nodes_ws: dict[str, websockets.WebSocketServerProtocol] = {}
        self._server = None
        self._running = False

    @property
    def registry(self) -> ServiceRegistry:
        return self._registry

    @property
    def router(self) -> IntentRouter:
        return self._router

    async def start(self) -> None:
        """Start the cluster bridge."""
        self._running = True

        # 1. Setup TLS
        self._tls.setup(self.local_node_id)

        # 2. Register local node
        local_node = ClusterNode(
            node_id=self.local_node_id,
            name=self.config.name,
            host=self.config.host,
            port=self.config.port,
            roles=self.config.roles,
            services=self.config.services,
            status=NodeStatus.ONLINE,
        )
        self._registry.register_node(local_node)

        # 3. Start WebSocket server
        await self._start_server()

        # 4. Connect to configured peers
        await self._connect_peers()

        # 5. Announce services to connected peers
        await self._announce_services()

        # 6. Start heartbeat
        await self._health.start()

        # 7. Hook into local message bus
        self._hook_bus()

    async def stop(self) -> None:
        self._running = False
        self._health.stop()
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        for ws in self._nodes_ws.values():
            try:
                await ws.close()
            except Exception:
                pass
        self._nodes_ws.clear()

    def _hook_bus(self) -> None:
        """Hook into local message bus to intercept outgoing intents."""
        from evoid import subscribe
        for svc in self.config.services:
            subscribe(svc, self._make_local_handler(svc))

    def _make_local_handler(self, pattern: str):
        async def handler(intent):
            node = self._registry.resolve(intent.name)
            if node and node.node_id != self.local_node_id:
                return await self._router.route(intent)
            return None
        return handler

    async def _start_server(self) -> None:
        ssl_ctx = self._tls.create_ssl_context(server_side=True) if self._tls.has_certs else None
        self._server = await websockets.serve(
            self._handle_connection,
            self.config.host,
            self.config.port,
            ssl=ssl_ctx,
        )

    async def _handle_connection(self, ws, path=None) -> None:
        remote_node_id = None
        try:
            async for raw in ws:
                msg = ClusterMessage.decode(raw)

                # Record heartbeat
                if msg.type == MessageType.HEARTBEAT:
                    self._health.record_heartbeat(msg.source_node)
                    if msg.target_node == self.local_node_id:
                        # Reply with heartbeat
                        pong = make_message(
                            MessageType.HEARTBEAT,
                            self.local_node_id,
                            msg.source_node,
                            {"load": 0.0, "uptime": 0},
                        )
                        await ws.send(pong.encode())
                    continue

                # Handle announce
                if msg.type == MessageType.ANNOUNCE:
                    data = _decode(msg.payload)
                    node = self._registry.get_node(msg.source_node)
                    if node:
                        self._registry.update_services(msg.source_node, data.get("services", []))
                    continue

                # Handle withdraw
                if msg.type == MessageType.WITHDRAW:
                    self._registry.unregister_node(msg.source_node)
                    ws_close = self._nodes_ws.pop(msg.source_node, None)
                    if ws_close:
                        await ws_close.close()
                    continue

                # Route intent/result/error
                await self._router.handle_incoming(msg)
        except websockets.ConnectionClosed:
            pass
        finally:
            if remote_node_id:
                self._nodes_ws.pop(remote_node_id, None)

    async def _connect_peers(self) -> None:
        for peer_id, peer_info in self.config.peers.items():
            await self._connect_to_peer(peer_id, peer_info["host"], peer_info["port"])

    async def _connect_to_peer(self, peer_id: str, host: str, port: int) -> None:
        ssl_ctx = self._tls.create_ssl_context(server_side=False) if self._tls.has_certs else None
        try:
            ws = await websockets.connect(
                f"ws://{host}:{port}",
                ssl=ssl_ctx,
                additional_headers={"X-Node-ID": self.local_node_id},
            )
            self._nodes_ws[peer_id] = ws
            node = ClusterNode(
                node_id=peer_id,
                name=peer_id,
                host=host,
                port=port,
                status=NodeStatus.ONLINE,
            )
            self._registry.register_node(node)
            # Listen for messages in background
            asyncio.create_task(self._listen_peer(peer_id, ws))
        except Exception as e:
            print(f"[cluster] Failed to connect to {peer_id}: {e}")

    async def _listen_peer(self, peer_id: str, ws) -> None:
        try:
            async for raw in ws:
                msg = ClusterMessage.decode(raw)
                if msg.type == MessageType.HEARTBEAT:
                    self._health.record_heartbeat(msg.source_node)
                else:
                    await self._router.handle_incoming(msg)
        except websockets.ConnectionClosed:
            self._nodes_ws.pop(peer_id, None)
            node = self._registry.get_node(peer_id)
            if node:
                node.status = NodeStatus.OFFLINE

    async def _announce_services(self) -> None:
        msg = make_message(
            MessageType.ANNOUNCE,
            self.local_node_id,
            None,
            encode_announce(self.config.services, self.config.name, self.config.roles),
        )
        await self._broadcast(msg)

    async def send(self, target_node_id: str, msg: ClusterMessage) -> None:
        ws = self._nodes_ws.get(target_node_id)
        if ws:
            await ws.send(msg.encode())

    async def _broadcast(self, msg: ClusterMessage) -> None:
        for ws in self._nodes_ws.values():
            try:
                await ws.send(msg.encode())
            except Exception:
                pass

    def register_node(self, node: ClusterNode) -> None:
        self._registry.register_node(node)

    def unregister_node(self, node_id: str) -> None:
        self._registry.unregister_node(node_id)

    def get_all_nodes(self) -> list[ClusterNode]:
        return self._registry.get_all_nodes()

    def get_all_services(self) -> dict[str, str]:
        return self._registry.get_all_services()

    def health(self) -> dict:
        nodes = self.get_all_nodes()
        online = sum(1 for n in nodes if n.status == NodeStatus.ONLINE)
        return {
            "node_id": self.local_node_id,
            "total_nodes": len(nodes),
            "online_nodes": online,
            "offline_nodes": len(nodes) - online,
            "total_services": len(self.get_all_services()),
            "uptime": time.time(),
        }

    def service(self, pattern: str):
        """Decorator to register a local service handler."""
        def decorator(fn):
            if pattern not in self.config.services:
                self.config.services.append(pattern)
            return fn
        return decorator
