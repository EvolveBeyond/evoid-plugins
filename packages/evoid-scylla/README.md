<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-scylla?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-scylla?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-scylla?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-scylla</h1>

<p align="center">
  <strong>ScyllaDB/Cassandra storage engine for EVOID</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#api">API</a> •
  <a href="#installation">Install</a> •
  <a href="https://evolvebeyond.github.io/EVOID/">Docs</a>
</p>

---

## Quick Start

```bash
pip install evoid-scylla
```

```python
from evoid_scylla import create_storage

# Connect to ScyllaDB/Cassandra
storage = create_storage(
    contact_points=["127.0.0.1"],
    port=9042,
    keyspace="evoid",
)

# Write with namespace
await storage.write("user:1", {"name": "Alice"}, namespace="users")

# Read
user = await storage.read("user:1", namespace="users")
print(user)  # {"name": "Alice"}

# Delete
await storage.delete("user:1", namespace="users")

# Health check
ok = await storage.health()

# Cleanup
await storage.close()
```

## Configuration

### TOML

```toml
[engines]
storage = "scylla"

[engines.scylla]
contact_points = ["127.0.0.1"]
port = 9042
keyspace = "evoid"
protocol_version = 4
```

### Python

```python
from evoid_scylla import create_storage

storage = create_storage(
    contact_points=["10.0.0.1", "10.0.0.2"],
    port=9042,
    keyspace="myapp",
    protocol_version=4,
)
```

## API

### `create_storage(contact_points, port, keyspace, protocol_version) -> ScyllaStorage`

Factory function. Creates and returns a ScyllaDB/Cassandra storage engine.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `contact_points` | `list[str]` | `["127.0.0.1"]` | Cluster contact points |
| `port` | `int` | `9042` | CQL native transport port |
| `keyspace` | `str` | `"evoid"` | Keyspace name |
| `protocol_version` | `int` | `4` | Cassandra protocol version |

### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `write` | `async write(key: str, data: Any, namespace: str)` | `bool` | Insert/update data |
| `read` | `async read(key: str, namespace: str)` | `Any \| None` | Read by key + namespace |
| `delete` | `async delete(key: str, namespace: str)` | `bool` | Delete by key + namespace |
| `health` | `async health()` | `bool` | Query `system.local` |
| `close` | `async close()` | `None` | Shutdown driver session |

## How it works

- Uses `cassandra-driver` (synchronous) wrapped via `run_in_executor` for async
- Table schema: `(namespace TEXT, key TEXT, value TEXT, PRIMARY KEY (namespace, key))`
- Values are JSON serialized as text
- Auto-creates keyspace and table on first use
- Works with both ScyllaDB and Cassandra (wire-compatible)

## Dependencies

- `cassandra-driver>=3.29.0`

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
