# EVOID Plugins

Official plugin collection for the [EVOID](https://github.com/EvolveBeyond/EVOID) Intent-Oriented Programming runtime.

Each plugin is an independent Python package on PyPI. Install only what you need.

## Install

```bash
uv add evoid-sqlite
uv add evoid-redis
uv add evoid-di
uv add evoid-smart-storage
```

Or via EVOID CLI:

```bash
evo install di
evo install redis
evo install smart-storage
```

## Architecture

All plugins integrate with **evoid-di** for dependency injection, service discovery, and fault tolerance.

```
┌─────────────────────────────────────────────────────┐
│                    Your App                         │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              evoid-di (Global DI)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   register   │  │   resolve   │  │  fallback   │ │
│  │   health     │  │   cluster   │  │  load-balance│ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                   Plugins                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ sqlite   │ │ postgres │ │ redis    │           │
│  │ storage  │ │ storage  │ │ cache    │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       └─────────────┼───────────┘                   │
│                     ▼                               │
│            evoid-smart-storage                      │
│         (routes by data type/level)                 │
└─────────────────────────────────────────────────────┘
```

## Plugins

| Package | PyPI | Description |
|---------|------|-------------|
| `evoid-base` | [![PyPI](https://img.shields.io/pypi/v/evoid-base.svg)](https://pypi.org/project/evoid-base/) | Base contracts and utilities |
| `evoid-di` | [![PyPI](https://img.shields.io/pypi/v/evoid-di.svg)](https://pypi.org/project/evoid-di/) | DI engine with fault tolerance |
| `evoid-sqlite` | [![PyPI](https://img.shields.io/pypi/v/evoid-sqlite.svg)](https://pypi.org/project/evoid-sqlite/) | SQLite storage engine |
| `evoid-redis` | [![PyPI](https://img.shields.io/pypi/v/evoid-redis.svg)](https://pypi.org/project/evoid-redis/) | Redis cache with TTL |
| `evoid-postgresql` | [![PyPI](https://img.shields.io/pypi/v/evoid-postgresql.svg)](https://pypi.org/project/evoid-postgresql/) | PostgreSQL via SQLAlchemy |
| `evoid-scylla` | [![PyPI](https://img.shields.io/pypi/v/evoid-scylla.svg)](https://pypi.org/project/evoid-scylla/) | ScyllaDB/Cassandra storage |
| `evoid-smart-storage` | [![PyPI](https://img.shields.io/pypi/v/evoid-smart-storage.svg)](https://pypi.org/project/evoid-smart-storage/) | Multi-DB routing, schema enforcement |
| `evoid-auth` | [![PyPI](https://img.shields.io/pypi/v/evoid-auth.svg)](https://pypi.org/project/evoid-auth/) | Bring your own auth provider |
| `evoid-tasks` | [![PyPI](https://img.shields.io/pypi/v/evoid-tasks.svg)](https://pypi.org/project/evoid-tasks/) | Background tasks + logging |
| `evoid-dashboard` | [![PyPI](https://img.shields.io/pypi/v/evoid-dashboard.svg)](https://pypi.org/project/evoid-dashboard/) | Monitoring dashboard |
| `evoid-cluster` | [![PyPI](https://img.shields.io/pypi/v/evoid-cluster.svg)](https://pypi.org/project/evoid-cluster/) | Multi-node clustering |
| `evoid-godot` | [![PyPI](https://img.shields.io/pypi/v/evoid-godot.svg)](https://pypi.org/project/evoid-godot/) | Godot game integration |
| `evoid-scheduler` | [![PyPI](https://img.shields.io/pypi/v/evoid-scheduler.svg)](https://pypi.org/project/evoid-scheduler/) | Priority-aware scheduler |
| `evoid-transport` | [![PyPI](https://img.shields.io/pypi/v/evoid-transport.svg)](https://pypi.org/project/evoid-transport/) | Low-latency UDP transport |

## Creating Plugins

### Method 1: With DI (Recommended)

Plugins that use DI get automatic service discovery, fault tolerance, and cluster integration.

```python
from evoid_di import di

def register_handlers(config=None):
    # 1. Register with DI
    di.register("storage.mydb", lambda: MyStorage(config), scope="singleton")

    # 2. Define fallback chain
    di.set_fallback("storage.mydb", ["storage.sqlite", "cache.redis"])

    # 3. Optional: health check
    di.set_health_check("storage.mydb", lambda: my_storage.ping())

    # 4. Wire to EVOID intents
    from evoid.core import register as register_intent, register_processor

    async def handle_read(ctx):
        storage = di.resolve("storage.mydb")  # resolve via DI
        return await storage.read(ctx.intent.metadata.get("key"))

    register_processor("storage.read", handle_read)
```

**Benefits:**
- Automatic fallback when service fails
- Load balancing across cluster nodes
- Health checking and auto-reconnect
- Smart-storage integration

### Method 2: Without DI (Simple)

For quick prototypes or standalone use.

```python
from evoid_sqlite import create_storage

storage = create_storage("app.db")
await storage.write("user:1", {"name": "Alice"})
user = await storage.read("user:1")
```

## DI Features

### Service Registration

```python
from evoid_di import di

# Register services
di.register("storage.sqlite", lambda: SQLiteStorage("app.db"), scope="singleton")
di.register("cache.redis", lambda: RedisCache("redis://localhost"), scope="singleton")

# Batch registration
di.register_many({
    "db": create_db,
    "cache": create_cache,
})
```

### Resolution

```python
# Simple resolve
storage = di.resolve("storage.sqlite")

# Safe resolve (returns None if not found)
storage = di.resolve_or_none("nonexistent")

# Resolve with automatic fallback
storage = di.resolve_with_fallback("storage.postgresql")

# Resolve first available from list
cache = di.resolve_any("cache.redis", "cache.memory", "storage.sqlite")
```

### Fault Tolerance

```python
# Define fallback chain
di.set_fallback("storage.postgresql", ["storage.sqlite", "cache.redis"])

# Health checking
di.set_health_check("cache.redis", lambda: redis.ping())

# Mark services unhealthy
di.mark_unhealthy("cache.redis")

# Auto-fallback on failure
storage = di.resolve_with_fallback("storage.postgresql")
# Tries: postgresql → sqlite → redis → None (no crash)
```

### Cluster Integration

```python
# Connect cluster registry
from evoid_cluster import ServiceRegistry
di.set_cluster_registry(cluster._registry)

# Remote resolution (automatic)
storage = di.resolve("storage.postgresql")
# If not local, checks cluster peers automatically
```

### Scopes

```python
# Singleton (default) - one instance
di.register("db", create_db, scope="singleton")

# Transient - new instance each time
di.register("request", create_request, scope="transient")

# Per-user - isolated per user
di.register("session", create_session, scope="per_user")
```

## Smart Storage

Routes data to different backends based on type, level, or metadata.

```python
from evoid_smart_storage import register_handlers

register_handlers(config={
    "mapping": {
        "credentials": "cache.redis",      # sensitive data → Redis
        "session": "storage.sqlite",        # session → SQLite
        "logs": "storage.postgresql",       # logs → PostgreSQL
    },
    "level_routing": {
        "CRITICAL": "storage.postgresql",   # critical → PostgreSQL
    },
    "schemas": {
        "credentials": ["email", "password_hash"],
        "session": ["username", "uuid", "cookie"],
    },
})
```

## Cluster

Multi-node clustering with automatic failover.

```python
from evoid_cluster import ClusterBridge, ClusterConfig

config = ClusterConfig(
    node_id="node-1",
    host="0.0.0.0",
    port=9100,
    services=["storage.sqlite", "cache.redis"],
    peers={"node-2": {"host": "192.168.1.11", "port": 9100}},
)

bridge = ClusterBridge(config)
await bridge.start()
```

**Features:**
- Automatic failover between nodes
- Load balancing across healthy nodes
- Auto-reconnect to offline nodes
- Heartbeat-based health checking
- Message bus integration

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Standard](https://evolvebeyond.github.io/EVOID/learn/plugin-standard/)

## License

MIT
