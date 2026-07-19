<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-tasks?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-tasks?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-tasks?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-tasks</h1>

<p align="center">
  <strong>Background tasks with Godot-inspired lifecycle for EVOID</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#lifecycle">Lifecycle</a> •
  <a href="#api">API</a> •
  <a href="#installation">Install</a> •
  <a href="https://evolvebeyond.github.io/EVOID/">Docs</a>
</p>

---

## Quick Start

```bash
pip install evoid-tasks
```

### Fire and Forget

```python
from evoid_tasks import scheduler

# Run in background
scheduler.run(send_email, to="alice@example.com")
```

### Periodic Tasks

```python
from evoid_tasks import scheduler, TaskContext

@scheduler.task(interval=60)
async def monitor(ctx: TaskContext):
    if ctx.tick:
        await check_service_health()
```

### Event-Driven

```python
from evoid_tasks import scheduler

@scheduler.on("order_placed")
async def update_stats(ctx):
    await recalc_inventory(ctx.event_data)
```

## Lifecycle

Interval-based tasks follow a Godot-inspired lifecycle:

```
on_start → on_tick (repeats) → on_stop
                ↓
            on_error (on failure)
```

| Hook | When | Use Case |
|------|------|----------|
| `on_start` | Task begins | Initialize resources |
| `on_tick` | Every `interval` seconds | Main work |
| `on_stop` | Task cancelled | Cleanup |
| `on_error` | Tick fails | Error recovery |

### TaskContext

```python
@dataclass
class TaskContext:
    task_name: str       # "monitor"
    started: float       # Start timestamp
    tick: int            # Current tick number
    stopped: bool        # True if shutting down
    delta: float         # Seconds since last tick
    event_data: Any      # Data from emit()
    state: dict          # Persistent state across ticks
```

## Pipeline Integration

### As Processor

```python
from evoid_tasks import scheduler

@scheduler.as_processor("send_welcome_email")
async def send_welcome(ctx):
    await send_email(ctx.state["user"]["email"])
```

### As Intent

```python
from evoid_tasks import scheduler
from evoid import Level

@scheduler.as_intent("process_order", level=Level.CRITICAL)
async def process_order(ctx):
    await charge_card(ctx.state["order"])
```

### Inject into Pipeline

```python
from evoid_tasks import scheduler

@scheduler.inject(task_fn, before="validate", after="authorize")
async def audit_log(ctx):
    await log_action(ctx)
```

## Configuration

```python
from evoid_tasks import TaskScheduler

scheduler = TaskScheduler(max_concurrent=20)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_concurrent` | `int` | `10` | Max concurrent periodic tasks |

## API

### Scheduler

| Method | Signature | Description |
|--------|-----------|-------------|
| `run` | `run(func, *args, **kwargs)` | Fire-and-forget background task |
| `task` | `@scheduler.task(interval=N)` | Register periodic task |
| `on` | `@scheduler.on("event_name")` | Register event handler |
| `emit` | `emit(event, data)` | Fire event to all handlers |
| `as_processor` | `@scheduler.as_processor(name)` | Wrap as EVOID processor |
| `as_intent` | `@scheduler.as_intent(name, level)` | Create Intent + processor |
| `inject` | `inject(fn, before, after)` | Insert into existing pipeline |
| `cancel` | `cancel(task_def)` | Cancel a periodic task |
| `shutdown` | `shutdown()` | Cancel all tasks |

### Convenience Re-exports

```python
from evoid_tasks import run, task, on, emit, as_processor, as_intent, inject
```

## Optional Dependencies

- `loguru>=0.7.0` — for beautiful colored output

Install with:

```bash
pip install "evoid-tasks[loguru]"
```

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
