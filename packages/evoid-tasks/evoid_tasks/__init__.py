"""Background Tasks with Structured Logging for EVOID.

Every task produces structured logs via EVOID's event system.
Loguru is optional — install with `evoid-tasks[loguru]` for pretty output.

IOP: Tasks are Intents. Logging is a processor.
"""

from .scheduler import TaskScheduler, background, schedule
from .logger import TaskLogger, get_logger

__all__ = [
    "TaskScheduler",
    "background",
    "schedule",
    "TaskLogger",
    "get_logger",
]

MANIFEST = {
    "name": "evoid-tasks",
    "version": "0.1.0",
    "type": "engine",
    "description": "Background tasks with structured logging",
    "entry_point": "evoid_tasks:register_plugin",
    "dependencies": ["evoid>=0.4.0"],
    "evoid_version": ">=0.4.0",
    "tags": ["tasks", "background", "logging"],
}


def register_plugin():
    """Called when the plugin is loaded."""
    from evoid.engines.plugin import register

    register(
        name="tasks",
        type="engine",
        factory=TaskScheduler,
        version="0.1.0",
        description="Background task scheduler with structured logging",
    )
