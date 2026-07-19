---
name: evoid-plugins
description: Build, configure, and extend EVOID plugins. Use when creating new storage/cache/logging engines, writing plugin registration code, configuring SmartStorage routing, setting up DI rules, integrating auth providers, or working with the EVOID Intent-Oriented Programming runtime and its plugin ecosystem. Also use when debugging plugin loading, connection issues, or namespace problems in EVOID projects.
compatibility: Requires Python 3.12+ and evoid>=0.4.0
metadata:
  author: EvolveBeyond
  version: "1.0"
  repo: https://github.com/EvolveBeyond/evoid-plugins
---

# EVOID Plugins

Complete reference for building and using EVOID plugins. This skill covers every plugin in the ecosystem, their contracts, configuration patterns, and known gotchas.

## Quick orientation

EVOID uses Intent-Oriented Programming. Plugins are independent Python packages that register engines via `evoid.engines.plugin.register()`. Each plugin exposes a `MANIFEST` dict and a `register_plugin()` entry point.

Install plugins individually:
```bash
pip install evoid-sqlite evoid-redis evoid-di
# or via EVOID CLI
evo install sqlite
evo install redis
```

## Contracts (evoid-base)

Three Protocol classes define what backends must implement. Any object with matching methods qualifies — no inheritance required.

### StorageEngine

```python
from evoid_base.contracts import StorageEngine

class StorageEngine(Protocol):
    async def write(self, key: str, data: Any, **kwargs) -> bool: ...
    async def read(self, key: str, **kwargs) -> Any | None: ...
    async def delete(self, key: str, **kwargs) -> bool: ...
    async def health(self) -> bool: ...
```

### CacheEngine

```python
from evoid_base.contracts import CacheEngine

class CacheEngine(Protocol):
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: float | None = None) -> bool: ...
    async def delete(self, key: str) -> bool: ...
    async def exists(self, key: str) -> bool: ...
    async def health(self) -> bool: ...
```

### LoggerEngine

```python
from evoid_base.contracts import LoggerEngine

class LoggerEngine(Protocol):
    def info(self, msg: str, **kwargs) -> None: ...
    def warning(self, msg: str, **kwargs) -> None: ...
    def error(self, msg: str, **kwargs) -> None: ...
    def debug(self, msg: str, **kwargs) -> None: ...
```

## Writing a new plugin

### Step 1: Implement the contract

Pick the contract your engine fulfills. Here's a minimal storage engine:

```python
from typing import Any
from evoid_base.contracts import StorageEngine

class MyStorage:
    def __init__(self, path: str):
        self.path = path
        self._conn = None

    async def write(self, key: str, data: Any, **kwargs) -> bool:
        # your implementation
        return True

    async def read(self, key: str, **kwargs) -> Any | None:
        return None

    async def delete(self, key: str, **kwargs) -> bool:
        return True

    async def health(self) -> bool:
        return True
```

### Step 2: Create the MANIFEST and register

```python
MANIFEST = {
    "name": "my-storage",
    "version": "1.0.0",
    "type": "storage",
    "description": "Custom storage engine",
    "entry_point": "my_storage:register_plugin",
    "dependencies": [],
    "evoid_version": ">=0.4.0",
    "tags": ["storage", "custom"],
}

def register_plugin():
    from evoid.engines.plugin import register
    register("my-storage", "storage", MyStorage, version="1.0.0")
```

### Step 3: Package structure

```
evoid-my-storage/
├── evoid_my_storage/
│   ├── __init__.py
│   └── engine.py
├── pyproject.toml
└── README.md
```

## Available plugins

### Storage engines

| Plugin | Package | Backend | Key feature |
|--------|---------|---------|-------------|
| sqlite | `evoid-sqlite` | SQLite via aiosqlite | File-based, zero-config, has `list_keys()` |
| postgresql | `evoid-postgresql` | PostgreSQL via asyncpg | JSONB storage, upsert, connection pooling |
| scylla | `evoid-scylla` | ScyllaDB/Cassandra | High-throughput, sync driver wrapped in executor |

### Cache engines

| Plugin | Package | Backend | Key feature |
|--------|---------|---------|-------------|
| redis | `evoid-redis` | Redis via redis-py | TTL support, prefix namespacing, auto-serialization |

### Infrastructure

| Plugin | Package | Purpose |
|--------|---------|---------|
| smart-storage | `evoid-smart-storage` | Multi-backend routing, schema enforcement |
| di | `evoid-di` | Dependency injection with scoped lifetimes |
| auth | `evoid-auth` | Pluggable authentication/authorization |
| tasks | `evoid-tasks` | Background tasks + pipeline integration |
| dashboard | `evoid-dashboard` | Monitoring UI (ASGI app) |

## Configuration patterns

### Storage instantiation

```python
# SQLite — zero config
from evoid_sqlite import create_storage
storage = create_storage("app.db")

# PostgreSQL — connection URL
from evoid_postgresql import create_storage
storage = create_storage(url="postgresql+asyncpg://user:pass@localhost/evoid")

# ScyllaDB — explicit cluster params
from evoid_scylla import create_storage
storage = create_storage(contact_points=["127.0.0.1"], port=9042, keyspace="evoid")
```

All storage engines are lazy — connections open on first operation, not at instantiation.

### Cache instantiation

```python
from evoid_redis import create_cache
cache = create_cache(url="redis://localhost:6379", prefix="evoid:")
```

### Namespace usage

All storage engines support a `namespace` parameter (default: `"default"`). Namespaces partition data within a single backend:

```python
await storage.write("user:1", {"name": "Alice"}, namespace="auth")
await storage.write("user:1", {"name": "Bob"}, namespace="analytics")
# Different data, same key, different namespaces
```

### SmartStorage routing

```python
from evoid_smart_storage import SmartStorage

smart = SmartStorage(config={
    # Type-based routing
    "mapping": {
        "user": "sqlite",
        "order": "postgresql",
        "session": "redis",
    },
    # Schema enforcement — strips unknown fields
    "schemas": {
        "user": ["id", "name", "email"],
        "order": ["id", "user_id", "total", "items"],
    },
    # Per-level routing
    "level_routing": {
        "CRITICAL": "postgresql",
    },
    # Multi-tenant routing
    "user_connections": {
        "tenant_1": "postgresql",
        "tenant_2": "scylla",
    },
})
```

Routing priority (first match wins):
1. `intent.metadata["storage_preference"]` — explicit override
2. `user_connections[user_id]` — per-tenant
3. `level_routing[intent.level]` — per-level
4. `mapping[data_type]` — default type mapping

Multi-write: set `storage_preference` to `"memory+redis"` (plus-separated) to fan out writes. Reads hit first target; deletes fan out to all.

### DI with routing rules

```python
from evoid_di import DIEngine

di = DIEngine()

# Simple registration
di.register("db", lambda: create_db("app.db"))

# Scoped lifetime
di.register("cache", create_cache, scope="singleton")  # shared
di.register("request_ctx", create_ctx, scope="transient")  # new each call
di.register("user_svc", create_user_svc, scope="per_user")  # keyed by user_id

# Context-aware routing
di = DIEngine(
    rules_config={
        "storage": [
            {"when": {"level": "CRITICAL"}, "then": "postgresql_storage"},
            {"when": {"metadata_has": "high_volume"}, "then": "scylla_storage"},
        ]
    },
    implementations={
        "postgresql_storage": lambda: create_pg_storage(...),
        "scylla_storage": lambda: create_scylla_storage(...),
    }
)
# MUST use resolve_async for routed services
svc = await di.resolve_async("storage", ctx)
```

### Auth provider registration

```python
from evoid_auth import register_provider

async def my_auth(token: str) -> dict:
    user = await db.find_by_token(token)
    return {"user": user.name, "role": user.role}

register_provider("jwt", my_auth)
# Or register as "default" to be used when no provider is specified
register_provider("default", my_auth)
```

Token extraction priority: `metadata["token"]` → `Authorization: Bearer` → `Authorization: Token` → `X-API-Key` header → query param.

After `authenticate` runs, `ctx.state` contains: `user`, `role`, `auth_method`, `authenticated`.

Role hierarchy: admin(4) > editor(3) > viewer(2) > guest(1).

### Task scheduling

```python
from evoid_tasks import scheduler

# Fire-and-forget
scheduler.run(send_email, to="alice@example.com")

# Periodic
@scheduler.task(interval=60)
async def monitor(ctx):
    # ctx has: tick, delta, state, event_data
    await check_levels()

# Event-driven
@scheduler.on("order_placed")
async def handle_order(data):
    await process(data)

# Pipeline integration
@scheduler.as_processor("send_notification")
async def notify(ctx, intent):
    await send(intent.data)
```

## Gotchas

Read these before debugging plugin issues.

**StorageEngine write parameter name:** The Protocol defines `write(key, data, **kwargs)` but SQLiteStorage names its parameter `value`. This works at runtime because kwargs absorb the difference, but type-checkers may flag it. PostgreSQL and Scylla use `data` correctly.

**SQLite missing health():** `evoid-sqlite` does not implement `health()` despite the Protocol requiring it. SmartStorage checks `hasattr(eng, "health")` defensively, but direct callers will get `AttributeError`. Add a health method to any custom SQLite wrapper.

**Scylla async overhead:** `cassandra-driver` is synchronous. Every operation goes through `run_in_executor` → thread pool. Under high load this becomes a bottleneck compared to natively async PostgreSQL/Redis. Consider this when choosing between Scylla and PostgreSQL for write-heavy workloads.

**SmartStorage lazy resolution:** Backend engines resolve from the plugin registry on first `write`/`read`/`delete`, not at construction. If a backend plugin is missing, you get a runtime error at first use. Always verify backends are installed before deploying.

**Auth default provider:** When no `auth_provider` is in metadata, the processor looks for a provider named `"default"`. If you register only one provider, name it `"default"` or pass the name explicitly in every intent's metadata.

**DI sync vs async:** If a service has routing rules, calling synchronous `di.resolve()` raises `ValueError`. Use `await di.resolve_async("service", ctx)` for any service with context-aware routing.

**Redis prefix:** `create_cache(url, prefix="evoid:")` — always set a prefix when sharing a Redis instance. Without it, keys collide with other applications.

**PostgreSQL dialect:** Connection URL must use `postgresql+asyncpg://` prefix. Using plain `postgresql://` will fail at connection time.

## See also

- [Contracts reference](references/contracts.md) — full protocol signatures and utility functions
- [Plugin recipes](references/plugins.md) — copy-paste patterns for each plugin
- [Troubleshooting](references/troubleshooting.md) — common errors and fixes
