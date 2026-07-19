# Troubleshooting

## Core EVOID

### Intent not executing

**Symptom:** `execute(intent)` returns nothing or raises "intent not found".

**Fix:** Ensure the intent is registered:

```python
from evoid import add_intent, all_intents

add_intent(MY_INTENT, handler)

# Verify registration
intents = all_intents()
assert "my_intent" in intents
```

For @route/@controller, registration is automatic via decorators.

### Pipeline timeout

**Symptom:** `Result.success = False`, `Result.error = TimeoutError`.

**Fix:** Default timeouts: ephemeral=5s, standard=10s, critical=30s. Override per-intent:

```python
intent = Intent(name="slow_op", level=Level.CRITICAL, timeout=60.0)
```

Or check which processor is slow — `result.processors` lists what ran before the timeout.

### Processor not found in pipeline

**Symptom:** Pipeline skips a processor silently.

**Fix:** Processor names must match exactly. Check registration:

```python
from evoid import register_processor
register_processor("my_proc", my_processor)
```

Then reference by name: `processors=["validate", "my_proc", "handler"]`.

### Context state not persisting between processors

**Symptom:** Processor B doesn't see data written by Processor A.

**Fix:** Ensure Processor A writes to `ctx.state`, not a local variable:

```python
# Wrong — local variable, lost after return
async def proc_a(ctx: Context) -> dict:
    data = {"key": "value"}
    return data

# Correct — write to shared state
async def proc_a(ctx: Context) -> dict:
    ctx.state["key"] = "value"
    return {"saved": True}
```

### @route decorator not creating intent

**Symptom:** Endpoint not responding.

**Fix:** Ensure the Service is created and the decorator is called:

```python
from evoid.web.route import Service, get

app = Service("my-api")  # Must be created

@get("/users/{id}")      # Decorator registers automatically
async def get_user(id: int) -> dict:
    return {"id": id}
```

## Plugins

### Plugin not loading

**Symptom:** Engine not found when calling `resolve_engine()`.

**Fix:** Verify installation and entry point:

```bash
pip list | grep evoid
```

Check `MANIFEST["entry_point"]` matches an importable `module:function` path.

### Connection refused (PostgreSQL)

**Symptom:** `ConnectionRefusedError` on first operation.

**Fix:** Connections are lazy. Verify:
1. PostgreSQL is running
2. URL uses `postgresql+asyncpg://` (not `postgresql://`)
3. Database and user exist

### AttributeError: health()

**Symptom:** `AttributeError: 'SQLiteStorage' has no attribute 'health'`

**Fix:** `evoid-sqlite` doesn't implement `health()`. SmartStorage handles this, but direct usage needs a wrapper:

```python
class SafeSQLite:
    def __init__(self, path):
        self._storage = create_storage(path)
    async def health(self):
        try:
            await self._storage.read("__health__")
            return True
        except Exception:
            return False
    def __getattr__(self, name):
        return getattr(self._storage, name)
```

### DI ValueError on sync resolve

**Symptom:** `ValueError: Service has routing rules. Use resolve_async() instead.`

**Fix:** Use async resolution for routed services:

```python
svc = await di.resolve_async("storage", ctx)
```

### Auth: no provider found

**Symptom:** Authentication fails silently.

**Fix:** Register as `"default"` or pass `auth_provider` in every intent's metadata:

```python
register_provider("default", my_auth)
```

### Redis key collisions

**Symptom:** Data corrupted or overwritten.

**Fix:** Always set prefix:

```python
cache = create_cache(url="redis://localhost:6379", prefix="myapp:")
```

### SmartStorage: backend not found at runtime

**Symptom:** `PluginError: Engine 'scylla' not found` on first use.

**Fix:** SmartStorage resolves lazily. Install the backend:

```bash
pip install evoid-scylla
```

### Namespace confusion

**Symptom:** Data not found despite being written.

**Fix:** Default namespace is `"default"`. Match namespaces on read/write:

```python
await storage.write("key", "value", namespace="custom")
result = await storage.read("key", namespace="custom")  # Must match
```

### Import errors

**Symptom:** `ModuleNotFoundError: No module named 'evoid_sqlite'`

**Fix:** Pip uses hyphens, Python uses underscores:

```bash
pip install evoid-sqlite      # hyphen
```
```python
from evoid_sqlite import ...  # underscore
```
