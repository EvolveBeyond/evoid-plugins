<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-postgresql?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-postgresql?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-postgresql?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-postgresql</h1>

<p align="center">
  <strong>PostgreSQL storage engine — Intent Handler system</strong>
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
pip install evoid-postgresql
```

### Method 1: Intent Handler (Recommended)

```python
from evoid_postgresql import register_handlers
from evoid.core.storage import storage_read, storage_write, storage_delete

# Register PostgreSQL as storage handler
register_handlers(url="postgresql+asyncpg://user:pass@localhost/evoid")

# Use high-level API
await storage_write("user:1", {"name": "Alice"})
user = await storage_read("user:1")
await storage_delete("user:1")
```

### Method 2: Direct API

```python
from evoid_postgresql import create_storage

storage = create_storage("postgresql+asyncpg://user:pass@localhost/evoid")
await storage.write("user:1", {"name": "Alice"})
user = await storage.read("user:1")
```

---

## Intent Handler

evoid-postgresql registers these Intent handlers:

| Intent | Handler | Description |
|--------|---------|-------------|
| `storage.read` | `handle_read` | Read from PostgreSQL |
| `storage.write` | `handle_write` | Write to PostgreSQL |
| `storage.delete` | `handle_delete` | Delete from PostgreSQL |
| `storage.health` | `handle_health` | Check connection |

---

## Configuration

### TOML

```toml
[engines]
storage = "postgresql"

[engines.options.postgresql]
url = "postgresql+asyncpg://user:pass@localhost/evoid"
```

### Python

```python
from evoid.config import config

app = config(
    engines={
        "storage": "postgresql",
        "options": {
            "postgresql": {
                "url": "postgresql+asyncpg://prod:secret@db/evoid",
            },
        },
    },
)
```

---

## API

### `register_handlers(url: str)`

Register PostgreSQL as Intent handlers.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | `postgresql+asyncpg://localhost/evoid` | SQLAlchemy async connection URL |

### `create_storage(url: str) -> PostgresStorage`

Factory function for direct API access.

### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `write` | `async write(key: str, data: dict)` | `bool` | Upsert data (JSONB) |
| `read` | `async read(key: str)` | `Any \| None` | Read data by key |
| `delete` | `async delete(key: str)` | `bool` | Delete by key |
| `health` | `async health()` | `bool` | Check connection |

---

## Dependencies

- `evoid>=0.4.0`
- `sqlalchemy[asyncio]>=2.0.0`
- `asyncpg>=0.29.0`

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
