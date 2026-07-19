# EVOID Contracts & Core API Reference

## Intent

```python
from evoid import Intent, Level

intent = Intent(
    name="get_user",           # str — unique identifier (required)
    level=Level.STANDARD,      # Level — ephemeral/standard/critical
    metadata={"method": "GET"},# dict — arbitrary data for processors
    timeout=10.0,              # float | None — max seconds
    priority=0,                # int — execution order (higher first)
)
```

Intent is a **frozen dataclass**. Once created, immutable.

### Level enum

```python
from evoid import Level

Level.EPHEMERAL   # → pipeline: [validate], timeout: 5s
Level.STANDARD    # → pipeline: [validate, authorize], timeout: 10s
Level.CRITICAL    # → pipeline: [validate, authorize, audit, protect], timeout: 30s
```

## Context

```python
from evoid.core import Context

ctx.intent      # Intent — the intent being processed
ctx.state       # dict — shared mutable state between processors
ctx.deps        # dict — injected dependencies (engines, services)
ctx.metadata    # dict — extra metadata (request params, body)
ctx.errors      # list[Exception] — accumulated non-fatal errors
ctx.id          # str — unique context ID (auto-generated)
```

### Forking contexts

```python
from evoid.core import fork

child = fork(ctx)
# child has same intent + deps, copied state, parent_id in metadata
```

## Result

```python
from evoid import execute

result = await execute(intent)

result.success     # bool
result.value       # Any — return value from last processor
result.error       # Exception | None
result.processors  # tuple[str, ...] — processor names that ran
result.duration    # float — seconds
```

## Processor registration

```python
from evoid import register_processor

async def my_processor(ctx: Context) -> dict:
    return {"status": "ok"}

register_processor("my_processor", my_processor)
```

Built-in processors: `intent_extractor`, `schema_validator`, `auth_checker`, `rate_limiter`, `circuit_breaker`, `logger_processor`.

## Pipeline extension

```python
from evoid.core.extend import (
    add_intent_with_pipeline,
    replace_pipeline,
    before,
    after,
    before_processor,
    after_processor,
    remove_processor,
    list_overrides,
    clear_overrides,
    get_pipeline_config,
)
```

## Execution

```python
from evoid import execute, all_intents

# Execute an intent
result = await execute(intent)

# List all registered intents
intents = all_intents()
for name, intent in intents.items():
    print(f"{name} [{intent.level.value}]")
```

## StorageEngine Protocol

```python
from typing import Any, Protocol
from evoid_base.contracts import StorageEngine

class StorageEngine(Protocol):
    async def write(self, key: str, data: Any, **kwargs) -> bool: ...
    async def read(self, key: str, **kwargs) -> Any | None: ...
    async def delete(self, key: str, **kwargs) -> bool: ...
    async def health(self) -> bool: ...
```

## CacheEngine Protocol

```python
from evoid_base.contracts import CacheEngine

class CacheEngine(Protocol):
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: float | None = None) -> bool: ...
    async def delete(self, key: str) -> bool: ...
    async def exists(self, key: str) -> bool: ...
    async def health(self) -> bool: ...
```

## LoggerEngine Protocol

```python
from evoid_base.contracts import LoggerEngine

class LoggerEngine(Protocol):
    def info(self, msg: str, **kwargs) -> None: ...
    def warning(self, msg: str, **kwargs) -> None: ...
    def error(self, msg: str, **kwargs) -> None: ...
    def debug(self, msg: str, **kwargs) -> None: ...
```

## Plugin registration

```python
from evoid.engines.plugin import register

# Register an engine
register("my-engine", "storage", MyStorage, version="1.0.0")

# Resolve a registered engine
from evoid_base.utils import resolve_engine
storage = resolve_engine("sqlite", "storage")

# Inject dependencies into context
from evoid_base.utils import inject_deps
await inject_deps(ctx, {"storage": "sqlite", "cache": "redis"})
```

## MANIFEST fields

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| name | Yes | str | Must match package name |
| version | Yes | str | Semver |
| type | Yes | str | `storage`, `cache`, or `logger` |
| description | Yes | str | Short description |
| entry_point | Yes | str | `module:function` path |
| dependencies | No | list[str] | Required pip packages |
| evoid_version | Yes | str | Minimum EVOID version |
| tags | No | list[str] | Discovery tags |

## Schema export (AI integration)

```python
from evoid import export_schemas
from evoid.adapters.mcp import create_mcp_server

# Export all intent schemas as JSON
schemas = export_schemas()

# Create MCP server for AI agents
server = create_mcp_server("my-api")
```
