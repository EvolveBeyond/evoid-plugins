<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-postgresql?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-postgresql?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-postgresql?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-postgresql</h1>

<p align="center">
  <strong>PostgreSQL storage engine via SQLAlchemy for EVOID</strong>
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
pip install evoid-postgresql
```

```python
from evoid_postgresql import create_storage

# Connect to PostgreSQL
storage = create_storage("postgresql+asyncpg://user:pass@localhost/evoid")

# Write with namespace
await storage.write("user:1", {"name": "Alice"}, namespace="users")

# Read
user = await storage.read("user:1", namespace="users")
print(user)  # {"name": "Alice"}

# Delete
await storage.delete("user:1", namespace="users")

# Health check
ok = await storage.health()
```

## Configuration

### TOML

```toml
[engines]
storage = "postgresql"

[engines.postgresql]
url = "postgresql+asyncpg://user:pass@localhost/evoid"
```

### Python

```python
from evoid_postgresql import create_storage

storage = create_storage("postgresql+asyncpg://user:pass@localhost/evoid")
```

## API

### `create_storage(url: str) -> PostgresStorage`

Factory function. Creates and returns a PostgreSQL storage engine.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | `postgresql+asyncpg://localhost/evoid` | SQLAlchemy async connection URL |

### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `write` | `async write(key: str, data: Any, namespace: str)` | `bool` | Upsert data (JSONB) |
| `read` | `async read(key: str, namespace: str)` | `Any \| None` | Read data by key + namespace |
| `delete` | `async delete(key: str, namespace: str)` | `bool` | Delete by key + namespace |
| `health` | `async health()` | `bool` | Check connection (`SELECT 1`) |
| `close` | `async close()` | `None` | Dispose SQLAlchemy engine |

## How it works

- Uses SQLAlchemy 2.0 async with `asyncpg` driver
- Table schema: `(namespace TEXT, key TEXT, value JSONB, created_at TIMESTAMP)`
- Composite primary key: `(namespace, key)`
- Upsert via `ON CONFLICT DO UPDATE`
- Lazy setup — table is created on first operation
- Namespace allows logical data partitioning

## Dependencies

- `sqlalchemy[asyncio]>=2.0.0`
- `asyncpg>=0.29.0`

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
