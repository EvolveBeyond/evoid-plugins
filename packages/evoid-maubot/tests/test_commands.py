"""Tests for evoid-jitsi-maubot command registry."""

from __future__ import annotations

from evoid_jitsi_maubot.commands import (
    COMMAND_REGISTRY,
    CommandDef,
    _fmt_created,
    _fmt_watch,
    _parse_kick,
    _parse_recording,
    _parse_volume,
    _parse_watch,
)


def test_command_registry_not_empty() -> None:
    """Ensure command registry has expected commands."""
    assert len(COMMAND_REGISTRY) > 0
    assert "create" in COMMAND_REGISTRY
    assert "join" in COMMAND_REGISTRY
    assert "kick" in COMMAND_REGISTRY
    assert "watch" in COMMAND_REGISTRY


def test_create_command() -> None:
    """Test create command definition."""
    cmd = COMMAND_REGISTRY["create"]
    assert isinstance(cmd, CommandDef)
    assert cmd.category == "Room"
    assert cmd.requires_moderator is False
    assert cmd.arg_parser is not None


def test_kick_command_requires_moderator() -> None:
    """Test kick command requires moderator."""
    cmd = COMMAND_REGISTRY["kick"]
    assert cmd.requires_moderator is True
    assert cmd.category == "Participants"


def test_parse_watch_args() -> None:
    """Test watch argument parsing."""
    result = _parse_watch(["https://youtube.com/watch?v=abc", "my-party"])
    assert result == {"url": "https://youtube.com/watch?v=abc", "name": "my-party"}

    result = _parse_watch(["https://youtube.com/watch?v=abc"])
    assert result == {"url": "https://youtube.com/watch?v=abc", "name": ""}

    assert _parse_watch([]) is None


def test_parse_kick_args() -> None:
    """Test kick argument parsing."""
    result = _parse_kick(["participant123"])
    assert result == {"participantId": "participant123"}

    assert _parse_kick([]) is None


def test_parse_volume_args() -> None:
    """Test volume argument parsing."""
    result = _parse_volume(["user123", "0.5"])
    assert result == {"participantId": "user123", "volume": 0.5}

    # Clamped to 0-1
    result = _parse_volume(["user123", "1.5"])
    assert result == {"participantId": "user123", "volume": 1.0}

    result = _parse_volume(["user123", "-0.5"])
    assert result == {"participantId": "user123", "volume": 0.0}

    assert _parse_volume(["user123"]) is None


def test_parse_recording_args() -> None:
    """Test recording argument parsing."""
    result = _parse_recording(["local"])
    assert result == {"mode": "local"}

    result = _parse_recording(["stream", "rtmp-key"])
    assert result == {"mode": "stream", "rtmpStreamKey": "rtmp-key"}

    assert _parse_recording(["invalid"]) is None


def test_fmt_created() -> None:
    """Test create response formatting."""
    result = {"meeting_url": "https://meet.example.com/room123"}
    assert _fmt_created(result, {}) == "Room created: https://meet.example.com/room123"


def test_fmt_watch() -> None:
    """Test watch response formatting."""
    result = {"meeting_url": "https://meet.example.com/room123", "content_type": "youtube"}
    args = {"url": "https://youtube.com/watch?v=abc"}
    formatted = _fmt_watch(result, args)
    assert "youtube" in formatted
    assert "https://meet.example.com/room123" in formatted
    assert "https://youtube.com/watch?v=abc" in formatted
