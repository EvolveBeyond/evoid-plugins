"""ScyllaDB/Cassandra Storage Engine for EVOID.

ScyllaDB is wire-compatible with Cassandra. This plugin works with both.
Uses cassandra-driver for async operations.

IOP: Plugin registry pattern — register, resolve, use.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from evoid.engines.plugin import register

MANIFEST = {
    "name": "evoid-scylla",
    "version": "0.1.0",
    "type": "engine",
    "description": "ScyllaDB/Cassandra storage engine for EVOID",
    "entry_point": "evoid_scylla:register_plugin",
    "dependencies": ["cassandra-driver>=3.29.0"],
    "evoid_version": ">=0.4.0",
    "tags": ["storage", "scylla", "cassandra", "nosql"],
}


class ScyllaStorage:
    """ScyllaDB/Cassandra-backed storage engine."""

    def __init__(
        self,
        contact_points: list[str] | None = None,
        port: int = 9042,
        keyspace: str = "evoid",
        protocol_version: int = 4,
    ):
        self.contact_points = contact_points or ["127.0.0.1"]
        self.port = port
        self.keyspace = keyspace
        self.protocol_version = protocol_version
        self._session = None

    async def _setup(self):
        if self._session is not None:
            return

        from cassandra.cluster import Cluster
        from cassandra.policies import DCAwareRoundRobinPolicy

        loop = asyncio.get_running_loop()

        def _connect():
            cluster = Cluster(
                contact_points=self.contact_points,
                port=self.port,
                protocol_version=self.protocol_version,
            )
            session = cluster.connect()
            session.set_keyspace(self.keyspace)
            return session

        self._session = await loop.run_in_executor(None, _connect)

        # Create table if not exists
        await self._execute("""
            CREATE TABLE IF NOT EXISTS kv_store (
                namespace TEXT,
                key TEXT,
                value TEXT,
                PRIMARY KEY (namespace, key)
            )
        """)

    async def _execute(self, query: str, params: dict | None = None):
        if self._session is None:
            await self._setup()
        loop = asyncio.get_running_loop()
        if params:
            return await loop.run_in_executor(
                None, lambda: self._session.execute(query, params)
            )
        return await loop.run_in_executor(
            None, lambda: self._session.execute(query)
        )

    async def write(self, key: str, data: dict[str, Any], **kwargs) -> bool:
        namespace = kwargs.get("namespace", "default")
        await self._execute(
            "INSERT INTO kv_store (namespace, key, value) VALUES (%(ns)s, %(k)s, %(v)s)",
            {"ns": namespace, "k": key, "v": json.dumps(data)},
        )
        return True

    async def read(self, key: str, **kwargs) -> Any | None:
        namespace = kwargs.get("namespace", "default")
        result = await self._execute(
            "SELECT value FROM kv_store WHERE namespace = %(ns)s AND key = %(k)s",
            {"ns": namespace, "k": key},
        )
        row = result.one()
        if row and row.value:
            return json.loads(row.value)
        return None

    async def delete(self, key: str, **kwargs) -> bool:
        namespace = kwargs.get("namespace", "default")
        result = await self._execute(
            "DELETE FROM kv_store WHERE namespace = %(ns)s AND key = %(k)s",
            {"ns": namespace, "k": key},
        )
        return result is not None

    async def health(self) -> bool:
        try:
            await self._execute("SELECT release_version FROM system.local")
            return True
        except Exception:
            return False

    async def close(self):
        if self._session:
            self._session.shutdown()
            self._session = None


def create_storage(
    contact_points: list[str] | None = None,
    port: int = 9042,
    keyspace: str = "evoid",
) -> ScyllaStorage:
    """Factory: create a ScyllaDB/Cassandra storage instance."""
    return ScyllaStorage(contact_points=contact_points, port=port, keyspace=keyspace)


def register_plugin():
    """Called when the plugin is loaded."""
    register(
        name="scylla",
        type="engine",
        factory=create_storage,
        version="0.1.0",
        description="ScyllaDB/Cassandra storage engine for EVOID",
    )
