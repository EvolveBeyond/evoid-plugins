<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-tasks?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-tasks?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-tasks?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-tasks</h1>

<p align="center">
  <strong>Background tasks with lifecycle — Intent Handler system</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#intent-handler">Intent Handler</a> •
  <a href="#lifecycle">Lifecycle</a> •
  <a href="#api">API</a>
</p>

---

## Quick Start

```bash
pip install evoid-tasks
```

### Method 1: Intent Handler (Recommended)

```python
from evoid_tasks import register_handlers

# Register task scheduler as Intent handlers
register_handlers(max_concurrent=10)
```

### Method 2: Direct API

```python
from evoid_tasks import scheduler

# Fire and forget
scheduler.run(send_email, to="alice@example.com")

# Periodic tasks
@scheduler.task(interval=60)
async def cleanup(ctx):
    await delete_old_sessions()
```

---

## Intent Handler

evoid-tasks registers task scheduling as Intent handlers.

---

## Lifecycle (Godot-inspired)

```python
from evoid_tasks import scheduler, TaskContext

@scheduler.task(interval=10)
async def my_task(ctx: TaskContext):
    # on_start — called once
    print(f"Task {ctx.task_name} started")

    # on_tick — called every interval
    print(f"Tick {ctx.tick}, delta={ctx.delta}")

    # on_stop — called on cancellation
    # on_error — called on exception
```

---

## Configuration

### TOML

```toml
[engines]
tasks = "tasks"

[engines.options.tasks]
max_concurrent = 10
```

---

## API

### `register_handlers(max_concurrent: int = 10)`

Register task scheduler as Intent handlers.

### Scheduler Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `run` | `run(func, *args, **kwargs)` | Fire-and-forget background task |
| `task` | `@task(interval=N)` | Decorator for periodic tasks |
| `on` | `@on(event)` | Listen for named events |
| `emit` | `emit(event, data)` | Emit event to all handlers |
| `cancel` | `cancel(task_def)` | Cancel a running task |
| `shutdown` | `shutdown()` | Cancel all tasks |

---

## Dependencies

- `evoid>=0.4.0`

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
