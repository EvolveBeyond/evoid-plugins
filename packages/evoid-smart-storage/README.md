<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-smart-storage?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-smart-storage?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-smart-storage?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-smart-storage</h1>

<p align="center">
  <strong>Multi-DB routing, schema enforcement, and multi-tenancy for EVOID</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#routing">Routing</a> •
  <a href="#api">API</a> •
  <a href="#installation">Install</a> •
  <a href="https://evolvebeyond.github.io/EVOID/">Docs</a>
</p>

---

## Quick Start

```bash
pip install evoid-smart-storage
```

Smart Storage routes data to different backends based on type, level, or user. It doesn't store data itself — it delegates to your installed storage plugins.

```python
from evoid_smart_storage import SmartStorage

# Configure routing
storage = SmartStorage(config={
    "mapping": {
        "credentials": "postgresql",
        "session": "redis",
        "logs": "memory",
    },
    "level_routing": {
        "CRITICAL": "postgresql",
        "STANDARD": "sqlite",
    },
})

# Write — routes to postgresql (because data_type="credentials")
await storage.write("credentials", {"email": "alice@example.com"})

# Write — routes to redis (because data_type="session")
await storage.write("session", {"token": "abc123"})
```

## Configuration

### TOML

```toml
[engines]
storage = "smart_storage"

[engines.smart_storage.mapping]
credentials = "postgresql"
session = "redis"
logs = "memory"

[engines.smart_storage.level_routing]
CRITICAL = "postgresql"
STANDARD = "sqlite"
EPHEMERAL = "memory"

[engines.smart_storage.schemas]
credentials = ["email", "password_hash", "role"]
```

### Python

```python
from evoid_smart_storage import SmartStorage

storage = SmartStorage(config={
    "mapping": {
        "credentials": "postgresql",
        "session": "redis",
    },
    "schemas": {
        "credentials": ["email", "password_hash"],
    },
    "level_routing": {
        "CRITICAL": "postgresql",
    },
    "user_connections": {
        "user_123": "scylla",
    },
})
```

## Routing Priority

Smart Storage checks in this order:

1. **Explicit override** — `intent.metadata["storage_preference"]`
2. **User routing** — `user_connections[user_id]` (multi-tenancy)
3. **Level routing** — `level_routing[intent.level]` (e.g., CRITICAL → PostgreSQL)
4. **Type mapping** — `mapping[data_type]` (default fallback)

## Schema Enforcement

Define allowed fields per data type:

```python
storage = SmartStorage(config={
    "mapping": {"credentials": "postgresql"},
    "schemas": {
        "credentials": ["email", "password_hash"],  # Only these fields allowed
    },
})

# Extra fields are stripped automatically
await storage.write("credentials", {
    "email": "alice@example.com",
    "password_hash": "...",
    "debug_field": "removed",  # This gets stripped
})
```

## Multi-Write

Route to multiple backends at once:

```python
# In metadata, set storage_preference to "memory+redis"
await storage.write("logs", {"event": "login"}, metadata={
    "storage_preference": "memory+redis",
})
```

## API

### `SmartStorage(config: dict)`

| Config Key | Type | Description |
|------------|------|-------------|
| `mapping` | `dict[str, str]` | Data type → backend name |
| `schemas` | `dict[str, list[str]]` | Allowed fields per type |
| `level_routing` | `dict[str, str]` | Intent level → backend |
| `user_connections` | `dict[str, str]` | User ID → backend (multi-tenancy) |

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `write` | `async write(data_type, data, intent=None, user_id=None)` | Route and write |
| `read` | `async read(data_type, query, intent=None, user_id=None)` | Read from primary backend |
| `delete` | `async delete(data_type, query, intent=None, user_id=None)` | Delete from all targets |
| `health` | `async health()` | Check all backends |

## Dependencies

- `evoid>=0.4.0`
- At least one storage plugin (e.g., `evoid-sqlite`, `evoid-redis`, `evoid-postgresql`)

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
