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
                "default_level": "standard",
                "command_prefix": "jitsi",
                "jitsi": {
                    "server_url": "",
                    "muc_domain": "",
                    "admin_username": "",
                    "admin_password": "",
                },
                "storage": {
                    "db_path": "jitsi-bot.db",
                    "enable_smart_routing": True,
                },
                "admin_whitelist": [],
                "debug": False,
            }
        )
