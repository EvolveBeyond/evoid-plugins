"""Shared contracts for EVOID plugins.

All storage/cache/logger plugins implement these protocols.
This ensures SmartStorage and other routing engines can work with any backend.
"""

from __future__ import annotations

from typing import Any, Protocol


class StorageEngine(Protocol):
    """Contract for storage backends (SQLite, PostgreSQL, ScyllaDB, etc.)."""

    async def write(self, key: str, data: dict[str, Any], **kwargs) -> bool: ...

    async def read(self, key: str, **kwargs) -> Any | None: ...

    async def delete(self, key: str, **kwargs) -> bool: ...

    async def health(self) -> bool: ...


class CacheEngine(Protocol):
    """Contract for cache backends (Redis, Memory, etc.)."""

    async def get(self, key: str) -> Any | None: ...

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool: ...

    async def delete(self, key: str) -> bool: ...

    async def exists(self, key: str) -> bool: ...

    async def health(self) -> bool: ...


class LoggerEngine(Protocol):
    """Contract for logging backends (Loguru, stdlib, etc.)."""

    def info(self, msg: str, **kwargs) -> None: ...

    def warning(self, msg: str, **kwargs) -> None: ...

    def error(self, msg: str, **kwargs) -> None: ...

    def debug(self, msg: str, **kwargs) -> None: ...
