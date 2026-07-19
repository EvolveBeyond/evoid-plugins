---
name: evoid-plugins
description: Build applications with EVOID Intent-Oriented Programming runtime. Use when creating Intents, writing processors, configuring pipelines, building web APIs with @route or @controller, setting up storage/cache/DI/auth, writing plugins, testing with tc(), or deploying EVOID services. Also use for debugging pipeline execution, plugin loading, connection issues, or IOP architecture decisions.
compatibility: Requires Python 3.12+ and evoid>=0.4.0
metadata:
  author: EvolveBeyond
  version: "2.0"
  repo: https://github.com/EvolveBeyond/evoid-plugins
---

# EVOID — Intent-Oriented Programming Runtime

EVOID is a Python runtime where **data declares what it needs, the runtime handles how**. Your Intents carry infrastructure intent (storage, caching, auth, audit), and the pipeline resolves it automatically. Zero boilerplate, zero config scattering.

## Core concepts

### Intent

An Intent is a **frozen dataclass** — pure data that declares what you want to achieve. Immutable, thread-safe.

```python
from evoid import Intent, Level

GET_USER = Intent(
    name="get_user",
    level=Level.STANDARD,
    metadata={"method": "GET", "path": "/users/{id}"},
    timeout=10.0,
    priority=0,
)
```

| Field | Type | Purpose |
|-------|------|---------|
| `name` | str | Unique identifier |
| `level` | Level | Protection level (ephemeral/standard/critical) |
| `metadata` | dict | Arbitrary data for processors |
| `timeout` | float \| None | Max seconds before timeout |
| `priority` | int | Execution order (higher first) |

### Intent Levels

Each level maps to a **default pipeline** with different infrastructure:

| Level | Pipeline | Timeout | Use Case |
|-------|----------|---------|----------|
| `EPHEMERAL` | `validate` | 5s | Cache, sessions, temp data |
| `STANDARD` | `validate`, `authorize` | 10s | User profiles, posts, comments |
| `CRITICAL` | `validate`, `authorize`, `audit`, `protect` | 30s | Payments, medical, legal |

Pick the level that matches your data's criticality. Overusing `critical` defeats the purpose.

### Pipeline

A pipeline is a **list of processor names** executed in order. The runtime resolves it from the Intent level, then runs each processor sequentially, passing a shared `Context`.

```
Intent → Resolver → PipelineConfig → [validate, authorize, handler, audit] → Result
```

### Processor

A processor is a **pure function** — receives `Context`, returns a result. One responsibility per processor.

```python
from evoid.core import Context

async def validate_input(ctx: Context) -> dict:
    data = ctx.state.get("data")
    if not data:
        raise ValueError("Missing data")
    return {"validated": True}
```

### Context

Mutable databag shared between processors:

```python
ctx.intent      # Intent being processed
ctx.state       # Shared state (read/write between processors)
ctx.deps        # Injected dependencies (engines, services)
ctx.metadata    # Extra metadata (request params, body)
ctx.errors      # Accumulated non-fatal errors
ctx.id          # Unique context ID
```

### Result

Every pipeline execution returns:

```python
result.success     # bool — completed without error?
result.value       # Any — return value from last processor
result.error       # Exception | None
result.processors  # tuple[str, ...] — names of processors that ran
result.duration    # float — total execution time in seconds
```

## Three syntax styles

All IOP underneath. Pick your style.

### @route — Function decorators (FastAPI/Flask style)

```python
from evoid.web.route import Service, get, post

app = Service("my-api")

@get("/users/{user_id}")
async def get_user(user_id: int) -> dict:
    return {"id": user_id, "name": "Alice"}

@post("/payments", level="critical")
async def process_payment(amount: float) -> dict:
    return {"status": "paid", "amount": amount}
```

### @controller — Class-based (NestJS/Django REST style)

```python
from evoid.web.controller import Service, Controller, GET, POST

app = Service("my-api")

@Controller("/users")
class UserController:
    @GET("/{user_id}")
    async def get_user(self, user_id: int) -> dict:
        return {"id": user_id}

    @POST("/")
    async def create_user(self, name: str) -> dict:
        return {"id": 1, "name": name}
```

### Native — Full control

```python
from evoid import Intent, Level, add_intent, on

GET_USER = Intent(name="get_user", level=Level.STANDARD)

async def handler(intent: Intent) -> dict:
    return {"id": 1, "name": "Alice"}

add_intent(GET_USER, handler)
```

## Writing processors

### Read-Process-Write pattern

```python
from evoid.core import Context
from evoid import register_processor

async def enrich_user(ctx: Context) -> dict:
    user_id = ctx.state.get("user_id")
    user = await db.get_user(user_id)
    ctx.state["user"] = user
    return {"enriched": True}

register_processor("enrich_user", enrich_user)
```

### Conditional logic by level

```python
async def adaptive_processor(ctx: Context) -> dict:
    if ctx.intent.level == Level.CRITICAL:
        ctx.state["consistency"] = "strong"
        ctx.state["audit"] = True
    elif ctx.intent.level == Level.EPHEMERAL:
        ctx.state["cache_only"] = True
    return {"adapted": True}
```

### Error accumulation (non-fatal)

```python
async def validate_optional(ctx: Context) -> dict:
    try:
        validate(ctx.state.get("data"))
    except ValidationError as e:
        ctx.errors.append(e)  # pipeline continues
    return {"validated": True}
```

## Pipeline customization

### Custom pipeline per intent

```python
from evoid.core.extend import add_intent_with_pipeline

PAYMENT = Intent(name="process_payment", level=Level.CRITICAL)

add_intent_with_pipeline(
    PAYMENT,
    processors=["validate", "check_fraud", "charge", "notify"],
    handler=handle_payment,
)
```

### Inject processors before/after

```python
from evoid.web.route import Service, get, before, after

app = Service("api")

@get("/users/{id}")
async def get_user(id: int) -> dict:
    return {"id": id}

before("GET:/users/{id}", "rate_limit")
after("GET:/users/{id}", "log_response")
```

### Replace entire pipeline

```python
from evoid.core.extend import replace_pipeline
replace_pipeline("GET:/users/{id}", ["cache", "fetch_user", "log"])
```

### Remove a processor

```python
from evoid.core.extend import remove_processor
remove_processor("process_payment", "audit")
```

## Plugins

Plugins are independent Python packages on PyPI. Install only what you need.

```bash
evo install sqlite       # Storage
evo install redis        # Cache
evo install di           # Dependency injection
evo install auth         # Authentication
evo install tasks        # Background tasks
evo install dashboard    # Monitoring UI
evo install smart-storage # Multi-backend routing
```

### Storage engines

```python
# SQLite — zero config
from evoid_sqlite import create_storage
storage = create_storage("app.db")

# PostgreSQL — connection URL (must use asyncpg dialect)
from evoid_postgresql import create_storage
storage = create_storage(url="postgresql+asyncpg://user:pass@localhost/evoid")

# ScyllaDB — explicit cluster params
from evoid_scylla import create_storage
storage = create_storage(contact_points=["127.0.0.1"], port=9042, keyspace="evoid")

# All storage is lazy — connections open on first operation
await storage.write("user:1", {"name": "Alice"}, namespace="auth")
user = await storage.read("user:1", namespace="auth")
```

### Cache

```python
from evoid_redis import create_cache
cache = create_cache(url="redis://localhost:6379", prefix="evoid:")
await cache.set("session:abc", {"user": "alice"}, ttl=300)
data = await cache.get("session:abc")
```

### DI — Dependency injection

```python
from evoid_di import DIEngine

di = DIEngine()

# Simple
di.register("db", lambda: create_db("app.db"))
db = di.resolve("db")

# Scoped
di.register("cache", create_cache, scope="singleton")     # shared
di.register("request", create_request, scope="transient")  # new each call

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
svc = await di.resolve_async("storage", ctx)
```

### Auth — Pluggable authentication

```python
from evoid_auth import register_provider

async def jwt_provider(token: str) -> dict:
    payload = jwt.decode(token, SECRET)
    return {"user": payload["sub"], "role": payload["role"]}

register_provider("default", jwt_provider)
```

After `authenticate` runs: `ctx.state` contains `user`, `role`, `auth_method`, `authenticated`.

Role hierarchy: admin(4) > editor(3) > viewer(2) > guest(1).

### Tasks — Background scheduling

```python
from evoid_tasks import scheduler

# Fire-and-forget
scheduler.run(send_email, to="alice@example.com")

# Periodic
@scheduler.task(interval=60)
async def monitor(ctx):
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

### SmartStorage — Multi-backend routing

```python
from evoid_smart_storage import SmartStorage

smart = SmartStorage(config={
    "mapping": {"user": "sqlite", "order": "postgresql"},
    "schemas": {"user": ["id", "name", "email"]},
    "level_routing": {"CRITICAL": "postgresql"},
    "user_connections": {"tenant_1": "postgresql"},
})
```

Routing priority: `storage_preference` → `user_connections` → `level_routing` → `mapping`.

Multi-write: `"storage_preference": "sqlite+postgresql"` fans out writes.

### Dashboard — Monitoring UI

```python
from evoid_dashboard import create_dashboard
create_dashboard(host="0.0.0.0", port=8001)
# API: /api/services, /api/intents, /api/processors, /api/messages, /api/databases
```

## Writing a new plugin

### Step 1: Implement the contract

```python
from evoid_base.contracts import StorageEngine

class MyStorage:
    async def write(self, key: str, data: Any, **kwargs) -> bool: ...
    async def read(self, key: str, **kwargs) -> Any | None: ...
    async def delete(self, key: str, **kwargs) -> bool: ...
    async def health(self) -> bool: ...
```

### Step 2: Register

```python
MANIFEST = {
    "name": "my-storage",
    "version": "1.0.0",
    "type": "storage",
    "description": "Custom storage engine",
    "entry_point": "my_storage:register_plugin",
    "dependencies": [],
    "evoid_version": ">=0.4.0",
    "tags": ["storage"],
}

def register_plugin():
    from evoid.engines.plugin import register
    register("my-storage", "storage", MyStorage, version="1.0.0")
```

## Testing

```python
from evoid.testing import tc
from myapp import GET_USER

def test_get_user():
    return tc(GET_USER, expect={"id": 1})

# Run with: pytest tests/ -v
# Web dashboard: pytest tests/ --evoid-webui
```

## Configuration

```python
from evoid.config import config

app = config(
    service={"name": "my-api"},
    runtime={"adapter": "asgi", "port": 8000},
    engines={"storage": "redis"},
)
```

## CLI

| Command | Description |
|---------|-------------|
| `evo init <name>` | Create project |
| `evo service new <name>` | Add service |
| `evo service run <name>` | Run service |
| `evo run` | Run all |
| `evo install <pkg>` | Install dependency |
| `evo plug install <name>` | Install plugin |
| `evo plug search <query>` | Search plugins |

## AI agent integration

```python
from evoid import exportschemas
from evoid.adapters.mcp import create_mcp_server

# Export schemas for AI discovery
schemas = export_schemas()

# Create MCP server
server = create_mcp_server("my-api")
```

## Gotchas

**PostgreSQL dialect:** Connection URL must use `postgresql+asyncpg://`. Plain `postgresql://` fails at connection time.

**SQLite missing health():** `evoid-sqlite` doesn't implement `health()`. SmartStorage checks `hasattr()` defensively, but direct callers get `AttributeError`.

**Scylla async overhead:** `cassandra-driver` is synchronous. Every operation goes through `run_in_executor` → thread pool. Use PostgreSQL for write-heavy workloads.

**SmartStorage lazy resolution:** Backends resolve on first `write`/`read`/`delete`, not at construction. Missing backend = runtime error at first use.

**Auth default provider:** No `auth_provider` in metadata → looks for `"default"`. Register your provider as `"default"` or pass the name explicitly.

**DI sync vs async:** Services with routing rules raise `ValueError` on sync `resolve()`. Use `await di.resolve_async("service", ctx)`.

**Redis prefix:** Always set `prefix="evoid:"` when sharing Redis. Without it, keys collide.

**StorageEngine write param:** Protocol says `data`, SQLite says `value`. Works at runtime (kwargs absorb it), but type-checkers may flag it.

## See also

- [Contracts reference](references/contracts.md) — full protocol signatures
- [Plugin recipes](references/plugins.md) — copy-paste patterns for each plugin
- [Troubleshooting](references/troubleshooting.md) — common errors and fixes
