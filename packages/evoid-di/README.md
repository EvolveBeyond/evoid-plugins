<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-di?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-di?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-di?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-di</h1>

<p align="center">
  <strong>Dependency injection engine for EVOID — simple, scoped, or context-aware</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#three-levels">Three Levels</a> •
  <a href="#api">API</a> •
  <a href="#installation">Install</a> •
  <a href="https://evolvebeyond.github.io/EVOID/">Docs</a>
</p>

---

## Quick Start

```bash
pip install evoid-di
```

```python
from evoid_di import DIEngine

di = DIEngine()

# Register factories
di.register("db", lambda: create_db("app.db"))
di.register("cache", lambda: create_cache("redis://localhost"))

# Resolve
db = di.resolve("db")
cache = di.resolve("cache")
```

## Three Levels

### Level 1: Simple

Name-based resolution. One factory, one instance.

```python
from evoid_di import DIEngine

di = DIEngine()
di.register("db", lambda: create_db("app.db"))
db = di.resolve("db")
```

### Level 2: Scoped

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

### Level 3: Context-Aware

Route implementations based on Intent level, metadata, or user.

```python
from evoid_di import DIEngine, Rule, RuleSet

di = DIEngine(
    rules_config={
        "notifier": {
            "scope": "singleton",
            "default": "memory_notifier",
            "rules": [
                {
                    "when": {"level": "CRITICAL"},
                    "then": "email_sender",
                },
                {
                    "when": {"level": "STANDARD"},
                    "then": "slack_sender",
                },
            ],
        }
    },
    implementations={
        "memory_notifier": lambda: MemoryNotifier(),
        "email_sender": lambda: EmailSender(),
        "slack_sender": lambda: SlackSender(),
    },
)

# Resolves based on context
notifier = await di.resolve_async("notifier", ctx)
```

## Configuration

### TOML

```toml
[engines]
di = "di"

[engines.di.notifier]
scope = "singleton"
default = "memory"

[engines.di.notifier.critical]
when = { level = "CRITICAL" }
then = "email_sender"
```

## API

### `DIEngine`

| Method | Tier | Signature | Description |
|--------|------|-----------|-------------|
| `register` | L1/L2 | `register(name, factory, scope="transient")` | Register a factory |
| `resolve` | L1/L2 | `resolve(name, user_id=None)` | Synchronous resolve |
| `resolve_async` | L3 | `async resolve_async(name, ctx, extra=None)` | Async resolve with context |
| `inject` | All | `inject(ctx, service_name, key=None)` | Resolve and inject into `ctx.deps` |
| `clear` | All | `clear()` | Purge all cached instances |
| `list_services` | All | `list_services()` | List registered service names |

### Scopes

| Scope | Behavior |
|-------|----------|
| `singleton` | One instance, shared everywhere |
| `transient` | New instance on every resolve |
| `per_user` | One instance per `user_id` |

## Dependencies

- `evoid>=0.4.0` (no extra dependencies)

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
