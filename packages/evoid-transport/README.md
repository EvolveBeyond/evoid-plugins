<p align="center">
  <img src="https://img.shields.io/badge/rust-orange?style=for-the-badge&logo=rust&logoColor=white" alt="Rust">
  <img src="https://img.shields.io/pypi/v/evoid-transport?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-transport?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-transport?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-transport</h1>

<p align="center">
  <strong>Low-latency UDP transport for EVOID — ENet-level performance</strong>
</p>

---

## What is it?

Replaces WebSocket (TCP) with raw UDP for game state synchronization. Binary protocol with optional reliability per packet type.

```
WebSocket (TCP):  ~2-5ms overhead
evoid-transport:  ~0.5-1ms overhead
ENet:             ~0.3-0.5ms overhead
```

## Channels

| Channel | Use Case | Reliability | Ordering |
|---------|----------|-------------|----------|
| 0 | Card plays, game actions | Reliable | Ordered |
| 1 | Position, animations | Unreliable | Sequenced |
| 2 | Chat messages | Reliable | Unordered |

## Architecture

```
Godot Client (EvoidUDP)
  │
  ├─ Reliable channel ──▶ Card plays, game actions
  ├─ Unreliable channel ──▶ Position updates
  └─ Chat channel ──▶ Chat messages
  │
  ▼
UDP (binary protocol)
  │
  ▼
evoid-transport (Rust/Python)
  │
  ▼
evoid Message Bus
  │
  ▼
evoid-godot handlers (same as WebSocket)
```

## Quick Start

### Server (Python)

```python
from evoid_transport import EvoidUDPPort

transport = EvoidUDPPort(host="0.0.0.0", port=9000)
await transport.start(game_id="card-game")

# Broadcast state to all clients
await transport.broadcast_state_sync({"cards": [...]}, tick=1)
```

### Client (GDScript)

```gdscript
func _ready():
    # Use UDP instead of WebSocket
    EvoidUDP.connect_to_server("127.0.0.1", 9000, "Player1")
    EvoidUDP.packet_received.connect(_on_packet)

func play_card(card_id: String):
    # Reliable delivery — card play must arrive
    EvoidUDP.send_intent("card_played", {"card": card_id})

func update_position(pos: Vector2):
    # Unreliable — position can skip frames
    EvoidUDP.send_intent_unreliable("player_move", {"x": pos.x, "y": pos.y})
```

## Packet Format

```
Offset  Size   Field
0       4      Magic ("EVOI")
4       1      Protocol version
5       1      Packet type
6       4      Sequence number
10      4      Last received sequence (ACK)
14      4      ACK bitfield
16      4      Payload length
20      N      Payload (JSON or binary)
```

## Latency Measurement

```gdscript
# Automatic ping/pong every 1 second
EvoidUDP.latency_updated.connect(_on_latency)

func _on_latency(ms: int):
    $Label.text = "Ping: %dms" % ms
```

## Installation

### Python

```bash
pip install evoid-transport
```

### With Rust extension (optional, faster)

```bash
pip install evoid-transport[rust]
```

### Godot

Copy `evoid_godot/` to your project's `addons/` folder. Enable in Project Settings.

## Comparison

| Feature | WebSocket | evoid-transport | ENet |
|---------|-----------|-----------------|------|
| Protocol | TCP | UDP | UDP |
| Overhead | ~3ms | ~0.8ms | ~0.5ms |
| Reliability | Always | Optional | Optional |
| Web support | Yes | Fallback WS | No |
| Binary | JSON | bincode/JSON | Custom |
| Max players | 1000+ | 256+ | 50 |

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)

## License

MIT
