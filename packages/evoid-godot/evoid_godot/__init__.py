"""EVOID Godot Integration — Adapter for Godot games.

Connects Godot games to EVOID server via WebSocket.
Follows the same topic/event pattern as the Godot plugin.
"""

from .topics import Topics
from .handler import game_intent_handler, create_game_handler

__all__ = [
    "Topics",
    "game_intent_handler",
    "create_game_handler",
    "register_plugin",
]


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
