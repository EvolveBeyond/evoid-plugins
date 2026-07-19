# Troubleshooting

Common errors and fixes in EVOID plugin projects.

## Plugin not loading

**Symptom:** Engine not found when calling `resolve_engine()`.

**Fix:** Verify the plugin is installed and the entry point is correct.

```bash
pip list | grep evoid
```

Check that `MANIFEST["entry_point"]` matches an importable `module:function` path. The module must be importable from the installed package.

## Connection refused (PostgreSQL)

**Symptom:** `ConnectionRefusedError` when first calling storage operations.

**Fix:** Connections are lazy — they open on first use, not at `create_storage()`. Verify:
1. PostgreSQL is running and accepting connections
2. Connection URL uses `postgresql+asyncpg://` prefix (not plain `postgresql://`)
3. Database and user exist

```python
# Wrong — will fail at first write
storage = create_storage(url="postgresql://user:pass@localhost/evoid")

# Correct
storage = create_storage(url="postgresql+asyncpg://user:pass@localhost/evoid")
```

## AttributeError: health()

**Symptom:** `AttributeError: 'SQLiteStorage' object has no attribute 'health'`

**Fix:** `evoid-sqlite` doesn't implement `health()`. SmartStorage handles this defensively, but direct usage requires a wrapper:

```python
class SafeSQLite:
    def __init__(self, path):
        self._storage = create_storage(path)

    async def health(self):
        try:
            await self._storage.read("__health_check__")
            return True
        except Exception:
            return False

    def __getattr__(self, name):
        return getattr(self._storage, name)
```

## DI resolve() ValueError

**Symptom:** `ValueError: Service 'storage' has routing rules. Use resolve_async() instead.`

**Fix:** Services with routing rules must be resolved asynchronously:

```python
# Wrong — sync resolve with routing rules
svc = di.resolve("storage")

# Correct
svc = await di.resolve_async("storage", ctx)
```

## Auth: no provider found

**Symptom:** Authentication fails silently or raises about missing provider.

**Fix:** The `authenticate` processor looks for `metadata["auth_provider"]` first, then falls back to `"default"`. If you register only one provider, name it `"default"`:

```python
# This won't work unless you pass auth_provider="custom" in every intent
register_provider("custom", my_auth)

# This works as fallback
register_provider("default", my_auth)
```

## Redis key collisions

**Symptom:** Data appears corrupted or overwritten by another application.

**Fix:** Always set a prefix when sharing a Redis instance:

```python
# Bad — keys collide with other apps
cache = create_cache(url="redis://localhost:6379")

# Good — isolated key namespace
cache = create_cache(url="redis://localhost:6379", prefix="myapp:")
```

## SmartStorage: backend not found at runtime

**Symptom:** `PluginError: Engine 'scylla' not found` on first write/read.

**Fix:** SmartStorage resolves backends lazily. The error appears on first use, not at construction. Ensure the backend plugin is installed:

```bash
pip install evoid-scylla
```

## ScyllaDB: slow under high load

**Symptom:** Latency spikes with many concurrent operations.

**Cause:** `cassandra-driver` is synchronous. Every operation goes through `run_in_executor` → thread pool. This adds overhead compared to natively async drivers.

**Fix:** For write-heavy workloads, prefer PostgreSQL or Redis. Use Scylla for high-throughput reads where eventual consistency is acceptable.

## Namespace confusion

**Symptom:** Data not found despite being written.

**Fix:** Storage engines default to `namespace="default"`. If you write with a custom namespace, you must read with the same one:

```python
await storage.write("key", "value", namespace="custom")
result = await storage.read("key")  # → None (wrong namespace)
result = await storage.read("key", namespace="custom")  # → "value"
```

## Import errors after install

**Symptom:** `ModuleNotFoundError: No module named 'evoid_sqlite'`

**Fix:** EVOID plugins use underscores in Python imports but hyphens in pip:

```bash
pip install evoid-sqlite  # hyphen in pip name
```

```python
from evoid_sqlite import create_storage  # underscore in import
```
