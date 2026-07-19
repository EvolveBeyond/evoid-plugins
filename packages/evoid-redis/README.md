<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-redis?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-redis?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-redis?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-redis</h1>

<p align="center">
  <strong>Redis cache engine for EVOID with TTL support</strong>
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
pip install evoid-redis
```

```python
from evoid_redis import create_cache

# Connect to Redis
cache = create_cache("redis://localhost:6379")

# Set with TTL (seconds)
await cache.set("session:abc", {"user": "Alice"}, ttl=300)

# Get
data = await cache.get("session:abc")
print(data)  # {"user": "Alice"}

# Check existence
exists = await cache.exists("session:abc")

# Delete
await cache.delete("session:abc")

# Health check
ok = await cache.health()
```

## Configuration

### TOML

```toml
[engines]
cache = "redis"

[engines.redis]
url = "redis://localhost:6379"
prefix = "evoid:"
```

### Python

```python
from evoid_redis import create_cache

cache = create_cache(
    url="redis://localhost:6379",
    prefix="myapp:",
)
```

## API

### `create_cache(url: str, prefix: str) -> RedisCache`

Factory function. Creates and returns a Redis cache engine.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | `redis://localhost:6379` | Redis connection URL |
| `prefix` | `str` | `evoid:` | Key prefix for all operations |

### Methods

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `get` | `async get(key: str)` | `Any \| None` | Get value (auto JSON decode) |
| `set` | `async set(key: str, value: Any, ttl: float \| None)` | `bool` | Set value with optional TTL |
| `delete` | `async delete(key: str)` | `bool` | Delete key |
| `exists` | `async exists(key: str)` | `bool` | Check key exists |
| `health` | `async health()` | `bool` | Ping Redis |
| `close` | `async close()` | `None` | Close connection |

## How it works

- Uses `redis[hiredis]` for async Redis access
- All keys are prefixed (default `evoid:`) to avoid collisions
- Values are JSON serialized/deserialized automatically
- TTL is handled via Redis `SETEX` command
- Health check pings the Redis server

## Dependencies

- `redis[hiredis]>=5.0.0`

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
