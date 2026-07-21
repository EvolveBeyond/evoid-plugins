# EVOID Plugins

Official plugin collection for the [EVOID](https://github.com/EvolveBeyond/EVOID) Intent-Oriented Programming runtime.

Each plugin is an independent Python package on PyPI. Install only what you need.

## Install

```bash
uv add evoid-base
uv add evoid-sqlite
uv add evoid-redis
uv add evoid-postgresql
uv add evoid-scylla
uv add evoid-smart-storage
uv add evoid-di
uv add evoid-auth
uv add evoid-tasks
uv add evoid-dashboard
uv add evoid-cluster
uv add evoid-godot
uv add evoid-scheduler
uv add evoid-transport
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
| `evoid-base` | [![PyPI](https://img.shields.io/pypi/v/evoid-base.svg)](https://pypi.org/project/evoid-base/) | Base contracts and utilities for EVOID plugins |
| `evoid-sqlite` | [![PyPI](https://img.shields.io/pypi/v/evoid-sqlite.svg)](https://pypi.org/project/evoid-sqlite/) | SQLite storage engine |
| `evoid-redis` | [![PyPI](https://img.shields.io/pypi/v/evoid-redis.svg)](https://pypi.org/project/evoid-redis/) | Redis cache with TTL support |
| `evoid-postgresql` | [![PyPI](https://img.shields.io/pypi/v/evoid-postgresql.svg)](https://pypi.org/project/evoid-postgresql/) | PostgreSQL via SQLAlchemy + asyncpg |
| `evoid-scylla` | [![PyPI](https://img.shields.io/pypi/v/evoid-scylla.svg)](https://pypi.org/project/evoid-scylla/) | ScyllaDB/Cassandra storage |
| `evoid-smart-storage` | [![PyPI](https://img.shields.io/pypi/v/evoid-smart-storage.svg)](https://pypi.org/project/evoid-smart-storage/) | Data-type routing, multi-tenancy, schema enforcement |
| `evoid-di` | [![PyPI](https://img.shields.io/pypi/v/evoid-di.svg)](https://pypi.org/project/evoid-di/) | DI engine — simple, scoped, or context-aware |
| `evoid-auth` | [![PyPI](https://img.shields.io/pypi/v/evoid-auth.svg)](https://pypi.org/project/evoid-auth/) | Bring your own auth provider |
| `evoid-tasks` | [![PyPI](https://img.shields.io/pypi/v/evoid-tasks.svg)](https://pypi.org/project/evoid-tasks/) | Background tasks + structured logging |
| `evoid-dashboard` | [![PyPI](https://img.shields.io/pypi/v/evoid-dashboard.svg)](https://pypi.org/project/evoid-dashboard/) | Monitoring dashboard — service map, data lineage, DB viewer, logs |
| `evoid-cluster` | [![PyPI](https://img.shields.io/pypi/v/evoid-cluster.svg)](https://pypi.org/project/evoid-cluster/) | Multi-node clustering via WebSocket |
| `evoid-godot` | [![PyPI](https://img.shields.io/pypi/v/evoid-godot.svg)](https://pypi.org/project/evoid-godot/) | Godot game integration adapter |
| `evoid-scheduler` | [![PyPI](https://img.shields.io/pypi/v/evoid-scheduler.svg)](https://pypi.org/project/evoid-scheduler/) | Priority-aware scheduler with adaptive concurrency |
| `evoid-transport` | [![PyPI](https://img.shields.io/pypi/v/evoid-transport.svg)](https://pypi.org/project/evoid-transport/) | Low-latency UDP transport (Rust core) |

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

### Scheduler

```python
from evoid_scheduler import SchedulerEngine, Priority

scheduler = SchedulerEngine()
await scheduler.submit(intent=process_payment, priority=Priority.CRITICAL)
```

### Cluster

```python
from evoid_cluster import register_handlers

register_handlers(config={
    "node": {"id": "node-1", "host": "0.0.0.0", "port": 9100},
    "cluster": {"secret": "my-secret"},
})
```

### Transport

```python
from evoid_transport import register_handlers

register_handlers(host="0.0.0.0", port=9000)
```

### Godot

```python
from evoid_godot import register_handlers

register_handlers()
```

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Standard](https://evolvebeyond.github.io/EVOID/learn/plugin-standard/)

## License

MIT
