<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-smart-storage?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-smart-storage?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-smart-storage?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-smart-storage</h1>

<p align="center">
  <strong>Multi-DB routing — Intent Handler system</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#intent-handler">Intent Handler</a> •
  <a href="#routing">Routing</a> •
  <a href="#api">API</a>
</p>

---

## Quick Start

```bash
pip install evoid-smart-storage
```

### Method 1: Intent Handler (Recommended)

```python
from evoid_smart_storage import register_handlers
from evoid.core.storage import storage_read, storage_write

# Register Smart Storage as storage handler
register_handlers(config={
    "mapping": {
        "credentials": "postgresql",
        "session": "redis",
        "logs": "memory",
    },
})

# Routes automatically based on data type
await storage_write("cred:db_pass", {"password": "secret"})
await storage_write("session:abc", {"user": "alice"})
```

### Method 2: Direct API

```python
from evoid_smart_storage import SmartStorage

storage = SmartStorage(config={...})
await storage.write("key", {"data": "value"})
```

---

## Intent Handler

evoid-smart-storage registers these Intent handlers:

| Intent | Handler | Description |
|--------|---------|-------------|
| `storage.read` | `handle_read` | Read with smart routing |
| `storage.write` | `handle_write` | Write with smart routing |
| `storage.delete` | `handle_delete` | Delete with smart routing |
| `storage.health` | `handle_health` | Check all backends |

---

## Routing

Smart Storage routes data based on:

1. **Data type** — credentials → PostgreSQL, sessions → Redis
2. **Intent level** — CRITICAL → PostgreSQL, STANDARD → SQLite
3. **User ID** — multi-tenancy support
4. **Metadata override** — explicit backend selection

---

## Configuration

### TOML

```toml
[engines]
storage = "smart_storage"

[engines.options.smart_storage]
mapping = { credentials = "postgresql", session = "redis" }
```

---

## API

### `register_handlers(config: dict)`

Register Smart Storage as Intent handlers.

### SmartStorage Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `read` | `async read(key: str)` | `Any \| None` | Read with routing |
| `write` | `async write(key: str, data: dict)` | `bool` | Write with routing |
| `delete` | `async delete(key: str)` | `bool` | Delete with routing |
| `health` | `async health()` | `bool` | Check all backends |

---

## Dependencies

- `evoid>=0.4.0`
- At least one storage plugin (sqlite, postgresql, redis, etc.)

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
