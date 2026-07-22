"""EVOID Scheduler — Priority-aware task scheduling with system metrics.

Provides system-aware scheduling with:
- True priority queue (O(log n) operations)
- System metrics (CPU cores, load average, memory)
- Adaptive concurrency based on system load
- Task deferral when system is overloaded
- Cross-service load balancing via message bus
"""

from .engine import SchedulerEngine, Priority, SystemMetrics
from .processor import scheduler_processor

__all__ = [
    "SchedulerEngine",
    "Priority",
    "SystemMetrics",
    "scheduler_processor",
    "register_plugin",
]

MANIFEST = {
    "name": "evoid-scheduler",
    "version": "0.1.1",
    "type": "engine",
    "description": "Priority-aware scheduler with system metrics and adaptive concurrency",
    "entry_point": "evoid_scheduler:register_plugin",
    "dependencies": ["evoid>=0.4.3"],
    "evoid_version": ">=0.4.3",
    "tags": ["scheduler", "priority", "load-balancing", "system-metrics"],
}


def register_plugin():
    """Called by EVOID to register this plugin (legacy path)."""
    from evoid.engines.plugin import register

    register(
        name="scheduler",
        type="engine",
        factory=SchedulerEngine,
        version="0.1.1",
        description="Priority-aware scheduler with system metrics",
    )


def register_handlers(max_workers: int = 4) -> None:
    """Register scheduler as Intent handlers.

    IOP: Scheduler operations are Intents for task management.
    Registers with DI as 'scheduler.priority' for dependency resolution.
    """
    from evoid_di import di

    di.register("scheduler.priority", lambda: SchedulerEngine(), scope="singleton")
