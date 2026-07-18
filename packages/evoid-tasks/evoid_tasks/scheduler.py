"""Task scheduler — Godot-inspired lifecycle model.

Every task has lifecycle hooks:
  on_start()  → _ready()       — task begins
  on_tick()   → _process()     — runs every interval
  on_stop()   → _exit_tree()   — task ends
  on_event()  → Signal         — reacts to events
  on_error()  → error handler  — catches failures

Usage:
    from evoid_tasks import Task, scheduler

    # Simple: fire-and-forget
    scheduler.run(send_email, to="alice@example.com")

    # Lifecycle: recurring with hooks
    @scheduler.task(interval=60)
    async def monitorinventory(ctx):
        if ctx.started:
            await check_levels()
        if ctx.tick:
            await sync_stock()

    # Event-driven: reacts to signals
    @scheduler.on("order_placed")
    async def update_stats(ctx):
        await recalc_stats(ctx.event_data)
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .logger import get_logger


@dataclass
class TaskContext:
    """Runtime context for a task — passed to lifecycle hooks.

    Inspired by Godot's _process(delta) and _ready() patterns.
    """
    task_name: str
    started: bool = False
    tick: bool = False
    stopped: bool = False
    delta: float = 0.0  # Time since last tick
    event_data: dict = field(default_factory=dict)
    state: dict = field(default_factory=dict)  # Task-local state


@dataclass(frozen=True)
class TaskDef:
    """Task definition — pure data."""
    name: str
    func: Callable
    interval: float | None = None
    event: str | None = None  # Listen to this event
    created_at: float = field(default_factory=time.time)


class TaskScheduler:
    """Godot-inspired task scheduler with lifecycle hooks.

    Lifecycle:
        on_start  → called once when task begins
        on_tick   → called every interval
        on_stop   → called when task is cancelled
        on_event  → called when a signal/event fires
        on_error  → called on exception
    """

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._tasks: list[TaskDef] = []
        self._running: dict[str, asyncio.Task] = {}
        self._event_handlers: dict[str, list[Callable]] = {}
        self._log = get_logger("tasks")

    # ============================================================
    # Core API
    # ============================================================

    def run(self, func: Callable, *args: Any, **kwargs: Any) -> TaskDef:
        """Fire-and-forget. Runs once in background."""
        task = TaskDef(name=func.__name__, func=func)
        self._tasks.append(task)
        asyncio.create_task(self._exec_once(task, args, kwargs))
        return task

    def task(
        self,
        func: Callable | None = None,
        *,
        interval: float | None = None,
    ):
        """Decorator: define a task with optional interval.

        @scheduler.task(interval=60)
        async def monitor(ctx):
            ...
        """
        def decorator(fn: Callable) -> TaskDef:
            task_def = TaskDef(name=fn.__name__, func=fn, interval=interval)
            self._tasks.append(task_def)
            if interval:
                task_id = f"{fn.__name__}_{id(fn)}"
                self._running[task_id] = asyncio.create_task(
                    self._run_lifecycle(task_def)
                )
                self._log.info(f"Scheduled: {fn.__name__} every {interval}s")
            return task_def  # type: ignore

        if func is not None:
            return decorator(func)
        return decorator

    def on(self, event: str):
        """Decorator: listen to an event.

        @scheduler.on("order_placed")
        async def handle_order(ctx):
            order = ctx.event_data
            ...
        """
        def decorator(fn: Callable) -> Callable:
            self._event_handlers.setdefault(event, []).append(fn)
            self._log.info(f"Listening: {fn.__name__} → '{event}'")
            return fn
        return decorator

    def emit(self, event: str, data: dict | None = None) -> None:
        """Emit an event to all handlers."""
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            asyncio.create_task(self._exec_event(handler, event, data or {}))

    # ============================================================
    # Lifecycle execution
    # ============================================================

    async def _exec_once(
        self, task: TaskDef, args: tuple, kwargs: dict
    ) -> None:
        """Execute a one-shot task with lifecycle."""
        ctx = TaskContext(task_name=task.name, started=True)
        start = time.monotonic()

        self._log.info(f"▶ start: {task.name}")

        try:
            if asyncio.iscoroutinefunction(task.func):
                await task.func(*args, **kwargs)
            else:
                task.func(*args, **kwargs)

            duration = time.monotonic() - start
            self._log.info(f"■ done: {task.name} ({duration:.3f}s)")
            self._emit_event("task_completed", {
                "name": task.name, "duration": duration,
            })

        except Exception as e:
            duration = time.monotonic() - start
            self._log.error(f"✖ error: {task.name} — {e}")
            self._emit_event("task_failed", {
                "name": task.name, "duration": duration, "error": str(e),
            })

    async def _run_lifecycle(self, task: TaskDef) -> None:
        """Run a recurring task with full lifecycle."""
        ctx = TaskContext(task_name=task.name)
        last_tick = time.monotonic()

        # _ready
        ctx.started = True
        self._log.info(f"▶ ready: {task.name}")

        try:
            if hasattr(task.func, "on_start"):
                await task.func.on_start(ctx)

            while True:
                # _process(delta)
                now = time.monotonic()
                ctx.delta = now - last_tick
                ctx.tick = True
                last_tick = now

                try:
                    if asyncio.iscoroutinefunction(task.func):
                        await task.func(ctx)
                    else:
                        task.func(ctx)
                except Exception as e:
                    self._log.error(f"✖ tick error: {task.name} — {e}")
                    if hasattr(task.func, "on_error"):
                        await task.func.on_error(ctx, e)

                ctx.tick = False
                await asyncio.sleep(task.interval)

        except asyncio.CancelledError:
            # _exit_tree
            ctx.stopped = True
            self._log.info(f"■ stop: {task.name}")
            if hasattr(task.func, "on_stop"):
                await task.func.on_stop(ctx)

    async def _exec_event(
        self, handler: Callable, event: str, data: dict
    ) -> None:
        """Execute an event handler."""
        ctx = TaskContext(task_name=handler.__name__, event_data=data)
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(ctx)
            else:
                handler(ctx)
        except Exception as e:
            self._log.error(f"✖ event error: {handler.__name__} on '{event}' — {e}")

    def _emit_event(self, name: str, data: dict) -> None:
        """Emit to EVOID event system."""
        try:
            from evoid.core.events import emit_sync
            emit_sync(name, data)
        except ImportError:
            pass

    # ============================================================
    # Control
    # ============================================================

    def cancel(self, task_def: TaskDef) -> None:
        """Cancel a scheduled task."""
        task_id = f"{task_def.name}_{id(task_def.func)}"
        if task_id in self._running:
            self._running[task_id].cancel()
            del self._running[task_id]
            self._log.info(f"Cancelled: {task_def.name}")

    def shutdown(self) -> None:
        """Cancel all tasks."""
        for async_task in self._running.values():
            async_task.cancel()
        self._running.clear()
        self._log.info("Scheduler shut down")

    @property
    def active(self) -> int:
        return len(self._running)


# ============================================================
# Default scheduler
# ============================================================

scheduler = TaskScheduler()
