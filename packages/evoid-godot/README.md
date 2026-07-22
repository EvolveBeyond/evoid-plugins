<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-godot?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-godot?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-godot?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-godot</h1>

<p align="center">
  <strong>Godot game integration — Intent Handler system</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#intent-handler">Intent Handler</a> •
  <a href="#features">Features</a> •
  <a href="#api">API</a>
</p>

---

## Quick Start

```bash
uv add evoid-godot
```

### Method 1: Intent Handler (Recommended)

```python
from evoid_godot import register_handlers

# Register Godot adapter as Intent handlers
register_handlers()
```

### Method 2: Direct API

```python
from evoid_godot import create_game_handler

handler = create_game_handler()
```

---

## Intent Handler

evoid-godot registers game-related Intents for Godot integration.

---

## Features

- WebSocket connection to Godot games
- Topic-based pub/sub system
- Game hosting with splash screen config
- Multiplayer support

---

## Configuration

### TOML

```toml
[engines]
godot = "godot"
```

---

## API

### `register_handlers()`

Register Godot adapter as Intent handlers.

### GameHost Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `register_build` | `register_build(game_id, build_dir, title, splash)` | Register a game build |
| `start` | `async start(game_id)` | Start hosting game |

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

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Godot Plugin](https://github.com/EvolveBeyond/evolvebeyond-evoid-godot)
- [Documentation](https://evolvebeyond.github.io/EVOID/)

## License

MIT
