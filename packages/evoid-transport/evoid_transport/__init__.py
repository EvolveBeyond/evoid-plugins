"""EVOID Transport — low-latency UDP transport layer.

Replaces WebSocket with binary UDP for ENet-level performance.
Compatible with evoid-godot pub/sub topics.
"""

from __future__ import annotations

import asyncio
import json
import socket
import struct
import time
from dataclasses import dataclass, field
from typing import Any, Callable

try:
    from evoid_transport.evoid_transport_rust import EvoidTransport as _RustTransport
    EvoidTransport = _RustTransport
    HAS_RUST = True
except ImportError:
    HAS_RUST = False

try:
    from evoid import Intent, Level, publish, subscribe
    HAS_EVOID = True
except ImportError:
    HAS_EVOID = False

try:
    from evoid_godot.topics import Topics
    HAS_GODOT_TOPICS = True
except ImportError:
    HAS_GODOT_TOPICS = False


# ── Protocol Constants ──────────────────────────────────────────────────────

MAGIC = b"EVOI"
PROTOCOL_VERSION = 1
HEADER_SIZE = 18  # 4(magic) + 1(version) + 1(type) + 4(seq) + 4(ack) + 4(ack_bits)

# Packet types — must match codec.rs
PKT_INTENT = 0x01
PKT_STATE_SYNC = 0x02
PKT_ACK = 0x03
PKT_CONNECTED = 0x04
PKT_PING = 0x05
PKT_PONG = 0x06
PKT_PLAYER_JOINED = 0x07
PKT_PLAYER_LEFT = 0x08

# Channel separation
CH_RELIABLE = 0    # Card plays, game actions — must arrive
CH_UNRELIABLE = 1  # Position, animations — can skip
CH_CHAT = 2        # Chat messages — reliable but unordered


# ── Packet Builder (pure Python, no Rust dependency) ────────────────────────

def build_header(
    packet_type: int,
    sequence: int,
    ack: int = 0,
    ack_bitfield: int = 0,
) -> bytes:
    return struct.pack(
        ">4sBBIII",
        MAGIC,
        PROTOCOL_VERSION,
        packet_type,
        sequence & 0xFFFFFFFF,
        ack & 0xFFFFFFFF,
        ack_bitfield & 0xFFFFFFFF,
    )


def parse_header(data: bytes) -> dict | None:
    if len(data) < HEADER_SIZE:
        return None
    magic, version, ptype, seq, ack, ack_bits = struct.unpack_from(">4sBBIII", data)
    if magic != MAGIC or version != PROTOCOL_VERSION:
        return None
    return {
        "type": ptype,
        "sequence": seq,
        "ack": ack,
        "ack_bitfield": ack_bits,
    }


def build_intent_packet(
    intent_name: str,
    metadata: dict,
    priority: int = 50,
    sequence: int = 0,
    ack: int = 0,
    ack_bitfield: int = 0,
) -> bytes:
    header = build_header(PKT_INTENT, sequence, ack, ack_bitfield)
    payload = _pack({
        "name": intent_name,
        "metadata": metadata,
        "priority": priority,
        "timestamp": int(time.time() * 1000),
    })
    return header + struct.pack(">I", len(payload)) + payload


def parse_intent_packet(data: bytes) -> dict | None:
    header = parse_header(data)
    if not header or header["type"] != PKT_INTENT:
        return None
    if len(data) < HEADER_SIZE + 4:
        return None
    payload_len = struct.unpack_from(">I", data, HEADER_SIZE)[0]
    if len(data) < HEADER_SIZE + 4 + payload_len:
        return None
    payload = _unpack(data[HEADER_SIZE + 4 : HEADER_SIZE + 4 + payload_len])
    payload["_header"] = header
    return payload


def build_state_sync_packet(
    game_id: str,
    state: dict,
    tick: int = 0,
    sequence: int = 0,
    ack: int = 0,
    ack_bitfield: int = 0,
) -> bytes:
    header = build_header(PKT_STATE_SYNC, sequence, ack, ack_bitfield)
    payload = _pack({
        "game_id": game_id,
        "state": state,
        "tick": tick,
    })
    return header + struct.pack(">I", len(payload)) + payload


def parse_state_sync_packet(data: bytes) -> dict | None:
    header = parse_header(data)
    if not header or header["type"] != PKT_STATE_SYNC:
        return None
    if len(data) < HEADER_SIZE + 4:
        return None
    payload_len = struct.unpack_from(">I", data, HEADER_SIZE)[0]
    if len(data) < HEADER_SIZE + 4 + payload_len:
        return None
    payload = _unpack(data[HEADER_SIZE + 4 : HEADER_SIZE + 4 + payload_len])
    payload["_header"] = header
    return payload


def build_ack_packet(ack: int, ack_bitfield: int, sequence: int = 0) -> bytes:
    return build_header(PKT_ACK, sequence, ack, ack_bitfield)


def build_ping_packet(sequence: int = 0, ack: int = 0, ack_bitfield: int = 0) -> bytes:
    header = build_header(PKT_PING, sequence, ack, ack_bitfield)
    send_time = int(time.time() * 1000)
    return header + struct.pack(">Q", send_time)


def build_pong_packet(send_time: int, sequence: int = 0, ack: int = 0, ack_bitfield: int = 0) -> bytes:
    header = build_header(PKT_PONG, sequence, ack, ack_bitfield)
    return header + struct.pack(">Q", send_time)


# ── ACK Tracker ─────────────────────────────────────────────────────────────

@dataclass
class ACKTracker:
    """Tracks packet sequencing and ACK bitfield for reliable delivery."""

    local_sequence: int = 0
    remote_sequence: int = 0
    ack_bitfield: int = 0

    def next_sequence(self) -> int:
        seq = self.local_sequence
        self.local_sequence = (self.local_sequence + 1) & 0xFFFFFFFF
        return seq

    def update_remote(self, remote_seq: int) -> None:
        delta = (remote_seq - self.remote_sequence) & 0xFFFFFFFF
        if delta == 0 or delta > 0x7FFFFFFF:
            return
        self.ack_bitfield = (self.ack_bitfield << delta) | 1
        self.remote_sequence = remote_seq

    @property
    def last_ack(self) -> int:
        return self.remote_sequence


# ── UDP Server (Python fallback when Rust is unavailable) ───────────────────

class UDPServer:
    """Pure Python UDP server — fallback when Rust extension isn't built."""

    def __init__(self, host: str = "0.0.0.0", port: int = 9000, tick_rate: int = 60):
        self.host = host
        self.port = port
        self.tick_rate = tick_rate
        self.sock: socket.socket | None = None
        self.running = False
        self.clients: dict[str, dict] = {}  # addr_str -> {client_id, tracker, name}
        self.next_client_id = 2
        self._handlers: dict[int, Callable] = {}

    async def start(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.sock.bind((self.host, self.port))
        self.running = True

    async def stop(self) -> None:
        self.running = False
        if self.sock:
            self.sock.close()
            self.sock = None

    async def receive_loop(self) -> None:
        loop = asyncio.get_running_loop()
        while self.running:
            try:
                data, addr = await loop.sock_recvfrom(self.sock, 4096)
                addr_str = f"{addr[0]}:{addr[1]}"
                self._handle_packet(data, addr_str, addr)
            except BlockingIOError:
                await asyncio.sleep(0.001)
            except Exception:
                await asyncio.sleep(0.01)

    def _handle_packet(self, data: bytes, addr_str: str, addr: tuple) -> None:
        header = parse_header(data)
        if not header:
            return

        # Update ACK tracking
        if addr_str in self.clients:
            self.clients[addr_str]["tracker"].update_remote(header["sequence"])

        ptype = header["type"]
        if ptype == PKT_INTENT:
            packet = parse_intent_packet(data)
            if packet:
                self._on_intent(addr_str, packet)
        elif ptype == PKT_PING:
            payload = data[HEADER_SIZE:]
            if len(payload) >= 8:
                send_time = struct.unpack_from(">Q", payload, 0)[0]
                self._send_pong(addr, send_time, addr_str)

    def _on_intent(self, addr_str: str, packet: dict) -> None:
        """Override this to handle intents via pub/sub."""
        pass

    def _send_pong(self, addr: tuple, send_time: int, addr_str: str) -> None:
        if addr_str not in self.clients:
            return
        tracker = self.clients[addr_str]["tracker"]
        seq = tracker.next_sequence()
        pong = build_pong_packet(send_time, seq, tracker.last_ack, tracker.ack_bitfield)
        if self.sock:
            self.sock.sendto(pong, addr)

    def send_to_all(self, data: bytes) -> None:
        if not self.sock:
            return
        for addr_str, client in self.clients.items():
            addr = client.get("addr")
            if not addr:
                # fallback: parse from string
                parts = addr_str.split(":")
                addr = (parts[0], int(parts[1]))
            try:
                self.sock.sendto(data, addr)
            except Exception:
                pass

    def send_to(self, addr_str: str, data: bytes) -> None:
        if not self.sock or addr_str not in self.clients:
            return
        client = self.clients[addr_str]
        addr = client.get("addr")
        if not addr:
            parts = addr_str.split(":")
            addr = (parts[0], int(parts[1]))
        try:
            self.sock.sendto(data, addr)
        except Exception:
            pass

    def register_client(self, addr_str: str, player_name: str = "", addr_tuple: tuple = None) -> int:
        client_id = self.next_client_id
        self.next_client_id += 1
        self.clients[addr_str] = {
            "client_id": client_id,
            "player_name": player_name,
            "tracker": ACKTracker(),
            "addr": addr_tuple,  # store tuple to avoid re-parsing
        }
        return client_id

    def remove_client(self, addr_str: str) -> tuple[int, str] | None:
        client = self.clients.pop(addr_str, None)
        if client:
            return (client["client_id"], client["player_name"])
        return None


# ── EvoidUDPPort (Integration with evoid pub/sub) ──────────────────────────

class EvoidUDPPort:
    """UDP transport integrated with evoid message bus and Godot pub/sub topics.

    Bridges UDP packets to evoid intents and publishes events using
    the same Topics as evoid-godot.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 9000, tick_rate: int = 60):
        if HAS_RUST:
            self._rust = _RustTransport(host, port, tick_rate)
            self.server = None  # Rust handles transport
        else:
            self._rust = None
            self.server = UDPServer(host, port, tick_rate)
        self.game_id = ""
        self._latency_cache: dict[str, int] = {}
        self._publish_semaphore = asyncio.Semaphore(50)  # cap concurrent publish tasks
        self._tracked_tasks: set = set()

    async def start(self, game_id: str = "default") -> None:
        self.game_id = game_id
        if self.server:
            await self.server.start()
            self.server._on_intent = self._handle_udp_intent

    async def stop(self) -> None:
        if self.server:
            await self.server.stop()
        self._latency_cache.clear()

    async def receive_loop(self) -> None:
        if self.server:
            await self.server.receive_loop()

    def _handle_udp_intent(self, addr_str: str, packet: dict) -> None:
        """Convert UDP intent to evoid intent and publish to message bus."""
        intent_name = packet.get("name", "")
        metadata = packet.get("metadata", {})
        priority = packet.get("priority", 50)

        task = asyncio.ensure_future(self._publish_intent(
            intent_name, metadata, priority, addr_str
        ))
        self._tracked_tasks.add(task)
        task.add_done_callback(self._tracked_tasks.discard)

    async def _publish_intent(
        self,
        intent_name: str,
        metadata: dict,
        priority: int,
        addr_str: str,
    ) -> None:
        async with self._publish_semaphore:
            client = self.server.clients.get(addr_str) if self.server else None
            player_id = str(client["client_id"]) if client else "unknown"

            await publish(
                Intent(
                    name=f"game:{self.game_id}:{intent_name}",
                    level=Level.STANDARD,
                    metadata={
                        **metadata,
                        "player_id": player_id,
                        "game_id": self.game_id,
                        "source": "udp_transport",
                        "transport": "udp",
                    },
                ),
                source=f"udp:{player_id}",
            )

    async def broadcast_state_sync(self, state: dict, tick: int = 0) -> None:
        """Broadcast state sync to all connected clients.

        Serializes state payload ONCE, then stamps per-client headers.
        Sends are non-blocking via loop.sock_sendto.
        """
        if not self.server or not self.server.sock:
            return

        # Serialize state once for all clients
        payload = _pack({"game_id": self.game_id, "state": state, "tick": tick})
        payload_bytes = struct.pack(">I", len(payload)) + payload

        loop = asyncio.get_running_loop()
        tasks = []
        for addr_str, client in self.server.clients.items():
            tracker = client["tracker"]
            seq = tracker.next_sequence()
            header = build_header(PKT_STATE_SYNC, seq, tracker.last_ack, tracker.ack_bitfield)
            packet = header + payload_bytes

            addr = client.get("addr")
            if not addr:
                parts = addr_str.split(":")
                addr = (parts[0], int(parts[1]))

            tasks.append(loop.sock_sendto(self.server.sock, packet, addr))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def send_intent_to_client(self, addr_str: str, intent_name: str, data: dict) -> None:
        if not self.server:
            return
        client = self.server.clients.get(addr_str)
        if not client:
            return
        tracker = client["tracker"]
        seq = tracker.next_sequence()
        packet = build_intent_packet(intent_name, data, 50, seq, tracker.last_ack, tracker.ack_bitfield)

        addr = client.get("addr")
        if addr and self.server.sock:
            loop = asyncio.get_running_loop()
            await loop.sock_sendto(self.server.sock, packet, addr)

    def remove_client(self, addr_str: str) -> None:
        """Remove client and clean up latency cache."""
        if self.server:
            self.server.remove_client(addr_str)
        self._latency_cache.pop(addr_str, None)

    def get_latency(self, addr_str: str) -> int | None:
        return self._latency_cache.get(addr_str)

    def measure_latency(self, addr_str: str) -> bytes:
        if not self.server:
            return b""
        client = self.server.clients.get(addr_str)
        if not client:
            return b""
        tracker = client["tracker"]
        seq = tracker.next_sequence()
        return build_ping_packet(seq, tracker.last_ack, tracker.ack_bitfield)


# ── Fast serialization (msgpack > orjson > json) ───────────────────────────

try:
    import msgpack as _msgpack
    _pack = _msgpack.packb
    _unpack = _msgpack.unpackb
    _SERIALIZE = "msgpack"
except ImportError:
    try:
        import orjson as _orjson
        def _pack(obj: dict) -> bytes:
            return _orjson.dumps(obj)
        def _unpack(data: bytes) -> dict:
            return _orjson.loads(data)
        _SERIALIZE = "orjson"
    except ImportError:
        import json as _json
        def _pack(obj: dict) -> bytes:
            return _json.dumps(obj).encode("utf-8")
        def _unpack(data: bytes) -> dict:
            return _json.loads(data)
        _SERIALIZE = "json"

MANIFEST = {
    "name": "evoid-transport",
    "version": "0.1.0",
    "type": "engine",
    "description": "Low-latency UDP transport for EVOID",
    "entry_point": "evoid_transport:register_plugin",
    "dependencies": ["evoid>=0.4.0"],
    "evoid_version": ">=0.4.0",
    "tags": ["transport", "udp", "low-latency"],
}


def register_plugin():
    """Register evoid-transport with the evoid plugin registry."""
    try:
        from evoid.engines.plugin import register
        register(
            name="transport",
            type="engine",
            factory=EvoidUDPPort if HAS_EVOID else None,
            version="0.1.0",
            description="Low-latency UDP transport layer",
        )
    except ImportError:
        pass
