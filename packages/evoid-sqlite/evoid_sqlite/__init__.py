"""SQLite Storage Engine for EVOID.

IOP: Plugin registry pattern — register, resolve, use.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evoid.engines.plugin import register


# Plugin manifest
MANIFEST = {
    "name": "evoid-sqlite",
    "version": "0.1.0",
    "type": "engine",
    "description": "SQLite storage engine for EVOID",
    "entry_point": "evoid_sqlite:register_plugin",
    "dependencies": ["aiosqlite>=0.20.0"],
    "evoid_version": ">=0.4.0",
    "tags": ["storage", "sqlite", "database"],
}


class SQLiteStorage:
    """SQLite storage engine — async, file-based."""

    def __init__(self, db_path: str = "evoid.db"):
        self.db_path = db_path
        self._conn = None

    async def connect(self):
        import aiosqlite
        self._conn = await aiosqlite.connect(self.db_path)
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                namespace TEXT DEFAULT 'default'
            )
        """)
        await self._conn.commit()

    async def close(self):
        if self._conn:
            await self._conn.close()

    async def read(self, key: str, **kwargs) -> Any | None:
        namespace = kwargs.get("namespace", "default")
        if not self._conn:
            await self.connect()
        cursor = await self._conn.execute(
            "SELECT value FROM kv_store WHERE key = ? AND namespace = ?",
            (key, namespace),
        )
        row = await cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    async def write(self, key: str, data: dict[str, Any], **kwargs) -> bool:
        namespace = kwargs.get("namespace", "default")
        if not self._conn:
            await self.connect()
        await self._conn.execute(
            "INSERT OR REPLACE INTO kv_store (key, value, namespace) VALUES (?, ?, ?)",
            (key, json.dumps(data), namespace),
        )
        await self._conn.commit()
        return True

    async def delete(self, key: str, **kwargs) -> bool:
        namespace = kwargs.get("namespace", "default")
        if not self._conn:
            await self.connect()
        cursor = await self._conn.execute(
            "DELETE FROM kv_store WHERE key = ? AND namespace = ?",
            (key, namespace),
        )
        await self._conn.commit()
        return cursor.rowcount > 0

    async def health(self) -> bool:
        try:
            if not self._conn:
                await self.connect()
            await self._conn.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def list_keys(self, namespace: str = "default") -> list[str]:
        if not self._conn:
            await self.connect()
        cursor = await self._conn.execute(
            "SELECT key FROM kv_store WHERE namespace = ?",
            (namespace,),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


def create_storage(db_path: str = "evoid.db") -> SQLiteStorage:
    """Factory: create a SQLite storage instance."""
    return SQLiteStorage(db_path=db_path)


def register_plugin():
    """Called when the plugin is loaded."""
    register(
        name="sqlite",
        type="engine",
        factory=create_storage,
        version="0.1.0",
        description="SQLite storage engine for EVOID",
    )
