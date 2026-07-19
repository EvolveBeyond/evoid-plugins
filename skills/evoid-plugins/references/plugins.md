# Plugin Recipes

Copy-paste patterns for each EVOID plugin.

## SQLite — File-backed KV

```python
from evoid_sqlite import create_storage

# Create with custom path
storage = create_storage("data/app.db")

# Write with namespace
await storage.write("user:1", {"name": "Alice", "role": "admin"}, namespace="auth")

# Read
user = await storage.read("user:1", namespace="auth")
# → {"name": "Alice", "role": "admin"}

# List all keys in a namespace
keys = await storage.list_keys(namespace="auth")
# → ["user:1"]

# Delete
await storage.delete("user:1", namespace="auth")
```

Dependencies: `aiosqlite>=0.20.0`

## PostgreSQL — Production relational storage

```python
from evoid_postgresql import create_storage

# Connection URL must use asyncpg dialect
storage = create_storage(url="postgresql+asyncpg://user:pass@localhost/evoid")

# Write — upserts on conflict (key, namespace)
await storage.write("order:123", {"total": 99.99, "items": ["a", "b"]}, namespace="default")

# Read
order = await storage.read("order:123")

# Delete
await storage.delete("order:123")

# Health check — runs SELECT 1
ok = await storage.health()

# Cleanup — dispose connection pool
await storage.close()
```

Dependencies: `sqlalchemy[asyncio]>=2.0.0`, `asyncpg>=0.29.0`

## ScyllaDB — High-throughput storage

```python
from evoid_scylla import create_storage

# Explicit cluster params (no URL)
storage = create_storage(
    contact_points=["127.0.0.1"],
    port=9042,
    keyspace="evoid"
)

# Same API as other storage engines
await storage.write("session:abc", {"user_id": 1, "data": "..."})
session = await storage.read("session:abc")
await storage.delete("session:abc")

# Health check — queries system.local
ok = await storage.health()
```

Dependencies: `cassandra-driver>=3.29.0`

Note: Synchronous driver wrapped in `run_in_executor`. Thread-pool overhead under high load.

## Redis — Cache with TTL

```python
from evoid_redis import create_cache

# Always set prefix when sharing Redis
cache = create_cache(url="redis://localhost:6379", prefix="evoid:")

# Set with TTL (seconds)
await cache.set("session:abc", {"user": "alice"}, ttl=300)

# Get — auto-deserializes JSON
data = await cache.get("session:abc")
# → {"user": "alice"}

# Check existence
exists = await cache.exists("session:abc")

# Delete
await cache.delete("session:abc")

# Health — PING
ok = await cache.health()
```

Dependencies: `redis[hiredis]>=5.0.0`

## SmartStorage — Multi-backend routing

```python
from evoid_smart_storage import SmartStorage

smart = SmartStorage(config={
    "mapping": {
        "user": "sqlite",
        "order": "postgresql",
        "session": "redis",
        "logs": "scylla",
    },
    "schemas": {
        "user": ["id", "name", "email", "role"],
        "order": ["id", "user_id", "total", "items", "created_at"],
    },
    "level_routing": {
        "CRITICAL": "postgresql",
        "HIGH": "scylla",
    },
    "user_connections": {
        "tenant_1": "postgresql",
        "tenant_2": "scylla",
    },
})

# Automatic routing based on data_type
await smart.write("user:1", {"name": "Alice"}, data_type="user")
# → routed to SQLite via mapping

# Override routing via metadata
intent.metadata["storage_preference"] = "postgresql"
await smart.write("user:1", data, metadata=intent.metadata)

# Multi-write — fan out to multiple backends
intent.metadata["storage_preference"] = "sqlite+postgresql"
await smart.write("critical:1", data, metadata=intent.metadata)
# → writes to both SQLite and PostgreSQL

# Schema enforcement strips unknown fields
await smart.write("user:1", {"name": "Alice", "secret": "x"}, data_type="user")
# → only {"name": "Alice"} stored (secret not in schema)
```

Requires at least one storage backend plugin installed.

## DI — Dependency injection

```python
from evoid_di import DIEngine

# Simple
di = DIEngine()
di.register("db", lambda: create_db("app.db"))
db = di.resolve("db")

# Scoped
di.register("cache", create_cache, scope="singleton")     # shared instance
di.register("request", create_request, scope="transient")  # new each call
di.register("user_svc", create_user_svc, scope="per_user") # keyed by user_id

# Context-aware routing
di = DIEngine(
    rules_config={
        "storage": [
            {"when": {"level": "CRITICAL"}, "then": "pg_storage"},
            {"when": {"metadata_has": "high_volume"}, "then": "scylla_storage"},
        ]
    },
    implementations={
        "pg_storage": lambda: create_pg(...),
        "scylla_storage": lambda: create_scylla(...),
    }
)

# MUST use resolve_async for routed services
svc = await di.resolve_async("storage", ctx)

# Convenience — resolve and inject into ctx.deps
di.inject(ctx, "storage", key="db")
# → ctx.deps.db is now populated
```

## Auth — Pluggable authentication

```python
from evoid_auth import register_provider

# Register a provider
async def jwt_provider(token: str) -> dict:
    payload = jwt.decode(token, SECRET)
    return {"user": payload["sub"], "role": payload["role"]}

register_provider("jwt", jwt_provider)

# Or register as default
register_provider("default", jwt_provider)
```

After `authenticate` processor runs, `ctx.state` contains:
- `user` — user identifier
- `role` — role string
- `auth_method` — how token was extracted
- `authenticated` — bool

`authorize` processor checks role against intent metadata:
- `required_role` — single role string
- `required_roles` — list of acceptable roles

Role hierarchy: admin(4) > editor(3) > viewer(2) > guest(1).

## Tasks — Background scheduling

```python
from evoid_tasks import scheduler

# Fire-and-forget
scheduler.run(send_email, to="alice@example.com", subject="Hello")

# Periodic with TaskContext
@scheduler.task(interval=60)
async def monitor(ctx):
    # ctx.tick — True on each tick
    # ctx.delta — seconds since last tick
    # ctx.state — persistent dict across ticks
    # ctx.event_data — data from emit()
    await check_system_health()
    ctx.state["last_check"] = time.time()

# Event-driven
@scheduler.on("order_placed")
async def on_order(data):
    await send_confirmation(data)

# Trigger event
scheduler.emit("order_placed", {"order_id": 123})

# Pipeline integration
@scheduler.as_processor("send_notification")
async def notify(ctx, intent):
    await notify_user(intent.data["user_id"])

# Inject into existing pipeline
scheduler.inject(notify, before="validate", after="authorize")
```

Lifecycle hooks for periodic tasks:
- `monitor.on_start` — called when task begins
- `monitor.on_tick` — the decorated function itself
- `monitor.on_stop` — called on cancellation
- `monitor.on_error` — called on tick failure

## Dashboard — Monitoring UI

```python
from evoid_dashboard import create_dashboard

# Launch monitoring server
create_dashboard(host="0.0.0.0", port=8001)

# API endpoints:
# /api/services    — grouped intents by service
# /api/intents     — full intent details
# /api/processors  — registered processors
# /api/messages    — message bus history
# /api/databases   — storage engine info
# /api/pipelines   — pipeline configurations
# /api/system      — system info
# /api/all         — combined payload
# /                — HTML SPA dashboard (auto-refreshes every 5s)
```

Dependencies: `jinja2>=3.1.0`, `uvicorn>=0.30.0`
Full install: `pip install "evoid-dashboard[full]"`
