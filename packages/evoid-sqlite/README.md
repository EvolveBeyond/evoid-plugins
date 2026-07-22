<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-sqlite?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-sqlite?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-sqlite?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-sqlite</h1>

<p align="center">
  <strong>SQLite storage engine for EVOID — Intent Handler system</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#intent-handler">Intent Handler</a> •
  <a href="#configuration">Config</a> •
  <a href="#api">API</a>
</p>

---

## Quick Start

```bash
uv add evoid-sqlite
```

### Method 1: Intent Handler (Recommended)

```python
from evoid_sqlite import register_handlers
from evoid.core.storage import storage_read, storage_write, storage_delete

# Register SQLite as storage handler
register_handlers(db_path="my_app.db")

# Use high-level API — goes through Intent pipeline
await storage_write("user:1", {"name": "Alice", "role": "admin"})
user = await storage_read("user:1")
await storage_delete("user:1")
```

### Method 2: Direct API

```python
from evoid_sqlite import create_storage

storage = create_storage("my_app.db")
await storage.write("user:1", {"name": "Alice"})
user = await storage.read("user:1")
```

---

## Intent Handler

evoid-sqlite registers these Intent handlers:

| Intent | Handler | Description |
|--------|---------|-------------|
| `storage.read` | `handle_read` | Read from SQLite |
| `storage.write` | `handle_write` | Write to SQLite |
| `storage.delete` | `handle_delete` | Delete from SQLite |
| `storage.health` | `handle_health` | Check connection |

### How it works

1. `register_handlers()` registers Intent handlers for storage operations
2. `storage_read()` / `storage_write()` create Intents and execute through pipeline
3. Pipeline routes to SQLite handler
4. Handler connects to SQLite and performs operation

---

## Configuration

### TOML

```toml
[engines]
storage = "sqlite"

[engines.options.sqlite]
db_path = "data/my_app.db"
```

### Python

```python
from evoid.config import config

app = config(
    engines={
        "storage": "sqlite",
        "options": {
            "sqlite": {"db_path": "data/production.db"},
        },
    },
)
```

---

## API

### `register_handlers(db_path: str)`

Register SQLite as Intent handlers.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_path` | `str` | `evoid.db` | Path to SQLite database file |

### `create_storage(db_path: str) -> SQLiteStorage`

Factory function for direct API access.

### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `read` | `async read(key: str)` | `Any \| None` | Read value by key |
| `write` | `async write(key: str, data: dict)` | `bool` | Write value (JSON serialized) |
| `delete` | `async delete(key: str)` | `bool` | Delete by key |
| `health` | `async health()` | `bool` | Check connection |
| `list_keys` | `async list_keys(namespace: str)` | `list[str]` | List all keys |

---

## Dependencies

- `evoid>=0.4.3`
- `evoid-di>=0.1.0`
- `aiosqlite>=0.20.0`

## DI Integration

Registers as `storage.sqlite` in evoid-di:

```python
from evoid_di import di

# Auto-registered when you call register_handlers()
di.register("storage.sqlite", lambda: SQLiteStorage("app.db"))

# Resolve with fallback
storage = di.resolve_with_fallback("storage.postgresql")
# Falls back to storage.sqlite if postgresql fails
```

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
