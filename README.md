# EVOID Plugins

Official plugin collection for the [EVOID](https://github.com/EvolveBeyond/EVOID) Intent-Oriented Programming runtime.

Each plugin is an independent Python package on PyPI. Install only what you need.

## Install

```bash
pip install evoid-sqlite
pip install evoid-redis
pip install evoid-di
pip install evoid-auth
```

Or via EVOID CLI:

```bash
evo install di
evo install redis
evo install smart-storage
```

## Plugins

| Package | PyPI | Description |
|---------|------|-------------|
| `evoid-base` | [![PyPI](https://img.shields.io/pypi/v/evoid-base.svg)](https://pypi.org/project/evoid-base/) | Shared contracts (StorageEngine, CacheEngine, LoggerEngine) |
| `evoid-sqlite` | [![PyPI](https://img.shields.io/pypi/v/evoid-sqlite.svg)](https://pypi.org/project/evoid-sqlite/) | SQLite storage engine |
| `evoid-redis` | [![PyPI](https://img.shields.io/pypi/v/evoid-redis.svg)](https://pypi.org/project/evoid-redis/) | Redis cache with TTL support |
| `evoid-postgresql` | [![PyPI](https://img.shields.io/pypi/v/evoid-postgresql.svg)](https://pypi.org/project/evoid-postgresql/) | PostgreSQL via SQLAlchemy + asyncpg |
| `evoid-scylla` | [![PyPI](https://img.shields.io/pypi/v/evoid-scylla.svg)](https://pypi.org/project/evoid-scylla/) | ScyllaDB/Cassandra storage |
| `evoid-smart-storage` | [![PyPI](https://img.shields.io/pypi/v/evoid-smart-storage.svg)](https://pypi.org/project/evoid-smart-storage/) | Multi-DB routing, schema enforcement |
| `evoid-di` | [![PyPI](https://img.shields.io/pypi/v/evoid-di.svg)](https://pypi.org/project/evoid-di/) | DI engine — simple, scoped, or context-aware |
| `evoid-auth` | [![PyPI](https://img.shields.io/pypi/v/evoid-auth.svg)](https://pypi.org/project/evoid-auth/) | Bring your own auth provider |
| `evoid-tasks` | [![PyPI](https://img.shields.io/pypi/v/evoid-tasks.svg)](https://pypi.org/project/evoid-tasks/) | Background tasks + structured logging |
| `evoid-dashboard` | [![PyPI](https://img.shields.io/pypi/v/evoid-dashboard.svg)](https://pypi.org/project/evoid-dashboard/) | Monitoring dashboard |

## Examples

### Storage

```python
from evoid_sqlite import create_storage

storage = create_storage("app.db")
await storage.write("user:1", {"name": "Alice"})
user = await storage.read("user:1")
```

### DI

```python
from evoid_di import DIEngine

di = DIEngine()
di.register("db", lambda: create_db("app.db"))
db = di.resolve("db")
```

### Auth

```python
from evoid_auth import register_provider

async def my_auth(token: str) -> dict:
    user = await db.find_by_token(token)
    return {"user": user.name, "role": user.role}

register_provider("jwt", my_auth)
```

### Tasks

```python
from evoid_tasks import scheduler

scheduler.run(send_email, to="alice@example.com")

@scheduler.task(interval=60)
async def monitor(ctx):
    await check_levels()
```

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Standard](https://evolvebeyond.github.io/EVOID/learn/plugin-standard/)

## License

MIT
