<p align="center">
  <img src="https://img.shields.io/badge/rust-orange?style=for-the-badge&logo=rust&logoColor=white" alt="Rust">
  <img src="https://img.shields.io/pypi/v/evoid-transport?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-transport?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-transport?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-transport</h1>

<p align="center">
  <strong>Low-latency UDP transport — Intent Handler system</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#intent-handler">Intent Handler</a> •
  <a href="#channels">Channels</a> •
  <a href="#api">API</a>
</p>

---

## Quick Start

```bash
uv add evoid-transport
```

### Method 1: Intent Handler (Recommended)

```python
from evoid_transport import register_handlers

# Register UDP transport as Intent handlers
register_handlers(host="0.0.0.0", port=9000)
```

### Method 2: Direct API

```python
from evoid_transport import EvoidUDPPort

transport = EvoidUDPPort(host="0.0.0.0", port=9000)
await transport.start(game_id="my_game")
```

---

## Intent Handler

evoid-transport registers UDP packet handling as Intent handlers.

---

## Performance

```
WebSocket (TCP):  ~2-5ms overhead
evoid-transport:  ~0.5-1ms overhead
ENet:             ~0.3-0.5ms overhead
```

---

## Channels

| Channel | Use Case | Reliability | Ordering |
|---------|----------|-------------|----------|
| 0 | Card plays, game actions | Reliable | Ordered |
| 1 | Position, animations | Unreliable | Unordered |
| 2 | Chat messages | Reliable | Unordered |

---

## Configuration

### TOML

```toml
[engines]
transport = "transport"

[engines.options.transport]
host = "0.0.0.0"
port = 9000
```

---

## API

### `register_handlers(host, port)`

Register UDP transport as Intent handlers.

### EvoidUDPPort Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `start` | `async start(game_id)` | Start UDP server |
| `stop` | `async stop()` | Stop UDP server |
| `broadcast_state_sync` | `async broadcast_state_sync(state, tick)` | Broadcast game state |
| `send_intent_to_client` | `async send_intent_to_client(addr, name, data)` | Send to specific client |

---

## DI Integration

All plugins register with evoid-di for automatic service discovery and fault tolerance.

```python
from evoid_di import di

# Resolve with fallback
storage = di.resolve_with_fallback("storage.postgresql")
# Tries: postgresql → sqlite → redis → cluster peers → None
```

## Dependencies

- `evoid>=0.4.0`
- Optional: `evoid-godot>=1.0.0` (for Godot integration)

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
