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

## How It Works

UDP transport maps IOP levels to channels:
- Channel 0 (Reliable) — card plays, purchases (CRITICAL/STANDARD)
- Channel 1 (Unreliable) — position updates, animations (EPHEMERAL)
- Channel 2 (Chat) — chat messages (STANDARD)

The transport doesn't know your game logic. Your Intent's level determines the channel.

## Dependencies

- `evoid>=0.4.0`
- Optional: `evoid-godot>=1.0.0` (for Godot integration)

## Build Requirements

This plugin has a Rust core (PyO3 + maturin). Pre-built wheels are available on PyPI for Linux/macOS/Windows. If building from source:

- Rust toolchain (`rustup`)
- Python development headers (`python3-dev`)
- `maturin` (`pip install maturin`)

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
