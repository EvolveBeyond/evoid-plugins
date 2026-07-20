"""EVOID Godot Integration — Adapter for Godot games.

Connects Godot games to EVOID server via WebSocket.
Follows the same topic/event pattern as the Godot plugin.
"""

from .topics import Topics
from .handler import game_intent_handler, create_game_handler, setup_game_hosting
from .hosting import GameHost, GameBuild, SplashConfig

__all__ = [
    "Topics",
    "game_intent_handler",
    "create_game_handler",
    "setup_game_hosting",
    "GameHost",
    "GameBuild",
    "SplashConfig",
    "register_plugin",
]

MANIFEST = {
    "name": "evoid-godot",
    "version": "1.0.0",
    "type": "adapter",
    "description": "Godot game integration adapter for EVOID",
    "entry_point": "evoid_godot:register_plugin",
    "dependencies": ["evoid>=0.4.0"],
    "evoid_version": ">=0.4.0",
    "tags": ["godot", "game", "websocket", "adapter", "hosting", "web"],
}


def register_plugin():
    """Called by EVOID to register this plugin."""
    from evoid.engines.plugin import register

    register(
        name="godot",
        type="adapter",
        factory=create_game_handler,
        version="1.0.0",
        description="Godot game integration adapter",
    )
