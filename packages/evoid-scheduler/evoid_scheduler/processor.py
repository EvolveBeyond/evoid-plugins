"""Scheduler Processor — Pipeline integration for auto-defer and metrics."""

from __future__ import annotations

from evoid import register_processor
from evoid.core import Context
from .engine import SchedulerEngine, Priority

_engine: SchedulerEngine | None = None


def _get_engine() -> SchedulerEngine:
    global _engine
    if _engine is None:
        _engine = SchedulerEngine()
    return _engine


async def scheduler_processor(ctx: Context) -> dict:
    """Check system load and defer low-priority tasks if overloaded."""
    engine = _get_engine()
    metrics = engine.metrics()

    priority = ctx.intent.priority

    if metrics.is_overloaded and priority < Priority.NORMAL:
        return {
            "deferred": True,
            "reason": "system_overloaded",
            "load": metrics.load_avg_1m,
            "cores": metrics.cpu_cores,
        }

    ctx.state["scheduler_metrics"] = {
        "cpu_cores": metrics.cpu_cores,
        "load_avg_1m": metrics.load_avg_1m,
        "memory_available_mb": metrics.memory_available_mb,
        "is_overloaded": metrics.is_overloaded,
    }

    return {"scheduled": True}


register_processor("scheduler", scheduler_processor)
