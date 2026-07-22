<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-scheduler?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-scheduler?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-scheduler?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-scheduler</h1>

<p align="center">
  <strong>Priority-aware scheduler — Intent Handler system</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#intent-handler">Intent Handler</a> •
  <a href="#features">Features</a> •
  <a href="#api">API</a>
</p>

---

## Quick Start

```bash
uv add evoid-scheduler
```

### Method 1: Intent Handler (Recommended)

```python
from evoid_scheduler import register_handlers

# Register scheduler as Intent handlers
register_handlers(max_workers=4)
```

### Method 2: Direct API

```python
from evoid_scheduler import SchedulerEngine, Priority

scheduler = SchedulerEngine()
await scheduler.submit(intent=process_payment, priority=Priority.CRITICAL)
```

---

## Intent Handler

evoid-scheduler registers priority-aware task scheduling as Intent handlers.

---

## Features

- **True priority queue** — O(log n) enqueue/dequeue
- **System metrics** — CPU cores, load average, memory usage
- **Adaptive concurrency** — Adjusts based on system load
- **Task deferral** — Low-priority tasks deferred when system is busy
- **Cross-service balancing** — Distribute work across instances

---

## Configuration

### TOML

```toml
[engines]
scheduler = "scheduler"

[engines.options.scheduler]
max_workers = 4
```

---

## API

### `register_handlers(max_workers: int = 4)`

Register scheduler as Intent handlers.

### SchedulerEngine Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `submit` | `async submit(intent, priority, ...)` | Submit task with priority |
| `metrics` | `metrics()` | Get system metrics |
| `active` | `active` | Count of running tasks |

### Priority Levels

| Priority | Value | Use Case |
|----------|-------|----------|
| `CRITICAL` | 1 | Payments, medical |
| `HIGH` | 2 | User requests |
| `NORMAL` | 3 | Background jobs |
| `LOW` | 4 | Analytics, logging |

---

## DI Integration

All plugins register with evoid-di for automatic service discovery and fault tolerance.

```python
from evoid_di import di

# Resolve with fallback
storage = di.resolve_with_fallback("storage.postgresql")
# Tries: postgresql → sqlite → redis → cluster peers → None
```

## Dependencies

- `evoid>=0.4.0`

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
