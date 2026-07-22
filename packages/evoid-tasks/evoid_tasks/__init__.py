"""Background Tasks with IOP Pipeline Integration for EVOID.

Godot-inspired lifecycle + IOP-native pipeline injection.

Lifecycle:  on_start → on_tick → on_stop
IOP:        as_processor() → as_intent() → inject()
"""

from .scheduler import TaskScheduler, TaskContext, TaskDef, scheduler
from .logger import TaskLogger, get_logger

# Convenience re-exports
run = scheduler.run
task = scheduler.task
on = scheduler.on
emit = scheduler.emit
as_processor = scheduler.as_processor
as_intent = scheduler.as_intent
inject = scheduler.inject

__all__ = [
    "TaskScheduler", "TaskContext", "TaskDef", "scheduler",
    "run", "task", "on", "emit",
    "as_processor", "as_intent", "inject",
    "TaskLogger", "get_logger",
]

MANIFEST = {
    "name": "evoid-tasks",
    "version": "0.1.0",
    "type": "engine",
    "description": "Background tasks with lifecycle + IOP pipeline integration",
    "entry_point": "evoid_tasks:register_plugin",
    "dependencies": ["evoid>=0.4.0"],
    "evoid_version": ">=0.4.0",
    "tags": ["tasks", "background", "logging", "lifecycle", "pipeline"],
}


def register_plugin():
    """Called when the plugin is loaded (legacy path)."""
    from evoid.engines.plugin import register
    register(
        name="tasks",
        type="engine",
        factory=lambda config: scheduler,
        version="0.1.0",
        description="Background task scheduler with lifecycle + pipeline injection",
    )


def register_handlers(max_concurrent: int = 10) -> None:
    """Register task scheduler as Intent handlers.

    IOP: Task operations are Intents.
    The scheduler manages background execution.
    Registers with DI as 'scheduler.tasks' for dependency resolution.
    """
    from evoid_di import di

    di.register("scheduler.tasks", lambda: scheduler, scope="singleton")

    async def handle_task_run(ctx):
        sched = di.resolve("scheduler.tasks")
        func = ctx.intent.metadata.get("func")
        args = ctx.intent.metadata.get("args", ())
        kwargs = ctx.intent.metadata.get("kwargs", {})
        return await sched.run(func, *args, **kwargs)

    async def handle_task_status(ctx):
        sched = di.resolve("scheduler.tasks")
        return {"active": sched.active}
