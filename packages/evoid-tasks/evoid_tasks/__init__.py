"""Background Tasks with Structured Logging for EVOID.

Godot-inspired lifecycle model:
  on_start  → _ready()       — task begins
  on_tick   → _process()     — runs every interval
  on_stop   → _exit_tree()   — task ends
  on_event  → Signal         — reacts to events
  on_error  → error handler  — catches failures

IOP: Tasks are Intents. Logging is a processor.
"""

from .scheduler import TaskScheduler, TaskContext, TaskDef, scheduler
from .logger import TaskLogger, get_logger

# Convenience re-exports
run = scheduler.run
task = scheduler.task
on = scheduler.on
emit = scheduler.emit

__all__ = [
    "TaskScheduler",
    "TaskContext",
    "TaskDef",
    "scheduler",
    "run",
    "task",
    "on",
    "emit",
    "TaskLogger",
    "get_logger",
]

MANIFEST = {
    "name": "evoid-tasks",
    "version": "0.1.0",
    "type": "engine",
    "description": "Background tasks with Godot-inspired lifecycle",
    "entry_point": "evoid_tasks:register_plugin",
    "dependencies": ["evoid>=0.4.0"],
    "evoid_version": ">=0.4.0",
    "tags": ["tasks", "background", "logging", "lifecycle"],
}


def register_plugin():
    from evoid.engines.plugin import register
    register(
        name="tasks",
        type="engine",
        factory=lambda config: scheduler,
        version="0.1.0",
        description="Background task scheduler with lifecycle hooks",
    )
