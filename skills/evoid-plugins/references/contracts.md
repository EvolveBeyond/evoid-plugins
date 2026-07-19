# EVOID Contracts Reference

Full protocol signatures, utility functions, and the plugin registration system.

## StorageEngine Protocol

```python
from typing import Any, Protocol
from evoid_base.contracts import StorageEngine

class StorageEngine(Protocol):
    async def write(self, key: str, data: Any, **kwargs) -> bool:
        """Write data to storage. Returns True on success."""
        ...

    async def read(self, key: str, **kwargs) -> Any | None:
        """Read data from storage. Returns None if not found."""
        ...

    async def delete(self, key: str, **kwargs) -> bool:
        """Delete data from storage. Returns True on success."""
        ...

    async def health(self) -> bool:
        """Check if the backend is reachable."""
        ...
```

All backends accept a `namespace` kwarg (default: `"default"`) for logical partitioning within a single backend instance.

## CacheEngine Protocol

```python
from typing import Any, Protocol
from evoid_base.contracts import CacheEngine

class CacheEngine(Protocol):
    async def get(self, key: str) -> Any | None:
        """Get a cached value. Returns None if expired or missing."""
        ...

    async def set(self, key: str, value: Any, ttl: float | None = None) -> bool:
        """Set a cached value with optional TTL in seconds."""
        ...

    async def delete(self, key: str) -> bool:
        """Delete a cached value."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        ...

    async def health(self) -> bool:
        """Check if the cache backend is reachable."""
        ...
```

CacheEngine does NOT use namespaces. Use key prefixes instead (e.g., `create_cache(prefix="evoid:")`).

## LoggerEngine Protocol

```python
from typing import Protocol
from evoid_base.contracts import LoggerEngine

class LoggerEngine(Protocol):
    def info(self, msg: str, **kwargs) -> None: ...
    def warning(self, msg: str, **kwargs) -> None: ...
    def error(self, msg: str, **kwargs) -> None: ...
    def debug(self, msg: str, **kwargs) -> None: ...
```

LoggerEngine is synchronous. Do not make logging calls async.

## Utility functions

### resolve_engine

```python
from evoid_base.utils import resolve_engine

# Fetch a registered engine by name
storage = resolve_engine("sqlite", "storage")
cache = resolve_engine("redis", "cache")
```

### inject_deps

```python
from evoid_base.utils import inject_deps

# Populate ctx.deps from named engines
await inject_deps(ctx, {"storage": "sqlite", "cache": "redis"})
# ctx.deps.storage and ctx.deps.cache are now populated
```

## Plugin registration system

Every EVOID plugin must export:

```python
MANIFEST = {
    "name": "plugin-name",          # Must match pip package name
    "version": "1.0.0",             # Semver
    "type": "storage|cache|logger", # Engine type
    "description": "Short description",
    "entry_point": "module:register_plugin",  # Called by EVOID loader
    "dependencies": [],              # Required pip packages (optional)
    "evoid_version": ">=0.4.0",    # Minimum EVOID version
    "tags": ["storage", "custom"],  # For discovery
}

def register_plugin():
    from evoid.engines.plugin import register
    register("plugin-name", "storage", MyEngine, version="1.0.0")
```

The `entry_point` string is a `module:function` path. The EVOID loader imports the module and calls the function at startup.

## MANIFEST field reference

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| name | Yes | str | Must match package name on PyPI |
| version | Yes | str | Semver format |
| type | Yes | str | One of: `storage`, `cache`, `logger` |
| description | Yes | str | Short description for plugin discovery |
| entry_point | Yes | str | `module:function` path to registration function |
| dependencies | No | list[str] | Required pip packages |
| evoid_version | Yes | str | Minimum EVOID version constraint |
| tags | No | list[str] | Tags for plugin discovery |
