"""SmartStorage engine — routes data to backends based on type, level, metadata, user."""

from __future__ import annotations

from typing import Any

from .schema_enforcer import SchemaEnforcer


class SmartStorage:
    """Multi-backend storage with intelligent routing.

    Routing priority:
    1. intent.metadata["storage_preference"] — explicit override
    2. user_connections[user_id] — multi-tenant routing
    3. mapping[data_type] — default mapping from config

    Supports multi-write: "memory+redis" writes to both backends.
    """

    def __init__(self, config: dict):
        self.mapping: dict[str, str] = config.get("mapping", {})
        self.schemas: dict[str, list[str]] = config.get("schemas", {})
        self.user_connections: dict[str, str] = config.get("user_connections", {})
        self.level_routing: dict[str, str] = config.get("level_routing", {})
        self._engines: dict[str, Any] = {}
        self._schema_enforcer = SchemaEnforcer(self.schemas)
        self._setup_complete = False

    async def setup(self):
        """Initialize all backend engines from DI.

        Resolves backends like 'storage.sqlite', 'cache.redis', etc.
        Multi-write: 'memory+redis' resolves both from DI.
        """
        if self._setup_complete:
            return

        from evoid_di import di

        engine_names = set(self.mapping.values())
        for target in self.user_connections.values():
            engine_names.add(target)

        for name in engine_names:
            if "+" in name:
                parts = name.split("+")
                self._engines[name] = [di.resolve(p) for p in parts]
            else:
                self._engines[name] = di.resolve(name)

        self._setup_complete = True

    async def write(
        self,
        data_type: str,
        data: dict[str, Any],
        intent=None,
        user_id: str | None = None,
    ) -> bool:
        """Store data. Routes to the correct backend based on type/level/metadata/user."""
        await self.setup()

        engine_name = self._resolve_engine(data_type, intent, user_id)
        if not engine_name:
            raise ValueError(f"No engine mapped for data_type '{data_type}'")

        data = self._schema_enforcer.apply(data_type, data)

        targets = self._engines.get(engine_name, [])
        if not isinstance(targets, list):
            targets = [targets]

        for eng in targets:
            await eng.write(data_type, data)
        return True

    async def read(
        self,
        data_type: str,
        query: dict[str, Any] | None = None,
        intent=None,
        user_id: str | None = None,
    ) -> Any:
        """Read data from the primary backend for this data type."""
        await self.setup()

        engine_name = self._resolve_engine(data_type, intent, user_id)
        if not engine_name:
            return None

        target = self._engines.get(engine_name)
        if isinstance(target, list):
            target = target[0]
        if target is None:
            return None

        return await target.read(data_type, query or {})

    async def delete(
        self,
        data_type: str,
        query: dict[str, Any] | None = None,
        intent=None,
        user_id: str | None = None,
    ) -> bool:
        """Delete data from all backends for this data type."""
        await self.setup()

        engine_name = self._resolve_engine(data_type, intent, user_id)
        if not engine_name:
            return False

        targets = self._engines.get(engine_name, [])
        if not isinstance(targets, list):
            targets = [targets]

        for eng in targets:
            await eng.delete(data_type, query or {})
        return True

    async def health(self) -> bool:
        """Check health of all backends."""
        await self.setup()

        for target in self._engines.values():
            if isinstance(target, list):
                for eng in target:
                    if hasattr(eng, "health") and not await eng.health():
                        return False
            else:
                if hasattr(target, "health") and not await target.health():
                    return False
        return True

    def _resolve_engine(
        self,
        data_type: str,
        intent=None,
        user_id: str | None = None,
    ) -> str | None:
        """Resolve which backend engine to use.

        Priority:
        1. intent.metadata["storage_preference"] — explicit override
        2. user_connections[user_id] — multi-tenant
        3. level_routing[intent.level] — level-based routing
        4. mapping[data_type] — default mapping
        """
        # 1. Explicit metadata override
        if intent and hasattr(intent, "metadata"):
            pref = intent.metadata.get("storage_preference")
            if pref:
                return pref

        # 2. User-specific connection
        if user_id and user_id in self.user_connections:
            return self.user_connections[user_id]

        # 3. Level-based routing
        if intent and hasattr(intent, "level") and self.level_routing:
            level_name = intent.level.value if hasattr(intent.level, "value") else str(intent.level)
            if level_name in self.level_routing:
                return self.level_routing[level_name]

        # 4. Default mapping by data type
        return self.mapping.get(data_type)
