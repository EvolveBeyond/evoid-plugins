<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-godot?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-godot?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-godot?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-godot</h1>

<p align="center">
  <strong>Godot game integration adapter for EVOID</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#api">API</a> •
  <a href="https://evolvebeyond.github.io/EVOID/">Docs</a>
</p>

---

## What is this?

This is the **Python/EVOID side** of the Godot integration. It works together with the [Godot plugin](https://github.com/EvolveBeyond/evolvebeyond-evoid-godot) to connect Godot games to EVOID server.

## Quick Start

```bash
pip install evoid-godot
```

### 1. Register the plugin

```python
# In your EVOID service
from evoid_godot import register_plugin
register_plugin()
```

### 2. Setup game subscriptions

```python
from evoid_godot import setup_game_subscriptions

# Setup for a specific game
setup_game_subscriptions("my-game")
```

### 3. Handle game intents

```python
from evoid import subscribe
from evoid_godot import Topics

# Subscribe to game events
async def on_game_event(intent):
    event_type = intent.metadata.get("type")
    if event_type == "player_moved":
        print(f"Player moved: {intent.metadata}")

subscribe(Topics.GAME_EVENT, on_game_event)
```

---

## Features

### Mirrors Godot Plugin Topics

Same topic names as the Godot plugin:

```python
from evoid_godot import Topics

# Same as EvoidTopics in Godot
Topics.GAME_EVENT          # "evoid/game/event"
Topics.GAME_STATE_SYNC     # "evoid/game/state_sync"
Topics.GAME_PLAYER_JOINED  # "evoid/game/player_joined"
Topics.GAME_PLAYER_LEFT    # "evoid/game/player_left"
```

### Intent-based Game Events

Game events are Intents — they go through EVOID's pipeline:

```python
from evoid import Intent, Level

# Game event as Intent
intent = Intent(
    name="game:my-game:player_shot",
    level=Level.STANDARD,
    metadata={
        "player_id": "123",
        "origin": [0, 0],
        "direction": [1, 0],
    }
)
```

### Message Bus Integration

Uses EVOID's message bus for zero-latency communication:

```python
from evoid import publish

# Broadcast to all players (0ms — in-memory)
await publish(intent)
```

---

## API

### `Topics`

Topic constants matching the Godot plugin:

| Topic | Value | Description |
|-------|-------|-------------|
| `GAME_EVENT` | `evoid/game/event` | Game event |
| `GAME_STATE_SYNC` | `evoid/game/state_sync` | State sync |
| `GAME_PLAYER_JOINED` | `evoid/game/player_joined` | Player joined |
| `GAME_PLAYER_LEFT` | `evoid/game/player_left` | Player left |

### `setup_game_subscriptions(game_id)`

Setup default handlers for a game:

```python
from evoid_godot import setup_game_subscriptions

setup_game_subscriptions("my-game")
```

### `game_intent_handler(intent)`

Default handler for game intents:

```python
from evoid_godot import game_intent_handler

# Register as handler
subscribe("game:*", game_intent_handler)
```

---

## How It Works

```
Godot Game
    ↓ (WebSocket)
EVOID Server
    ↓
evoid-godot adapter
    ↓
Message Bus (0ms)
    ↓
┌──────────────────────┐
│ Your game handlers   │
│ State sync           │
│ Analytics            │
└──────────────────────┘
```

---

## With Godot Plugin

This plugin works together with the Godot plugin:

1. **Godot plugin** (`evoid_godot/`) — runs in Godot, handles client-side
2. **EVOID plugin** (`evoid-godot`) — runs on server, handles server-side

### Godot Side

```gdscript
# In Godot
EvoidApp.connect_to_server("wss://your-server.com", "my-game")
EvoidApp.send_intent("player_move", {"x": 10, "y": 20})
```

### EVOID Side

```python
# In EVOID server
from evoid_godot import setup_game_subscriptions
setup_game_subscriptions("my-game")

# Handle events
async def on_move(intent):
    # Process movement
    pass
```

---

## Example: Complete Setup

```python
from evoid import Intent, Level, subscribe, publish
from evoid_godot import Topics, setup_game_subscriptions

# Setup game
setup_game_subscriptions("my-game")

# Custom handler for shots
async def handle_shot(intent):
    player_id = intent.metadata.get("player_id")
    origin = intent.metadata.get("origin")
    direction = intent.metadata.get("direction")
    
    # Process shot (raycast, damage, etc.)
    hit = process_shot(origin, direction)
    
    # Broadcast result
    await publish(Intent(
        name=Topics.GAME_EVENT,
        level=Level.STANDARD,
        metadata={"type": "shot_result", "hit": hit}
    ))

subscribe("game:my-game:player_shot", handle_shot)
```

---

## Web Hosting (Instant Game Loading)

Serve Godot WebGL exports with zero perceived load time. Users see a splash screen instantly, the game streams in the background, and repeat visits are instant via Service Worker.

### Quick Start

```python
from evoid_godot import GameHost

host = GameHost()
host.register_build("my-game", "builds/my-game/", title="My Game")

from starlette.routing import Mount
app = Starlette(routes=[Mount("/game", app=host.create_router())])
```

Open `/game/my-game/` — splash appears instantly, game loads in background.

### Multi-Game

```python
from evoid_godot import GameHost, SplashConfig

host = GameHost()

# Game 1 — default splash
host.register_build("tank-battle", "builds/tank-battle/", title="Tank Battle")

# Game 2 — custom splash
host.register_build(
    "card-arena", "builds/card-arena/", title="Card Arena",
    splash=SplashConfig(
        bg_color="#0d1117",
        accent_color="#58a6ff",
        subtitle="Multiplayer Card Game",
    ),
)

# /game/tank-battle/ and /game/card-arena/ — both instant
```

### Custom Splash

```python
from evoid_godot import SplashConfig

splash = SplashConfig(
    bg_color="#0d1117",       # dark background
    text_color="#ffffff",      # white text
    accent_color="#58a6ff",   # blue progress bar
    logo_url="/logo.png",     # optional logo
    title="My Game",
    subtitle="Loading...",
)
host.register_build("my-game", "builds/my-game/", splash=splash)
```

### One-Liner

```python
from evoid_godot import setup_game_hosting

host = setup_game_hosting("my-game", "builds/my-game/", title="My Game")
```

### Godot Side (WebGL)

```gdscript
func _ready():
    # Auto-detect WebGL, connect to same-origin server
    EvoidApp.connect_to_server_auto()

    # Or explicit:
    # EvoidApp.connect_to_server("wss://server.com", "my-game")
```

### How It Works

```
User visits /game/{id}/
  → HTML splash (<100ms, inline CSS)
  → Service Worker registers
  → engine.wasm streams in background
  → game.pck loads in 256KB chunks
  → Game starts, splash fades
  → Repeat: instant (SW cache)
```

### Routes

| Route | Description |
|-------|-------------|
| `GET /` | Splash HTML (inline, instant) |
| `GET /engine.wasm` | Godot engine (cached forever) |
| `GET /game.pck` | Game data (or `?chunk=N&size=256K`) |
| `GET /chunk/{n}` | PCK chunk for progressive load |
| `GET /manifest.json` | Build manifest |
| `GET /sw.js` | Generated Service Worker |
| `GET /assets/*` | Static game assets |

---

## Dependencies

- `evoid>=0.4.0` (required)

## Links

- [Godot Plugin](https://github.com/EvolveBeyond/evolvebeyond-evoid-godot)
- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)

## License

MIT
