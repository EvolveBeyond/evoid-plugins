<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-di?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-di?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-di?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-di</h1>

<p align="center">
  <strong>Dependency injection engine — Intent Handler system</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#intent-handler">Intent Handler</a> •
  <a href="#three-levels">Three Levels</a> •
  <a href="#api">API</a>
</p>

---

## Quick Start

```bash
uv add evoid-di
```

### Method 1: Intent Handler (Recommended)

```python
from evoid_di import register_handlers

# Register DI engine as Intent handlers
register_handlers(
    rules={"notifier": {"default": "memory"}},
    implementations={"memory": lambda: MemoryNotifier()},
)
```

### Method 2: Direct API

```python
from evoid_di import DIEngine

di = DIEngine()
di.register("db", lambda: create_db("app.db"))
db = di.resolve("db")
```

---

## Intent Handler

evoid-di registers dependency resolution as Intent handlers.

### Three Levels

#### Level 1: Simple

Name-based resolution. One factory, one instance.

```python
from evoid_di import DIEngine

di = DIEngine()
di.register("db", lambda: create_db("app.db"))
db = di.resolve("db")
```

#### Level 2: Scoped

Control instance lifetime per dependency.

```python
di = DIEngine()

# Singleton — one instance for everyone
di.register("db", create_db, scope="singleton")

# Transient — new instance every time
di.register("logger", create_logger, scope="transient")

# Per-user — one instance per user
di.register("session", create_session, scope="per_user")

db = di.resolve("db")
session = di.resolve("session", user_id="user_123")
```

#### Level 3: Context-Aware

Route implementations based on Intent level, metadata, or user.

```python
from evoid_di import DIEngine, Rule, RuleSet

di = DIEngine(
    rules_config={
        "notifier": {
            "scope": "singleton",
            "default": "memory_notifier",
            "rules": [
                {"when": {"level": "CRITICAL"}, "then": "email_sender"},
                {"when": {"level": "STANDARD"}, "then": "slack_sender"},
            ],
        }
    },
    implementations={
        "memory_notifier": lambda: MemoryNotifier(),
        "email_sender": lambda: EmailSender(),
        "slack_sender": lambda: SlackSender(),
    },
)

notifier = await di.resolve_async("notifier", ctx)
```

---

## Configuration

### TOML

```toml
[engines]
di = "di"

[engines.options.di]
rules = {"notifier": {"default": "memory"}}
implementations = {"memory": "my_module:create_notifier"}
```

---

## API

### `register_handlers(rules, implementations, services)`

Register DI engine as Intent handlers.

### DIEngine Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `register` | `register(name, factory, scope="singleton")` | Register a factory |
| `resolve` | `resolve(name, user_id=None)` | Synchronous resolve |
| `resolve_async` | `async resolve_async(name, ctx)` | Async resolve with context |
| `inject` | `inject(ctx, service_name, key=None)` | Resolve and inject into `ctx.deps` |
| `set_fallback` | `set_fallback(name, fallbacks)` | Define fallback chain |
| `set_health_check` | `set_health_check(name, check_fn)` | Register health check |
| `resolve_with_fallback` | `resolve_with_fallback(name)` | Resolve with auto-fallback |
| `resolve_any` | `resolve_any(*names)` | Resolve first available |
| `set_cluster_registry` | `set_cluster_registry(registry)` | Connect to cluster |
| `has` | `has(name)` | Check if service exists |
| `register_many` | `register_many(services)` | Batch registration |
| `resolve_or_none` | `resolve_or_none(name)` | Safe resolve (no exception) |

### Scopes

| Scope | Behavior |
|-------|----------|
| `singleton` | One instance, shared everywhere |
| `transient` | New instance on every resolve |
| `per_user` | One instance per `user_id` |

### Fault Tolerance

```python
from evoid_di import di

# Fallback chain
di.set_fallback("storage.postgresql", ["storage.sqlite", "cache.redis"])

# Health check
di.set_health_check("cache.redis", lambda: redis.ping())

# Auto-fallback (never crashes)
storage = di.resolve_with_fallback("storage.postgresql")
# Tries: postgresql → sqlite → redis → cluster → None

# Resolve first available
cache = di.resolve_any("cache.redis", "cache.memory")
```

### Cluster Integration

```python
from evoid_cluster import ClusterBridge

bridge = ClusterBridge(config)
await bridge.start()

# Connect registry to DI
di.set_cluster_registry(bridge._registry)

# Remote services become fallbacks
storage = di.resolve("storage.postgresql")
# If not local, checks cluster peers
```

---

## Dependencies

- `evoid>=0.4.0`

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
