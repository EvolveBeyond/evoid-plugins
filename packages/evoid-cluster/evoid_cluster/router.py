"""IntentRouter — routes intents between cluster nodes with load balancing."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from .protocol import (
    ClusterMessage, MessageType, generate_id,
    encode_intent, decode_intent, encode_result, decode_result, _encode,
)
from .registry import ServiceRegistry

logger = logging.getLogger("evoid.cluster.router")


class IntentRouter:
    """Routes intents between local and remote nodes.

    Features:
    - Load balancing across healthy nodes
    - Automatic failover on timeout
    - Message bus for internal communication
    """

    def __init__(self, registry: ServiceRegistry, local_node_id: str, send_fn):
        self._registry = registry
        self._local_node_id = local_node_id
        self._send = send_fn
        self._pending: dict[str, asyncio.Future] = {}
        self._local_execute = None

    def set_local_executor(self, fn) -> None:
        self._local_execute = fn

    async def route(self, intent: Any, timeout: float | None = None, load_balance: bool = True) -> Any:
        """Route an intent — local or remote with load balancing."""
        if load_balance:
            node = self._registry.resolve_load_balanced(intent.name)
        else:
            node = self._registry.resolve(intent.name)

        if node is None:
            raise ValueError(f"No node handles service: {intent.name}")

        if node.node_id == self._local_node_id:
            return await self._execute_local(intent)

        return await self._forward_remote(intent, node, timeout or getattr(intent, "timeout", 10.0))

    async def route_with_failover(self, intent: Any, timeout: float | None = None) -> Any:
        """Route with automatic failover — try all healthy nodes."""
        nodes = self._registry.resolve_all(intent.name)
        if not nodes:
            raise ValueError(f"No node handles service: {intent.name}")

        last_error = None
        for node in nodes:
            if node.node_id == self._local_node_id:
                try:
                    return await self._execute_local(intent)
                except Exception as e:
                    last_error = e
                    logger.warning(f"Local execution failed: {e}")
                    continue

            try:
                return await self._forward_remote(intent, node, timeout or 5.0)
            except Exception as e:
                last_error = e
                logger.warning(f"Node '{node.node_id}' failed: {e}")
                self._registry.mark_node_offline(node.node_id)
                continue

        raise RuntimeError(f"All nodes failed for '{intent.name}': {last_error}")

    async def _execute_local(self, intent: Any) -> Any:
        """Execute intent locally via message bus."""
        if self._local_execute:
            return await self._local_execute(intent)
        from evoid import execute
        return await execute(intent)

    async def _forward_remote(self, intent: Any, node: Any, timeout: float) -> Any:
        """Forward intent to remote node via WebSocket."""
        msg = ClusterMessage(
            type=MessageType.INTENT,
            source_node=self._local_node_id,
            target_node=node.node_id,
            message_id=generate_id(),
            timestamp=time.time(),
            payload=encode_intent(intent),
        )

        future: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending[msg.message_id] = future

        try:
            await self._send(node.node_id, msg)
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(msg.message_id, None)
            raise TimeoutError(f"Node {node.node_id} timed out for {intent.name}")

    async def handle_incoming(self, msg: ClusterMessage) -> None:
        """Handle incoming message from a remote node."""
        if msg.type == MessageType.INTENT:
            await self._handle_remote_intent(msg)
        elif msg.type == MessageType.RESULT:
            await self._handle_remote_result(msg)
        elif msg.type == MessageType.ERROR:
            await self._handle_remote_error(msg)

    async def _handle_remote_intent(self, msg: ClusterMessage) -> None:
        """Execute an intent forwarded from a remote node, send result back."""
        intent_data = decode_intent(msg.payload)
        try:
            from evoid import Intent, Level
            level = Level(intent_data.get("level", "standard"))
            intent = Intent(
                name=intent_data["name"],
                level=level,
                metadata=intent_data.get("metadata", {}),
                timeout=intent_data.get("timeout", 10.0),
                priority=intent_data.get("priority", 0),
            )
            result = await self._execute_local(intent)
            result_value = getattr(result, "value", result) if result else None
            result_success = getattr(result, "success", True) if result else True

            reply = ClusterMessage(
                type=MessageType.RESULT,
                source_node=self._local_node_id,
                target_node=msg.source_node,
                message_id=msg.message_id,
                timestamp=time.time(),
                payload=encode_result(type("R", (), {"value": result_value, "success": result_success, "error": None})()),
            )
            await self._send(msg.source_node, reply)
        except Exception as e:
            err = ClusterMessage(
                type=MessageType.ERROR,
                source_node=self._local_node_id,
                target_node=msg.source_node,
                message_id=msg.message_id,
                timestamp=time.time(),
                payload=_encode({"error": str(e)}),
            )
            await self._send(msg.source_node, err)

    async def _handle_remote_result(self, msg: ClusterMessage) -> None:
        """Resolve a pending future with the result from a remote node."""
        future = self._pending.pop(msg.message_id, None)
        if future and not future.done():
            result_data = decode_result(msg.payload)
            if result_data.get("success", True):
                future.set_result(result_data.get("value"))
            else:
                future.set_exception(RuntimeError(result_data.get("error", "remote error")))

    async def _handle_remote_error(self, msg: ClusterMessage) -> None:
        """Handle error from remote node."""
        future = self._pending.pop(msg.message_id, None)
        if future and not future.done():
            from .protocol import _decode
            err_data = _decode(msg.payload)
            future.set_exception(RuntimeError(err_data.get("error", "unknown remote error")))
