"""Config handler for EVOID Maubot plugin."""

from __future__ import annotations

from typing import Any

from mautrix.util.config import BaseProxyConfig


class Config(BaseProxyConfig):
    """Configuration for EVOID Maubot plugin."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.update(
            {
                "service_name": "maubot-bot",
                "command_prefix": "bot",
                "storage": {
                    "db_path": "bot.db",
                    "enable_smart_routing": False,
                    "smart_mapping": {},
                    "smart_schemas": {},
                },
                "admin_whitelist": [],
            }
        )
