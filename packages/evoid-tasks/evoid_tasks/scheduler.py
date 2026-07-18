"""Task scheduler — fire-and-forget, scheduled, and recurring tasks.

Every task execution is logged via the event system.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .logger import get_logger


@dataclass(frozen=True)
class Task:
    """Task definition — pure data."""
    name: str
    func: Callable
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    interval: float | None = None  # seconds between runs
    cron: str | None = None  # cron expression (future)
    created_at: float = field(default_factory=time.time)


class TaskScheduler:
    """Background task scheduler.

    Usage:
        scheduler = TaskScheduler()
        scheduler.background(send_email, to="user@example.com")
        scheduler.schedule(cleanup, interval=3600)
    """

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._tasks: list[Task] = []
        self._running: set[asyncio.Task] = set()
        self._scheduled: dict[str, asyncio.Task] = {}
        self._log = get_logger("tasks")

    def background(self, func: Callable, *args: Any, **kwargs: Any) -> Task:
        """Fire-and-forget task. Runs in background, result is discarded.

        Args:
            func: Async or sync function to run
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Task definition (for tracking)
        """
        task = Task(
            name=func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
        )
        self._tasks.append(task)
        self._log.info(f"Background task queued: {task.name}")
        asyncio.create_task(self._run_background(task))
        return task

    def schedule(
        self,
        func: Callable,
        interval: float | None = None,
        cron: str | None = None,
    ) -> Task:
        """Schedule a recurring task.

        Args:
            func: Async function to run repeatedly
            interval: Seconds between runs
            cron: Cron expression (future support)

        Returns:
            Task definition
        """
        task = Task(
            name=func.__name__,
            func=func,
            interval=interval,
            cron=cron,
        )
        self._tasks.append(task)

        if interval:
            task_id = f"{func.__name__}_{id(func)}"
            self._scheduled[task_id] = asyncio.create_task(
                self._run_recurring(task)
            )
            self._log.info(f"Scheduled: {task.name} every {interval}s")

        return task

    async def _run_background(self, task: Task) -> None:
        """Execute a background task with logging."""
        start = time.monotonic()
        self._log.info(f"Running: {task.name}")

        try:
            if asyncio.iscoroutinefunction(task.func):
                result = await task.func(*task.args, **task.kwargs)
            else:
                result = task.func(*task.args, **task.kwargs)

            duration = time.monotonic() - start
            self._log.info(f"Completed: {task.name} in {duration:.3f}s")

            # Emit event for EVOID event system
            try:
                from evoid.core.events import emit_sync
                emit_sync("task_completed", {
                    "name": task.name,
                    "duration": duration,
                    "success": True,
                })
            except ImportError:
                pass

        except Exception as e:
            duration = time.monotonic() - start
            self._log.error(f"Failed: {task.name} after {duration:.3f}s — {e}")

            try:
                from evoid.core.events import emit_sync
                emit_sync("task_failed", {
                    "name": task.name,
                    "duration": duration,
                    "error": str(e),
                })
            except ImportError:
                pass

    async def _run_recurring(self, task: Task) -> None:
        """Run a task on interval until cancelled."""
        while True:
            await asyncio.sleep(task.interval)
            await self._run_background(task)

    def cancel(self, task: Task) -> None:
        """Cancel a scheduled task."""
        task_id = f"{task.func.__name__}_{id(task.func)}"
        if task_id in self._scheduled:
            self._scheduled[task_id].cancel()
            del self._scheduled[task_id]
            self._log.info(f"Cancelled: {task.name}")

    def shutdown(self) -> None:
        """Cancel all scheduled tasks."""
        for task_id, async_task in self._scheduled.items():
            async_task.cancel()
        self._scheduled.clear()
        self._log.info("Scheduler shut down")

    @property
    def pending(self) -> int:
        """Number of queued background tasks."""
        return len(self._tasks)


# ============================================================
# Module-level convenience functions
# ============================================================

_default_scheduler: TaskScheduler | None = None


def _get_scheduler() -> TaskScheduler:
    global _default_scheduler
    if _default_scheduler is None:
        _default_scheduler = TaskScheduler()
    return _default_scheduler


def background(func: Callable, *args: Any, **kwargs: Any) -> Task:
    """Fire-and-forget a background task."""
    return _get_scheduler().background(func, *args, **kwargs)


def schedule(
    func: Callable,
    interval: float | None = None,
    cron: str | None = None,
) -> Task:
    """Schedule a recurring task."""
    return _get_scheduler().schedule(func, interval=interval, cron=cron)
