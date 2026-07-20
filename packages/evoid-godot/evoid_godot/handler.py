"""Game Intent Handler — processes intents from Godot games.

Handles game intents and routes them to the message bus.
"""

from __future__ import annotations

from typing import Any

from evoid import Intent, Level, publish, subscribe
from .topics import Topics


async def game_intent_handler(ctx: Any) -> dict:
    """Handle a game intent from Godot client.

    IOP-compliant: takes Context, reads ctx.intent, writes ctx.state.
    Routes the intent to the message bus for processing.
    """
    intent = ctx.intent
    game_id = intent.metadata.get("game_id", "default")
    player_id = intent.metadata.get("player_id", "unknown")
    action = intent.metadata.get("action", intent.name)

    # Publish to message bus
    await publish(
        Intent(
            name=f"game:{game_id}:{action}",
            level=intent.level,
            metadata={
                **intent.metadata,
                "player_id": player_id,
                "game_id": game_id,
                "source": "godot_client",
            },
        ),
        source=f"godot:{player_id}",
    )

    # Write result to context state
    ctx.state["game_result"] = {
        "status": "ok",
        "action": action,
        "player_id": player_id,
    }

    return {"status": "ok", "action": action, "player_id": player_id}


def create_game_handler() -> Any:
    """Factory for game handler."""
    return game_intent_handler


def setup_game_subscriptions(game_id: str = "default"):
    """Setup default subscriptions for a game.

    Call this once when the game server starts.
    """
    # Subscribe to game events
    subscribe(f"game:{game_id}:player_move", _handle_player_move)
    subscribe(f"game:{game_id}:player_shot", _handle_player_shot)
    subscribe(f"game:{game_id}:card_played", _handle_card_played)
    subscribe(f"game:{game_id}:chat_message", _handle_chat_message)


async def _handle_player_move(intent: Intent) -> dict:
    """Handle player movement."""
    player_id = intent.metadata.get("player_id")
    x = intent.metadata.get("x", 0)
    y = intent.metadata.get("y", 0)

    # Broadcast to other players
    await publish(
        Intent(
            name=Topics.GAME_STATE_SYNC,
            level=Level.EPHEMERAL,
            metadata={
                "type": "player_moved",
                "player_id": player_id,
                "x": x,
                "y": y,
            },
        ),
        source=f"game:{intent.metadata.get('game_id', 'default')}",
    )

    return {"synced": True}


async def _handle_player_shot(intent: Intent) -> dict:
    """Handle player shot."""
    player_id = intent.metadata.get("player_id")
    origin = intent.metadata.get("origin", [0, 0])
    direction = intent.metadata.get("direction", [0, 1])

    # Broadcast shot event
    await publish(
        Intent(
            name=Topics.GAME_EVENT,
            level=Level.STANDARD,
            metadata={
                "type": "shot_fired",
                "player_id": player_id,
                "origin": origin,
                "direction": direction,
            },
        ),
        source=f"game:{intent.metadata.get('game_id', 'default')}",
    )

    return {"confirmed": True}


async def _handle_card_played(intent: Intent) -> dict:
    """Handle card played."""
    player_id = intent.metadata.get("player_id")
    card = intent.metadata.get("card")

    # Broadcast card event
    await publish(
        Intent(
            name=Topics.GAME_EVENT,
            level=Level.STANDARD,
            metadata={
                "type": "card_played",
                "player_id": player_id,
                "card": card,
            },
        ),
        source=f"game:{intent.metadata.get('game_id', 'default')}",
    )

    return {"confirmed": True}


async def _handle_chat_message(intent: Intent) -> dict:
    """Handle chat message."""
    player_id = intent.metadata.get("player_id")
    message = intent.metadata.get("message", "")

    # Broadcast chat
    await publish(
        Intent(
            name=Topics.GAME_EVENT,
            level=Level.EPHEMERAL,
            metadata={
                "type": "chat",
                "player_id": player_id,
                "message": message,
            },
        ),
        source=f"game:{intent.metadata.get('game_id', 'default')}",
    )

    return {"sent": True}


def setup_game_hosting(
    game_id: str,
    build_dir: str,
    title: str = "",
    splash: "SplashConfig | None" = None,
) -> "GameHost":
    """One-liner: register a game build and get a configured host.

    Example:
        host = setup_game_hosting("my-game", "builds/my-game/", title="My Game")
        app = Starlette(routes=[Mount("/game", app=host.create_router())])
    """
    from .hosting import GameHost

    host = GameHost()
    host.register_build(game_id, build_dir, title=title, splash=splash)
    return host
