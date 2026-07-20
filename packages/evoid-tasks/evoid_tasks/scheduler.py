"""Task scheduler — Godot-inspired lifecycle + IOP pipeline integration.

Lifecycle hooks:
  on_start  → _ready()       — task begins
  on_tick   → _process()     — runs every interval
  on_stop   → _exit_tree()   — task ends
  on_event  → Signal         — reacts to events

IOP integration:
  as_processor()  → register as pipeline processor
  as_intent()     → register as Intent with custom pipeline
  inject()        → add task to pipeline via before/after
"""

from __future__ import annotations

import asyncio
import inspect
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .logger import get_logger


def _check_wants_ctx(fn: Callable) -> bool:
    """Check if a function accepts a ctx parameter. Uses inspect.signature for robustness."""
    try:
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        return len(params) > 0 and params[0] in ("ctx", "context", "task_ctx")
    except (ValueError, TypeError):
        return False


@dataclass
class TaskContext:
    """Runtime context for a task — lifecycle hooks."""
    task_name: str
    started: bool = False
    tick: bool = False
    stopped: bool = False
    delta: float = 0.0
    event_data: dict = field(default_factory=dict)
    state: dict = field(default_factory=dict)


@dataclass(frozen=True)
class TaskDef:
    """Task definition — pure data."""
    name: str
    func: Callable
    interval: float | None = None
    event: str | None = None
    created_at: float = field(default_factory=time.time)


class TaskScheduler:
    """Task scheduler with lifecycle + IOP integration."""

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
        """Fire-and-forget. Runs once in background. Cleans up after completion."""
        task = TaskDef(name=func.__name__, func=func)
        self._tasks.append(task)
        t = asyncio.create_task(self._exec_once(task, args, kwargs))
        t.add_done_callback(lambda _: self._cleanup_task(task))
        return task

    def _cleanup_task(self, task: TaskDef) -> None:
        """Remove completed one-shot task from list."""
        try:
            self._tasks.remove(task)
        except ValueError:
            pass

    def task(
        self,
        func: Callable | None = None,
        *,
        interval: float | None = None,
    ):
        """Decorator: define a task with optional interval."""
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
        """Decorator: listen to an event."""
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
    # IOP Integration — Pipeline Injection
    # ============================================================

    def as_processor(self, name: str | None = None) -> Callable:
        """Convert a task into an EVOID processor.

        @scheduler.task(interval=60)
        async def monitor(ctx):
            ...

        # Register as processor
        monitor.as_processor("monitor_inventory")

        # Or inline
        @scheduler.as_processor("check_health")
        async def health_check(ctx):
            ...
        """
        def decorator(fn: Callable) -> Callable:
            processor_name = name or fn.__name__
            _wants_ctx = _check_wants_ctx(fn)

            async def processor(ctx) -> dict:
                """Wrapper that runs the task and returns a result."""
                task_ctx = TaskContext(task_name=processor_name, started=True)
                try:
                    if asyncio.iscoroutinefunction(fn):
                        if _wants_ctx:
                            result = await fn(task_ctx)
                        else:
                            result = await fn()
                    else:
                        result = fn()
                    return {"task": processor_name, "status": "completed", "result": result}
                except Exception as e:
                    return {"task": processor_name, "status": "failed", "error": str(e)}

            # Register with EVOID
            from evoid import register_processor
            register_processor(processor_name, processor)
            self._log.info(f"Registered as processor: {processor_name}")

            # Attach inject method
            fn.as_processor = lambda n=None: self.as_processor(n or processor_name)(fn)  # type: ignore
            fn.processor_name = processor_name  # type: ignore
            return fn

        return decorator

    def as_intent(
        self,
        name: str,
        level: str = "standard",
        pipeline: tuple[str, ...] | None = None,
    ) -> Callable:
        """Convert a task into an EVOID Intent + processor.

        @scheduler.as_intent("sync_inventory", level="standard", pipeline=("validate", "sync"))
        async def sync_inventory():
            ...
        """
        def decorator(fn: Callable) -> Callable:
            from evoid import Intent, Level, register, register_processor

            intent_level = Level[level.upper()] if isinstance(level, str) else level
            intent = Intent(name=name, level=intent_level, metadata={"type": "task"})
            register(intent)

            async def processor(ctx) -> dict:
                try:
                    if asyncio.iscoroutinefunction(fn):
                        result = await fn()
                    else:
                        result = fn()
                    return {"task": name, "status": "completed", "result": result}
                except Exception as e:
                    return {"task": name, "status": "failed", "error": str(e)}

            register_processor(name, processor)

            if pipeline:
                from evoid.core.extend import add_intent_with_pipeline
                add_intent_with_pipeline(intent, list(pipeline), handler=processor)

            self._log.info(f"Registered as intent: {name} [{intent_level.value}]")
            fn.intent_name = name  # type: ignore
            fn.intent = intent  # type: ignore
            return fn

        return decorator

    def inject(self, task_fn: Callable, before: str | None = None, after: str | None = None) -> None:
        """Inject a task into an existing pipeline.

        scheduler.inject(monitor_task, before="handle_order")
        scheduler.inject(log_task, after="validate")
        """
        from evoid.core.extend import before as _before, after as _after

        processor_name = getattr(task_fn, "processor_name", getattr(task_fn, "intent_name", task_fn.__name__))

        if before:
            _before(before, processor_name)
            self._log.info(f"Injected {processor_name} before {before}")
        elif after:
            _after(after, processor_name)
            self._log.info(f"Injected {processor_name} after {after}")
        else:
            # Default: add to all standard-level intents
            from evoid.core.extend import before_all
            from evoid import Level
            before_all(processor_name, level=Level.STANDARD)

    # ============================================================
    # Lifecycle execution
    # ============================================================

    async def _exec_once(self, task: TaskDef, args: tuple, kwargs: dict) -> None:
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
            self._emit_event("task_completed", {"name": task.name, "duration": duration})
        except Exception as e:
            duration = time.monotonic() - start
            self._log.error(f"✖ error: {task.name} — {e}")
            self._emit_event("task_failed", {"name": task.name, "duration": duration, "error": str(e)})

    async def _run_lifecycle(self, task: TaskDef) -> None:
        ctx = TaskContext(task_name=task.name)
        last_tick = time.monotonic()
        ctx.started = True
        self._log.info(f"▶ ready: {task.name}")
        try:
            if hasattr(task.func, "on_start"):
                await task.func.on_start(ctx)
            while True:
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
            ctx.stopped = True
            self._log.info(f"■ stop: {task.name}")
            if hasattr(task.func, "on_stop"):
                await task.func.on_stop(ctx)

    async def _exec_event(self, handler: Callable, event: str, data: dict) -> None:
        ctx = TaskContext(task_name=handler.__name__, event_data=data)
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(ctx)
            else:
                handler(ctx)
        except Exception as e:
            self._log.error(f"✖ event error: {handler.__name__} on '{event}' — {e}")

    def _emit_event(self, name: str, data: dict) -> None:
        try:
            from evoid.core.events import emit_sync
            emit_sync(name, data)
        except ImportError:
            pass

    # ============================================================
    # Control
    # ============================================================

    def cancel(self, task_def: TaskDef) -> None:
        task_id = f"{task_def.name}_{id(task_def.func)}"
        if task_id in self._running:
            self._running[task_id].cancel()
            del self._running[task_id]
            self._log.info(f"Cancelled: {task_def.name}")

    def shutdown(self) -> None:
        for async_task in self._running.values():
            async_task.cancel()
        self._running.clear()
        self._log.info("Scheduler shut down")

    @property
    def active(self) -> int:
        return len(self._running)


# Default scheduler
scheduler = TaskScheduler()
