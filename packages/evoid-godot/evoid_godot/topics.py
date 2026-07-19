"""Topics — single source of truth for all EVOID Godot topic strings.

Same pattern as EvoidTopics in the Godot plugin.
Every topic MUST be defined here before use.
"""


class Topics:
    """EVOID Godot topics — mirrors EvoidTopics in Godot plugin."""

    # App lifecycle
    STATE_CHANGED = "evoid/state_changed"
    CONNECT_REQ = "evoid/connect_requested"
    DISCONNECT_REQ = "evoid/disconnect_requested"

    # Network
    NET_AVAILABLE = "evoid/net/available"
    NET_UNAVAILABLE = "evoid/net/unavailable"
    NET_ERROR = "evoid/net/error"
    NET_LATENCY_UPDATED = "evoid/net/latency_updated"

    # Session
    SESSION_SYNCED = "evoid/session/synced"
    SESSION_RESYNC_REQ = "evoid/session/resync_requested"

    # Commands
    CMD_SENT = "evoid/cmd/sent"
    CMD_ACKED = "evoid/cmd/acked"
    CMD_FAILED = "evoid/cmd/failed"

    # Game events
    GAME_EVENT = "evoid/game/event"
    GAME_STATE_SYNC = "evoid/game/state_sync"
    GAME_PLAYER_JOINED = "evoid/game/player_joined"
    GAME_PLAYER_LEFT = "evoid/game/player_left"

    # Intent
    INTENT_CREATED = "evoid/intent/created"
    INTENT_EXECUTED = "evoid/intent/executed"
    INTENT_FAILED = "evoid/intent/failed"
