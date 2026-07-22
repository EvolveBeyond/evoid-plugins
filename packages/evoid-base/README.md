<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-base?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-base?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-base?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-base</h1>

<p align="center">
  <strong>Shared contracts for EVOID plugins — Intent Handler system</strong>
</p>

<p align="center">
  <a href="#contracts">Contracts</a> •
  <a href="#writing-a-plugin">Write Plugin</a> •
  <a href="#validation">Validation</a>
</p>

---

## What is this?

`evoid-base` defines the interface contracts that all EVOID plugins implement. You don't install this directly — it comes with `evoid`. But if you're writing a custom plugin, these are the protocols you implement.

---

## Contracts

### StorageEngine

```python
from evoid_base.contracts import StorageEngine

class StorageEngine(Protocol):
    async def read(self, key: str) -> Any | None: ...
    async def write(self, key: str, value: Any) -> bool: ...
    async def delete(self, key: str) -> bool: ...
    async def health(self) -> bool: ...
```

### CacheEngine

```python
from evoid_base.contracts import CacheEngine

class CacheEngine(Protocol):
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool: ...
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

---

## Writing a Plugin

### Step 1: Implement handlers

```python
# my_storage/__init__.py
from evoid.core import register as register_intent, register_processor
from evoid.core.intents import STORAGE_READ, STORAGE_WRITE, STORAGE_DELETE, STORAGE_HEALTH

async def handle_read(ctx):
    key = ctx.intent.metadata.get("key")
    # Your storage logic here
    return value

async def handle_write(ctx):
    key = ctx.intent.metadata.get("key")
    value = ctx.intent.metadata.get("value")
    # Your storage logic here
    return True

async def handle_delete(ctx):
    key = ctx.intent.metadata.get("key")
    # Your storage logic here
    return True

async def handle_health(ctx):
    return True
```

### Step 2: Register handlers

```python
def register_handlers(db_path: str = "my.db"):
    """Register storage as Intent handlers."""
    register_intent(STORAGE_READ)
    register_intent(STORAGE_WRITE)
    register_intent(STORAGE_DELETE)
    register_intent(STORAGE_HEALTH)
    register_processor("storage.read", handle_read)
    register_processor("storage.write", handle_write)
    register_processor("storage.delete", handle_delete)
    register_processor("storage.health", handle_health)
```

### Step 3: Add validation

```python
from evoid.engines.validator import validate_plugin

def register_handlers():
    handlers = {
        "storage.read": handle_read,
        "storage.write": handle_write,
        "storage.delete": handle_delete,
        "storage.health": handle_health,
    }

    result = validate_plugin("storage", handlers)
    if not result.valid:
        raise ValueError(f"Plugin validation failed: {result.errors}")

    # Register validated handlers...
```

---

## Validation

evoid-base provides `validate_plugin()` to check your plugin before registration:

```python
from evoid.engines.validator import validate_plugin

result = validate_plugin("storage", handlers)
assert result.valid, f"Errors: {result.errors}"
```

Checks:
- All required handlers are provided
- Handlers are async callables
- Handlers accept `ctx` as first parameter

---

## Installation

```bash
uv add evoid-base
```

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Standard](https://evolvebeyond.github.io/EVOID/learn/plugin-standard/)

## License

MIT
