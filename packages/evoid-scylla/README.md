<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-scylla?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-scylla?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-scylla?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-scylla</h1>

<p align="center">
  <strong>ScyllaDB/Cassandra storage engine — Intent Handler system</strong>
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
uv add evoid-scylla
```

### Method 1: Intent Handler (Recommended)

```python
from evoid_scylla import register_handlers
from evoid.core.storage import storage_read, storage_write, storage_delete

# Register ScyllaDB as storage handler
register_handlers(
    contact_points=["127.0.0.1"],
    port=9042,
    keyspace="evoid",
)

# Use high-level API
await storage_write("user:1", {"name": "Alice"})
user = await storage_read("user:1")
await storage_delete("user:1")
```

### Method 2: Direct API

```python
from evoid_scylla import create_storage

storage = create_storage(contact_points=["127.0.0.1"], port=9042)
await storage.write("user:1", {"name": "Alice"})
user = await storage.read("user:1")
```

---

## Intent Handler

evoid-scylla registers these Intent handlers:

| Intent | Handler | Description |
|--------|---------|-------------|
| `storage.read` | `handle_read` | Read from ScyllaDB |
| `storage.write` | `handle_write` | Write to ScyllaDB |
| `storage.delete` | `handle_delete` | Delete from ScyllaDB |
| `storage.health` | `handle_health` | Check connection |

---

## Configuration

### TOML

```toml
[engines]
storage = "scylla"

[engines.options.scylla]
contact_points = ["127.0.0.1"]
port = 9042
keyspace = "evoid"
```

---

## API

### `register_handlers(contact_points, port, keyspace)`

Register ScyllaDB as Intent handlers.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `contact_points` | `list[str]` | `["127.0.0.1"]` | Cassandra/ScyllaDB nodes |
| `port` | `int` | `9042` | Native transport port |
| `keyspace` | `str` | `evoid` | Keyspace name |

### `create_storage(contact_points, port, keyspace) -> ScyllaStorage`

Factory function for direct API access.

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
- `cassandra-driver>=3.29.0`

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
