"""Cluster Protocol — message format for inter-node communication."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

try:
    import msgpack
    def _encode(data: dict) -> bytes:
        return msgpack.packb(data, use_bin_type=True)
    def _decode(data: bytes) -> dict:
        return msgpack.unpackb(data, raw=False)
except ImportError:
    import json
    def _encode(data: dict) -> bytes:
        return json.dumps(data).encode("utf-8")
    def _decode(data: bytes) -> dict:
        return json.loads(data)

_counter = 0


def generate_id() -> str:
    global _counter
    _counter += 1
    return f"msg-{_counter}-{int(time.time() * 1000)}"


class MessageType(str, Enum):
    INTENT = "intent"
    RESULT = "result"
    HEARTBEAT = "heartbeat"
    ANNOUNCE = "announce"
    WITHDRAW = "withdraw"
    ERROR = "error"


@dataclass(frozen=True)
class ClusterMessage:
    type: MessageType
    source_node: str
    target_node: str | None
    message_id: str
    timestamp: float
    payload: bytes

    def encode(self) -> bytes:
        return _encode({
            "type": self.type.value,
            "source_node": self.source_node,
            "target_node": self.target_node,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "payload": list(self.payload),
        })

    @classmethod
    def decode(cls, data: bytes) -> ClusterMessage:
        raw = _decode(data)
        return cls(
            type=MessageType(raw["type"]),
            source_node=raw["source_node"],
            target_node=raw.get("target_node"),
            message_id=raw["message_id"],
            timestamp=raw["timestamp"],
            payload=bytes(raw["payload"]),
        )


def encode_intent(intent: Any) -> bytes:
    return _encode({
        "name": intent.name,
        "level": intent.level.value if hasattr(intent.level, "value") else str(intent.level),
        "metadata": dict(intent.metadata) if hasattr(intent, "metadata") else {},
        "timeout": getattr(intent, "timeout", 10.0),
        "priority": getattr(intent, "priority", 0),
    })


def decode_intent(data: bytes) -> dict:
    return _decode(data)


def encode_result(result: Any) -> bytes:
    return _encode({
        "success": getattr(result, "success", True),
        "value": getattr(result, "value", result),
        "error": str(getattr(result, "error", "")) if getattr(result, "error", None) else None,
    })


def decode_result(data: bytes) -> dict:
    return _decode(data)


def encode_announce(services: list[str], node_name: str, roles: list[str]) -> bytes:
    return _encode({
        "services": services,
        "node_name": node_name,
        "roles": roles,
    })


def make_message(
    msg_type: MessageType,
    source: str,
    target: str | None,
    payload_data: dict | bytes | None = None,
) -> ClusterMessage:
    if isinstance(payload_data, dict):
        payload = _encode(payload_data)
    elif isinstance(payload_data, bytes):
        payload = payload_data
    else:
        payload = b""
    return ClusterMessage(
        type=msg_type,
        source_node=source,
        target_node=target,
        message_id=generate_id(),
        timestamp=time.time(),
        payload=payload,
    )
