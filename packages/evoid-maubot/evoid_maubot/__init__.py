"""EVOID Maubot Plugin — Bridge Matrix events to EVOID intents.

Full Jitsi iframe command support via EVOID pipeline.
SQLite + Smart Storage for persistence.
Reference: https://jitsi.github.io/handbook/docs/dev-guide/dev-guide-iframe-commands/

Usage:
    1. Install: pip install evoid-maubot
    2. Upload .mbp to maubot management interface
    3. Configure Jitsi server details in plugin config
    4. Create instance with your Matrix client
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from maubot import Plugin, MessageEvent
from maubot.handlers import event
from mautrix.types import EventType

try:
    from evoid import Intent, Level, publish
    from evoid.native import create_service, on as evoid_on

    HAS_EVOID = True
except ImportError:
    HAS_EVOID = False

try:
    from evoid_sqlite import SQLiteStorage, create_storage
    from evoid_smart_storage import SmartStorage

    HAS_STORAGE = True
except ImportError:
    HAS_STORAGE = False

if TYPE_CHECKING:
    from mautrix.util.config import BaseProxyConfig

from .config import Config
from .commands import COMMAND_REGISTRY, CommandDef


class EvoidMaubot(Plugin):
    """Maubot plugin that bridges Matrix to Jitsi iframe commands via EVOID."""

    config: BaseProxyConfig
    _evoid_service: Any = None
    _storage: Any = None
    _smart_storage: Any = None

    @classmethod
    def get_config_class(cls) -> type[BaseProxyConfig]:
        return Config

    async def start(self) -> None:
        """Initialize EVOID service and storage on plugin start."""
        self.log.info("Starting EVOID Maubot plugin...")

        if not HAS_EVOID:
            self.log.warning("EVOID not installed. Install with: pip install evoid")
            return

        # Initialize EVOID service
        service_name = self.config["service_name"]
        self._evoid_service = create_service(service_name)
        self._register_jitsi_intents()

        # Initialize storage
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
        """Initialize SQLite and Smart Storage."""
        if not HAS_STORAGE:
            self.log.warning("Storage plugins not installed. Meetings won't be persisted.")
            return

        db_path = self.config.get("storage.db_path", "jitsi-bot.db")

        # SQLite backend
        self._storage = create_storage(db_path)
        await self._storage.connect()
        self.log.info(f"SQLite storage connected: {db_path}")

        # Smart Storage with routing config
        smart_config = {
            "mapping": {
                "meeting": "storage.sqlite",
                "user_preference": "storage.sqlite",
                "watch_party": "storage.sqlite",
                "moderator_log": "storage.sqlite",
            },
            "schemas": {
                "meeting": ["room_id", "room_name", "creator", "created_at", "url"],
                "user_preference": ["user_id", "key", "value"],
                "watch_party": ["room_id", "video_url", "content_type", "creator"],
            },
        }
        self._smart_storage = SmartStorage(smart_config)
        # Register SQLite in DI for smart_storage to resolve
        try:
            from evoid_di import di
            di.register("storage.sqlite", lambda: self._storage, scope="singleton")
        except ImportError:
            pass

    def _register_jitsi_intents(self) -> None:
        """Register all Jitsi command intents with EVOID."""
        if not self._evoid_service or not HAS_EVOID:
            return

        for cmd_name, cmd_def in COMMAND_REGISTRY.items():
            intent = Intent(
                name=f"jitsi:{cmd_name}",
                level=Level.CRITICAL if cmd_def.requires_moderator else Level.STANDARD,
            )
            evoid_on(self._evoid_service, intent, self._make_handler(cmd_name))

    def _make_handler(self, cmd_name: str):
        """Create an EVOID handler for a Jitsi command."""
        async def handler(intent: Intent) -> dict:
            return {
                "status": "executed",
                "command": cmd_name,
                "args": intent.metadata.get("args", {}),
                "room_id": intent.metadata.get("room_id", ""),
                "jitsi_command": COMMAND_REGISTRY[cmd_name].iframe_command,
            }
        return handler

    # ── Matrix Event Handlers ──────────────────────────────────────────────

    @event.on(EventType.ROOM_MESSAGE)
    async def on_message(self, event: MessageEvent) -> None:
        """Convert Matrix messages to EVOID intents."""
        if event.sender == self.client.mxid:
            return

        text = event.body or ""
        if not text.startswith("!"):
            return

        prefix = self.config["command_prefix"]
        parts = text[len("!"):].split()
        command_name = parts[0] if parts else ""

        if command_name == prefix:
            await self._handle_jitsi_command(event, parts[1:])

    async def _handle_jitsi_command(self, event: MessageEvent, args: list[str]) -> None:
        """Route Jitsi commands to EVOID intents."""
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

        # Check moderator permission
        if cmd_def.requires_moderator and not self._is_moderator(event.sender):
            await event.reply(f"Command '{subcommand}' requires moderator privileges")
            return

        # Parse arguments
        parsed_args = cmd_def.parse_args(args[1:])

        if parsed_args is None:
            await event.reply(f"Usage: !jitsi {subcommand} {cmd_def.usage}")
            return

        # Publish EVOID intent
        if not HAS_EVOID:
            await event.reply("EVOID runtime not available")
            return

        intent = Intent(
            name=f"jitsi:{subcommand}",
            level=Level.CRITICAL if cmd_def.requires_moderator else Level.STANDARD,
            metadata={
                "command": subcommand,
                "iframe_command": cmd_def.iframe_command,
                "args": parsed_args,
                "user": event.sender,
                "room_id": event.room_id,
                "server_url": self.config["jitsi.server_url"],
                "muc_domain": self.config["jitsi.muc_domain"],
            },
        )

        result = await publish(intent, source="maubot")
        if result:
            response = cmd_def.format_response(result[0], parsed_args)
            # Persist meeting data for create/watch commands
            await self._persist_meeting(subcommand, parsed_args, event, result[0])
            await event.reply(response)
        else:
            await event.reply(f"Failed to execute: {subcommand}")

    async def _persist_meeting(
        self, command: str, args: dict, event: MessageEvent, result: dict
    ) -> None:
        """Persist meeting data to storage."""
        if not HAS_STORAGE or not self._storage:
            return

        if command == "create":
            room_name = args.get("value", "meeting")
            meeting_url = result.get("meeting_url", "")
            await self._storage.write(
                f"meeting:{event.room_id}",
                {
                    "room_id": event.room_id,
                    "room_name": room_name,
                    "creator": event.sender,
                    "url": meeting_url,
                    "created_at": str(event.server_timestamp),
                },
                namespace="meetings",
            )
        elif command == "watch":
            video_url = args.get("url", "")
            room_name = args.get("name", "watch-party")
            content_type = result.get("content_type", "video")
            await self._storage.write(
                f"watch:{event.room_id}",
                {
                    "room_id": event.room_id,
                    "room_name": room_name,
                    "video_url": video_url,
                    "content_type": content_type,
                    "creator": event.sender,
                },
                namespace="watch_parties",
            )
        elif command == "mod":
            target = args.get("value", "")
            await self._storage.write(
                f"mod:{event.room_id}:{target}",
                {
                    "room_id": event.room_id,
                    "user": target,
                    "granted_by": event.sender,
                },
                namespace="moderators",
            )

    # ── Helpers ────────────────────────────────────────────────────────────

    def _is_moderator(self, user_id: str) -> bool:
        """Check if user is allowed to run moderator commands."""
        whitelist = self.config["admin_whitelist"]
        if not whitelist:
            return True
        return user_id in whitelist

    def _help_text(self) -> str:
        """Return help text grouped by category."""
        categories: dict[str, list[str]] = {}
        for name, cmd in COMMAND_REGISTRY.items():
            cat = cmd.category
            if cat not in categories:
                categories[cat] = []
            mod = " (mod)" if cmd.requires_moderator else ""
            categories[cat].append(f"  !jitsi {name} {cmd.usage}{mod} — {cmd.description}")

        lines = ["Jitsi Commands:"]
        for cat, cmds in categories.items():
            lines.append(f"\n{cat}:")
            lines.extend(cmds)
        lines.append("\nType !jitsi help <command> for details.")
        return "\n".join(lines)
