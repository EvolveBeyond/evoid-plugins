"""Tests for evoid-maubot framework."""

from __future__ import annotations

from evoid_maubot.commands import (
    COMMAND_REGISTRY,
    CommandDef,
    parse_no_args,
    parse_optional_one,
    parse_required_one,
)


def test_command_registry_empty_by_default() -> None:
    """Ensure command registry starts empty."""
    assert COMMAND_REGISTRY == {}


def test_command_def_defaults() -> None:
    """Test CommandDef default values."""
    cmd = CommandDef()
    assert cmd.description == ""
    assert cmd.usage == ""
    assert cmd.category == "General"
    assert cmd.requires_moderator is False
    assert cmd.arg_parser is None
    assert cmd.response_formatter is None


def test_parse_required_one() -> None:
    result = parse_required_one(["value"])
    assert result == {"value": "value"}
    assert parse_required_one([]) is None


def test_parse_optional_one() -> None:
    result = parse_optional_one(["value"])
    assert result == {"value": "value"}
    result = parse_optional_one([])
    assert result == {"value": ""}


def test_parse_no_args() -> None:
    assert parse_no_args([]) == {}
    assert parse_no_args(["ignored"]) == {}
