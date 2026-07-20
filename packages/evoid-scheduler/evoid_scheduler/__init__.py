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
    "version": "1.0.0",
    "type": "engine",
    "description": "Priority-aware scheduler with system metrics and adaptive concurrency",
    "entry_point": "evoid_scheduler:register_plugin",
    "dependencies": ["evoid>=0.4.0"],
    "evoid_version": ">=0.4.0",
    "tags": ["scheduler", "priority", "load-balancing", "system-metrics"],
}


def register_plugin():
    """Called by EVOID to register this plugin."""
    from evoid.engines.plugin import register

    register(
        name="scheduler",
        type="engine",
        factory=SchedulerEngine,
        version="1.0.0",
        description="Priority-aware scheduler with system metrics",
    )
