<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-sqlite?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-sqlite?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-sqlite?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-sqlite</h1>

<p align="center">
  <strong>SQLite storage engine for EVOID</strong>
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
pip install evoid-sqlite
```

```python
from evoid_sqlite import create_storage

# Create storage
storage = create_storage("my_app.db")

# Write data
await storage.write("user:1", {"name": "Alice", "role": "admin"})

# Read data
user = await storage.read("user:1")
print(user)  # {"name": "Alice", "role": "admin"}

# Delete
await storage.delete("user:1")

# Health check
ok = await storage.health()
```

## Configuration

### TOML

```toml
[engines]
storage = "sqlite"

[engines.sqlite]
path = "data/my_app.db"
```

### Python

```python
from evoid_sqlite import create_storage

storage = create_storage("data/my_app.db")
```

## API

### `create_storage(path: str) -> SqliteStorage`

Factory function. Creates and returns a SQLite storage engine.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str` | — | Path to SQLite database file |

### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `read` | `async read(key: str)` | `Any \| None` | Read value by key |
| `write` | `async write(key: str, value: Any)` | `bool` | Write value (JSON serialized) |
| `delete` | `async delete(key: str)` | `bool` | Delete by key |
| `health` | `async health()` | `bool` | Check connection |

## How it works

- Values are stored as JSON in a `kv_store` table
- Schema: `(key TEXT PRIMARY KEY, value TEXT, created_at TIMESTAMP)`
- Async via `aiosqlite`
- Auto-creates table on first use

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
