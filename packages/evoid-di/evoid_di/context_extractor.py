"""Extract routing context from EVOID Context."""

from __future__ import annotations

from typing import Any


def extract_context(ev_ctx: Any, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a flat context dict from EVOID Context for rule matching."""
    intent = ev_ctx.intent

    ctx = {
        "level": intent.level,
        "name": intent.name,
        "metadata": intent.metadata,
        "user_id": ev_ctx.state.get("user_id"),
        "user_role": ev_ctx.state.get("user_role"),
    }

    if extra:
        ctx.update(extra)

    return ctx
