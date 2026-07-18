"""Structured logging for tasks.

Uses EVOID's event system as the core.
Loguru is optional — for pretty terminal output.
"""

from __future__ import annotations

import sys
from typing import Any


class TaskLogger:
    """Structured logger that outputs via print + optional loguru.

    Always emits structured dicts to EVOID's event system.
    Pretty-prints to terminal (loguru if available, else plain).
    """

    def __init__(self, component: str = "task"):
        self.component = component
        self._use_loguru = False
        try:
            from loguru import logger as _loguru
            self._loguru = _loguru
            self._use_loguru = True
        except ImportError:
            self._loguru = None

    def _emit(self, level: str, msg: str, **kwargs: Any) -> None:
        """Emit to EVOID event system + terminal."""
        # EVOID event system
        try:
            from evoid.core.events import emit_sync
            emit_sync(f"task_{level}", {
                "component": self.component,
                "message": msg,
                **kwargs,
            })
        except ImportError:
            pass

        # Terminal output
        if self._use_loguru:
            getattr(self._loguru, level)(f"[{self.component}] {msg}", **kwargs)
        else:
            prefix = f"[{self.component.upper()}]"
            print(f"{prefix} {msg}", file=sys.stderr)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._emit("info", msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._emit("warning", msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._emit("error", msg, **kwargs)

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._emit("debug", msg, **kwargs)


def get_logger(component: str = "task") -> TaskLogger:
    """Get a structured logger for a component."""
    return TaskLogger(component)
