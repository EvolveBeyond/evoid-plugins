<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-redis?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-redis?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-redis?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-redis</h1>

<p align="center">
  <strong>Redis cache engine for EVOID — Intent Handler system</strong>
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
pip install evoid-redis
```

### Method 1: Intent Handler (Recommended)

```python
from evoid_redis import register_handlers
from evoid.core.cache import cache_get, cache_set, cache_delete

# Register Redis as cache handler
register_handlers(url="redis://localhost:6379", prefix="myapp:")

# Use high-level API — goes through Intent pipeline
await cache_set("session:abc", {"user": "Alice"}, ttl=300)
data = await cache_get("session:abc")
await cache_delete("session:abc")
```

### Method 2: Direct API

```python
from evoid_redis import create_cache

cache = create_cache("redis://localhost:6379", prefix="myapp:")
await cache.set("key", {"data": "value"}, ttl=300)
data = await cache.get("key")
```

---

## Intent Handler

evoid-redis registers these Intent handlers:

| Intent | Handler | Description |
|--------|---------|-------------|
| `cache.get` | `handle_get` | Get value from Redis |
| `cache.set` | `handle_set` | Set value with optional TTL |
| `cache.delete` | `handle_delete` | Delete key |
| `cache.exists` | `handle_exists` | Check key existence |
| `cache.health` | `handle_health` | Ping Redis server |

### How it works

1. `register_handlers()` registers Intent handlers for cache operations
2. `cache_get()` / `cache_set()` create Intents and execute through pipeline
3. Pipeline routes to Redis handler
4. Handler connects to Redis and performs operation

---

## Configuration

### TOML

```toml
[engines]
cache = "redis"

[engines.options.redis]
url = "redis://localhost:6379"
prefix = "myapp:"
```

### Python

```python
from evoid.config import config

app = config(
    engines={
        "cache": "redis",
        "options": {
            "redis": {
                "url": "redis://prod:6379",
                "prefix": "production:",
            },
        },
    },
)
```

---

## API

### `register_handlers(url, prefix)`

Register Redis as Intent handlers.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | `redis://localhost:6379` | Redis connection URL |
| `prefix` | `str` | `evoid:` | Key prefix |

### `create_cache(url, prefix) -> RedisCache`

Factory function for direct API access.

### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `get` | `async get(key: str)` | `Any \| None` | Get value (auto JSON decode) |
| `set` | `async set(key: str, value: Any, ttl: int \| None)` | `bool` | Set value with optional TTL |
| `delete` | `async delete(key: str)` | `bool` | Delete key |
| `exists` | `async exists(key: str)` | `bool` | Check key exists |
| `health` | `async health()` | `bool` | Ping Redis |

---

## Dependencies

- `evoid>=0.4.0`
- `redis[hiredis]>=5.0.0`

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
