"""Tests for evoid-tasks plugin."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from evoid_tasks import TaskScheduler, TaskLogger


class TestTaskScheduler:
    @pytest.fixture
    def scheduler(self):
        return TaskScheduler(max_concurrent=5)

    @pytest.mark.asyncio
    async def test_background_runs(self, scheduler):
        func = AsyncMock(return_value="done")
        scheduler.background(func)
        # Give background task time to complete
        await asyncio.sleep(0.1)
        func.assert_called_once()

    @pytest.mark.asyncio
    async def test_background_with_args(self, scheduler):
        func = AsyncMock()
        scheduler.background(func, "arg1", key="value")
        await asyncio.sleep(0.1)
        func.assert_called_once_with("arg1", key="value")

    def test_schedule_creates_task(self, scheduler):
        func = AsyncMock()
        task = scheduler.schedule(func, interval=60)
        assert task.name == "test_tasks.<lambda>" or task.name == func.__name__
        assert task.interval == 60

    def test_cancel(self, scheduler):
        func = AsyncMock()
        task = scheduler.schedule(func, interval=60)
        scheduler.cancel(task)
        assert len(scheduler._scheduled) == 0

    def test_shutdown(self, scheduler):
        func = AsyncMock()
        scheduler.schedule(func, interval=60)
        scheduler.schedule(func, interval=30)
        scheduler.shutdown()
        assert len(scheduler._scheduled) == 0

    def test_pending_count(self, scheduler):
        assert scheduler.pending == 0
        func = AsyncMock()
        scheduler.background(func)
        # pending increments when task is added
        # (even if it runs immediately in background)


class TestTaskLogger:
    def test_logger_creation(self):
        logger = TaskLogger("my_component")
        assert logger.component == "my_component"

    def test_logger_info(self):
        logger = TaskLogger("test")
        # Should not raise
        logger.info("test message")

    def test_logger_error(self):
        logger = TaskLogger("test")
        logger.error("error message")

    def test_logger_warning(self):
        logger = TaskLogger("test")
        logger.warning("warning message")

    def test_logger_debug(self):
        logger = TaskLogger("test")
        logger.debug("debug message")
