"""Tests for evoid-tasks — Godot-inspired lifecycle."""

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
    async def test_on_start_called(self, s):
        started = []

        @s.task(interval=0.1)
        async def my_task(ctx: TaskContext):
            if len(started) >= 1:
                s.cancel(s._tasks[-1])
                raise asyncio.CancelledError()

        my_task.on_start = lambda ctx: started.append(True)  # type: ignore

        await asyncio.sleep(0.2)

    @pytest.mark.asyncio
    async def test_on_stop_called(self, s):
        stopped = []

        @s.task(interval=0.1)
        async def my_task(ctx: TaskContext):
            await asyncio.sleep(1)  # Will be cancelled

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

    @pytest.mark.asyncio
    async def test_multiple_handlers(self, s):
        count = [0]

        @s.on("ping")
        async def handler1(ctx):
            count[0] += 1

        @s.on("ping")
        async def handler2(ctx):
            count[0] += 1

        s.emit("ping")
        await asyncio.sleep(0.1)
        assert count[0] == 2


class TestControl:
    def test_shutdown(self, s):
        s.shutdown()
        assert s.active == 0
