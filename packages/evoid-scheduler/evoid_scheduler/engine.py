"""Scheduler Engine — Priority-aware task scheduling backend."""

from __future__ import annotations

import asyncio
import heapq
import os
import resource
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

_METRICS_TTL = 2.0  # seconds — cache metrics for 2s to avoid /proc reads on every call
_MAX_DEFERRED = 1000  # max deferred tasks to prevent memory leak


class Priority:
    """Priority levels for intent scheduling."""

    CRITICAL = 100
    HIGH = 75
    NORMAL = 50
    LOW = 25
    BACKGROUND = 10
    DEFERRED = 0


@dataclass(frozen=True)
class SystemMetrics:
    """System state snapshot."""

    cpu_cores: int
    cpu_count_logical: int
    load_avg_1m: float
    load_avg_5m: float
    load_avg_15m: float
    memory_total_mb: float
    memory_available_mb: float

    @property
    def is_overloaded(self) -> bool:
        return self.load_avg_1m > self.cpu_count_logical

    @property
    def recommended_concurrency(self) -> int:
        if self.is_overloaded:
            return max(1, self.cpu_count_logical // 2)
        return self.cpu_count_logical


@dataclass(order=True)
class _QueueItem:
    """Internal queue item — ordered by priority (desc), then timestamp (asc via negation)."""

    priority: int
    neg_timestamp: float = field(compare=False)
    task_id: str = field(compare=False)
    intent: Any = field(compare=False)


class SchedulerEngine:
    """Priority-aware scheduler engine.

    Provides:
    - True priority queue with O(log n) operations via heapq
    - Cached system metrics (2s TTL) to avoid repeated /proc reads
    - Adaptive concurrency based on load
    - Task deferral when overloaded (bounded at 1000)
    """

    def __init__(
        self,
        max_workers: int | None = None,
        load_threshold: float = 0.8,
        enable_defer: bool = True,
    ):
        self.max_workers = max_workers or os.cpu_count() or 4
        self.load_threshold = load_threshold
        self.enable_defer = enable_defer

        self._heap: list[_QueueItem] = []  # heapq min-heap (negated priority = max-heap)
        self._task_index: dict[str, _QueueItem] = {}  # O(1) cancel lookup
        self._running = 0
        self._task_counter = 0
        self._semaphore = asyncio.Semaphore(self.max_workers)
        self._deferred: deque[_QueueItem] = deque(maxlen=_MAX_DEFERRED)

        # Metrics cache
        self._cached_metrics: SystemMetrics | None = None
        self._metrics_time: float = 0.0

    def _collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics from OS (expensive — call sparingly)."""
        try:
            load = os.getloadavg()
            usage = resource.getrusage(resource.RUSAGE_SELF)
            mem_mb = usage.ru_maxrss / 1024
        except (OSError, AttributeError):
            load = (0.0, 0.0, 0.0)
            mem_mb = 0.0

        try:
            with open("/proc/meminfo") as f:
                line0 = f.readline()  # MemTotal: XXXXX kB
                f.readline()         # MemFree: ...
                line2 = f.readline() # MemAvailable: ... (or line3)
            mem_total = int(line0.split()[1]) / 1024
            mem_avail = int(line2.split()[1]) / 1024
        except (FileNotFoundError, IndexError, ValueError):
            mem_total = mem_mb
            mem_avail = mem_mb

        return SystemMetrics(
            cpu_cores=os.cpu_count() or 4,
            cpu_count_logical=os.cpu_count() or 4,
            load_avg_1m=load[0],
            load_avg_5m=load[1],
            load_avg_15m=load[2],
            memory_total_mb=mem_total,
            memory_available_mb=mem_avail,
        )

    def _get_metrics(self) -> SystemMetrics:
        """Return cached metrics, refreshing if stale (>2s old)."""
        now = time.monotonic()
        if self._cached_metrics is None or (now - self._metrics_time) > _METRICS_TTL:
            self._cached_metrics = self._collect_metrics()
            self._metrics_time = now
        return self._cached_metrics

    def _enqueue(self, intent: Any, priority: int, task_id: str) -> None:
        """Add item to priority queue — O(log n) via heapq."""
        item = _QueueItem(
            priority=-priority,  # negate for max-heap behavior
            neg_timestamp=-time.monotonic(),
            task_id=task_id,
            intent=intent,
        )
        heapq.heappush(self._heap, item)
        self._task_index[task_id] = item

    def _dequeue(self) -> _QueueItem | None:
        """Remove and return highest priority item — O(log n)."""
        while self._heap:
            item = heapq.heappop(self._heap)
            if item.task_id in self._task_index:
                del self._task_index[item.task_id]
                return item
        return None

    async def submit(self, intent: Any, priority: int = Priority.NORMAL) -> str:
        self._task_counter += 1
        task_id = f"task-{self._task_counter}"

        metrics = self._get_metrics()

        if self.enable_defer and metrics.is_overloaded and priority < Priority.NORMAL:
            if len(self._deferred) < _MAX_DEFERRED:
                self._deferred.append(_QueueItem(
                    priority=-priority,
                    neg_timestamp=-time.monotonic(),
                    task_id=task_id,
                    intent=intent,
                ))
            return task_id

        self._enqueue(intent, priority, task_id)
        return task_id

    async def cancel(self, task_id: str) -> bool:
        """Cancel a queued task — O(1) via index lookup."""
        item = self._task_index.pop(task_id, None)
        if item is not None:
            return True

        for i, item in enumerate(self._deferred):
            if item.task_id == task_id:
                self._deferred.remove(item)
                return True

        return False

    def metrics(self) -> SystemMetrics:
        return self._get_metrics()

    @property
    def queue_size(self) -> int:
        return len(self._heap)

    @property
    def deferred_size(self) -> int:
        return len(self._deferred)

    @property
    def active_workers(self) -> int:
        return self._running

    async def process_deferred(self) -> list[str]:
        """Process deferred tasks when system load drops. Returns re-enqueued task IDs."""
        if not self._deferred:
            return []

        metrics = self._get_metrics()
        if metrics.is_overloaded:
            return []

        re_enqueued: list[str] = []
        while self._deferred:
            item = self._deferred.popleft()
            self._enqueue(item.intent, -item.priority, item.task_id)
            re_enqueued.append(item.task_id)

        return re_enqueued

    def get_least_loaded(self) -> dict[str, Any]:
        metrics = self._get_metrics()
        return {
            "host": "localhost",
            "port": 8000,
            "load": metrics.load_avg_1m / metrics.cpu_count_logical,
            "queue_size": self.queue_size,
            "active_workers": self.active_workers,
        }
