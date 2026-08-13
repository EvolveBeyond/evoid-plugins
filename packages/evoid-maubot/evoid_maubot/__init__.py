"""EvoidMaubot — Generic EVOID maubot adapter.

Bridge Matrix events to EVOID intents. Jitsi-specific commands live in
`matrix-jitsi-bot/services/matrixbot/` — this package is a framework
for building any maubot-based Matrix bot with EVOID IOP.

Usage:
    1. Install: pip install evoid-maubot
    2. Subclass EvoidMaubot and register intents
    3. Upload .mbp to maubot management interface
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from maubot import MessageEvent, Plugin

try:
    from evoid import Intent, Level, publish
    from evoid.native import create_service
    from evoid.native import on as evoid_on

    HAS_EVOID = True
except ImportError:
    HAS_EVOID = False

try:
    from evoid_smart_storage import SmartStorage
    from evoid_sqlite import create_storage

    HAS_STORAGE = True
except ImportError:
    HAS_STORAGE = False

if TYPE_CHECKING:
    from mautrix.util.config import BaseProxyConfig

from .commands import COMMAND_REGISTRY
from .commands import CommandDef as CommandDef
from .config import Config


class EvoidMaubot(Plugin):
    """Generic maubot plugin that bridges Matrix events to EVOID intents.

    Subclass this and override `_register_intents()` to register your
    own intents. The base class handles Matrix event conversion,
    command routing, and storage initialization.
    """

    config: BaseProxyConfig
    _evoid_service: Any = None
    _storage: Any = None
    _smart_storage: Any = None

    @classmethod
    def get_config_class(cls) -> type[BaseProxyConfig]:
        return Config

    async def start(self) -> None:
        """Initialize EVOID service and storage on plugin start."""
        self.log.info(f"Starting {self.config.get('service_name', 'bot')} ...")

        if not HAS_EVOID:
            self.log.warning("EVOID not installed. Install with: pip install evoid")
            return

        service_name = self.config.get("service_name", "maubot-bot")
        self._evoid_service = create_service(service_name)
        self._register_intents()

        await self._init_storage()
        self.log.info(f"EVOID service '{service_name}' initialized")

    async def stop(self) -> None:
        """Cleanup on plugin stop."""
        self.log.info("Stopping EVOID Maubot plugin...")
        if self._storage and hasattr(self._storage, "close"):
            await self._storage.close()
        self._evoid_service = None
        self._storage = None
        self._smart_storage = None

    async def _init_storage(self) -> None:
        """Initialize SQLite and Smart Storage if available."""
        if not HAS_STORAGE:
            self.log.warning("Storage plugins not installed. Data won't be persisted.")
            return

        db_path = self.config.get("storage.db_path", "bot.db")
        self._storage = create_storage(db_path)
        await self._storage.connect()
        self.log.info(f"SQLite storage connected: {db_path}")

        smart_config = self._build_smart_storage_config()
        if smart_config:
            self._smart_storage = SmartStorage(smart_config)
            try:
                from evoid_di import di
                di.register("storage.sqlite", lambda: self._storage, scope="singleton")
            except ImportError:
                pass

    def _build_smart_storage_config(self) -> dict | None:
        """Build smart storage config from plugin configuration.

        Override in subclasses to provide custom routing.
        """
        enable_smart = self.config.get("storage.enable_smart_routing", False)
        if not enable_smart:
            return None

        return {
            "mapping": self.config.get("storage.smart_mapping", {}),
            "schemas": self.config.get("storage.smart_schemas", {}),
        }

    def _register_intents(self) -> None:
        """Register intents with EVOID.

        Override in subclasses to register custom intents.
        The base implementation registers commands from COMMAND_REGISTRY.
        """
        if not self._evoid_service or not HAS_EVOID:
            return

        for cmd_name, cmd_def in COMMAND_REGISTRY.items():
            intent = Intent(
                name=f"{self._intent_prefix()}:{cmd_name}",
                level=Level.CRITICAL if cmd_def.requires_moderator else Level.STANDARD,
            )
            evoid_on(self._evoid_service, intent, self._make_handler(cmd_name))

    def _intent_prefix(self) -> str:
        """Override to change intent namespace prefix."""
        return "bot"

    def _make_handler(self, cmd_name: str):
        """Create an EVOID handler for a command.

        Override in subclasses for custom logic.
        """
        async def handler(intent: Intent) -> dict:
            return {
                "status": "executed",
                "command": cmd_name,
                "args": intent.metadata.get("args", {}),
                "room_id": intent.metadata.get("room_id", ""),
            }
        return handler

    def _make_intent(self, subcommand: str, cmd_def: CommandDef, args: dict, event: MessageEvent) -> Intent:
        """Build an Intent from a Matrix command.

        Override to customize intent metadata.
        """
        return Intent(
            name=f"{self._intent_prefix()}:{subcommand}",
            level=Level.CRITICAL if cmd_def.requires_moderator else Level.STANDARD,
            metadata={
                "command": subcommand,
                "args": args,
                "user": event.sender,
                "room_id": event.room_id,
            },
        )

    async def _on_command(self, event: MessageEvent, args: list[str]) -> None:
        """Handle a parsed command. Override for custom dispatch."""
        if not args:
            await event.reply(self._help_text())
            return

        subcommand = args[0].lower()
        if subcommand == "help":
            await event.reply(self._help_text())
            return

        cmd_def = COMMAND_REGISTRY.get(subcommand)
        if not cmd_def:
            await event.reply(f"Unknown command: {subcommand}\n\n" + self._help_text())
            return

        if cmd_def.requires_moderator and not self._is_moderator(event.sender):
            await event.reply(f"Command '{subcommand}' requires moderator privileges")
            return

        parsed_args = cmd_def.parse_args(args[1:])
        if parsed_args is None:
            await event.reply(f"Usage: !{self._command_prefix()}{subcommand} {cmd_def.usage}")
            return

        if not HAS_EVOID:
            await event.reply("EVOID runtime not available")
            return

        intent = self._make_intent(subcommand, cmd_def, parsed_args, event)
        result = await publish(intent, source="maubot")
        if result:
            response = cmd_def.format_response(result[0], parsed_args)
            await self._on_result(subcommand, parsed_args, event, result[0])
            await event.reply(response)
        else:
            await event.reply(f"Failed to execute: {subcommand}")

    def _command_prefix(self) -> str:
        """Override to change command prefix."""
        return self.config.get("command_prefix", "bot")

    async def _on_result(self, command: str, args: dict, event: MessageEvent, result: dict) -> None:
        """Hook for post-result processing. Override for persistence."""
        pass

    def _is_moderator(self, user_id: str) -> bool:
        """Check if user is allowed to run moderator commands."""
        whitelist = self.config.get("admin_whitelist", [])
        if not whitelist:
            return True
        return user_id in whitelist

    def _help_text(self) -> str:
        """Return help text grouped by category."""
        prefix = self._command_prefix()
        categories: dict[str, list[str]] = {}
        for name, cmd in COMMAND_REGISTRY.items():
            cat = cmd.category
            if cat not in categories:
                categories[cat] = []
            mod = " (mod)" if cmd.requires_moderator else ""
            categories[cat].append(f"  !{prefix} {name} {cmd.usage}{mod} — {cmd.description}")

        lines = [f"{prefix} Commands:"]
        for cat, cmds in categories.items():
            lines.append(f"\n{cat}:")
            lines.extend(cmds)
        lines.append("\nType !help <command> for details.")
        return "\n".join(lines)

    def register_command(self, name: str, cmd_def: CommandDef) -> None:
        """Register a command at runtime."""
        COMMAND_REGISTRY[name] = cmd_def

    def register_commands(self, commands: dict[str, CommandDef]) -> None:
        """Register multiple commands at runtime."""
        for name, cmd_def in commands.items():
            COMMAND_REGISTRY[name] = cmd_def


def register_plugin() -> type:
    """Entry point for EVOID plugin system."""
    return EvoidMaubot
