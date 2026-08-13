"""Command definitions for EVOID Maubot framework.

Commands are registered via COMMAND_REGISTRY dict.
Subclasses or users can populate this with their own commands.

Each command maps a Matrix !command subcommand to an EVOID Intent.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class CommandDef:
    """Definition of a Matrix command exposed via maubot."""

    iframe_command: str = ""
    description: str = ""
    usage: str = ""
    category: str = "General"
    requires_moderator: bool = False
    arg_parser: Callable[[list[str]], dict[str, Any] | None] | None = None
    response_formatter: Callable[[dict, dict], str] | None = None

    def parse_args(self, args: list[str]) -> dict[str, Any] | None:
        """Parse raw args into structured dict. Returns None if invalid."""
        if self.arg_parser:
            return self.arg_parser(args)
        return {}

    def format_response(self, result: dict, args: dict) -> str:
        """Format EVOID result into human-readable response."""
        if self.response_formatter:
            return self.response_formatter(result, args)
        return f"{self.iframe_command or self.description}: {result.get('status', 'done')}"


# Empty registry — subclasses/populate with register_command() or register_commands()
COMMAND_REGISTRY: dict[str, CommandDef] = {}


# ── Common Argument Parsers ────────────────────────────────────────────────────

def parse_required_one(args: list[str]) -> dict[str, Any] | None:
    if len(args) < 1:
        return None
    return {"value": args[0]}


def parse_optional_one(args: list[str]) -> dict[str, Any]:
    return {"value": args[0] if args else ""}


def parse_no_args(args: list[str]) -> dict[str, Any]:
    return {}
