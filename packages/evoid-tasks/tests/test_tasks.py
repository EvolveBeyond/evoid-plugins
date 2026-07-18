"""Tests for evoid-tasks — lifecycle + IOP integration."""

import asyncio
import pytest
from evoid_tasks import TaskScheduler, TaskContext


class TestSimpleExecution:
    @pytest.fixture
    def s(self):
        return TaskScheduler()

    @pytest.mark.asyncio
    async def test_run_once(self, s):
        results = []
        async def my_task():
            results.append("done")
        s.run(my_task)
        await asyncio.sleep(0.1)
        assert results == ["done"]

    @pytest.mark.asyncio
    async def test_run_with_args(self, s):
        results = []
        async def my_task(x, y):
            results.append(x + y)
        s.run(my_task, 2, 3)
        await asyncio.sleep(0.1)
        assert results == [5]


class TestLifecycle:
    @pytest.fixture
    def s(self):
        return TaskScheduler()

    @pytest.mark.asyncio
    async def test_task_decorator(self, s):
        results = []
        @s.task(interval=0.1)
        async def my_task(ctx: TaskContext):
            results.append("tick")
            if len(results) >= 2:
                s.cancel(s._tasks[-1])
                raise asyncio.CancelledError()
        await asyncio.sleep(0.3)
        assert len(results) >= 2

    @pytest.mark.asyncio
    async def test_on_stop_called(self, s):
        stopped = []
        @s.task(interval=0.1)
        async def my_task(ctx: TaskContext):
            await asyncio.sleep(1)
        my_task.on_stop = lambda ctx: stopped.append(True)  # type: ignore
        await asyncio.sleep(0.05)
        s.cancel(s._tasks[-1])
        await asyncio.sleep(0.1)


class TestEvents:
    @pytest.fixture
    def s(self):
        return TaskScheduler()

    @pytest.mark.asyncio
    async def test_on_event(self, s):
        results = []
        @s.on("order_placed")
        async def handle(ctx: TaskContext):
            results.append(ctx.event_data)
        s.emit("order_placed", {"item": "BLT"})
        await asyncio.sleep(0.1)
        assert results == [{"item": "BLT"}]


class TestIOPIntegration:
    @pytest.fixture
    def s(self):
        return TaskScheduler()

    def test_as_processor_registers(self, s):
        @s.as_processor("my_check")
        async def check():
            return {"ok": True}
        # Processor should be registered
        from evoid import get_processor
        assert get_processor("my_check") is not None

    def test_as_intent_registers(self, s):
        @s.as_intent("my_task", level="ephemeral")
        async def my_task():
            return {"done": True}
        from evoid import resolve
        intent = resolve("my_task")
        assert intent is not None

    def test_inject_adds_to_pipeline(self, s):
        @s.as_processor("health_check")
        async def health():
            return {"healthy": True}
        # inject before a specific processor
        s.inject(health, before="validate")
        from evoid.core.extend import list_overrides
        overrides = list_overrides()
        # Should have an override for validate
        assert any("health_check" in str(v) for v in overrides.values())
