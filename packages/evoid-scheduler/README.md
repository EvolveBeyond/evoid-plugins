<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-scheduler?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-scheduler?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-scheduler?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-scheduler</h1>

<p align="center">
  <strong>Priority-aware scheduler with system metrics and adaptive concurrency for EVOID</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#api">API</a> •
  <a href="#installation">Install</a> •
  <a href="https://evolvebeyond.github.io/EVOID/">Docs</a>
</p>

---

## What is this?

`evoid-scheduler` replaces EVOID's built-in parallel execution with a priority-aware, system-aware scheduler. It understands your system's load, defers low-priority tasks when busy, and distributes work across service instances.

## Quick Start

```bash
pip install evoid-scheduler
```

```python
from evoid_scheduler import Scheduler, Priority

# Initialize with auto-detected CPU cores
scheduler = Scheduler()

# Submit tasks with priority
await scheduler.submit(intent=process_payment, priority=Priority.CRITICAL)
await scheduler.submit(intent=sync_inventory, priority=Priority.LOW)

# Check system state
metrics = scheduler.metrics()
print(f"CPU: {metrics.cpu_cores}, Load: {metrics.load_avg_1m}")
print(f"Overloaded: {metrics.is_overloaded}")
```

## Features

### True Priority Queue

Unlike EVOID's built-in `gather_with_priority` (which only sorts launch order), this provides a real priority queue:

- **O(log n)** enqueue/dequeue operations
- Higher priority tasks execute first
- Equal priority follows FIFO order
- Lock-free implementation (Rust backend optional)

### System Awareness

The scheduler understands your system:

```python
metrics = scheduler.metrics()
# SystemMetrics(
#   cpu_cores=8,
#   cpu_count_logical=16,
#   load_avg_1m=2.3,
#   load_avg_5m=1.8,
#   load_avg_15m=1.2,
#   memory_total_mb=32768,
#   memory_available_mb=24576,
# )

if metrics.is_overloaded:
    print("System is busy, deferring low-priority tasks")
```

### Adaptive Concurrency

Automatically scales workers based on load:

```python
scheduler = Scheduler(
    max_workers=None,       # Auto-detect CPU cores
    load_threshold=0.8,     # Defer when load > 80%
    enable_defer=True,      # Enable task deferral
)
```

### Task Deferral

When the system is overloaded, low-priority tasks are automatically deferred:

```python
# These get deferred when system is busy
await scheduler.submit(intent=cleanup_logs, priority=Priority.BACKGROUND)
await scheduler.submit(intent=sync_analytics, priority=Priority.LOW)

# Process deferred tasks when load drops
await scheduler.process_deferred()
```

### Cross-Service Load Balancing

Uses EVOID's message bus for service discovery:

```python
from evoid_scheduler import LoadBalancer

balancer = LoadBalancer(service_name="order-service")

# Register this instance
await balancer.register(port=8000)

# Get least-loaded instance
target = balancer.least_loaded()
# {"host": "10.0.0.2", "port": 8001, "load": 0.3}
```

### Pipeline Integration

Auto-defer processor for pipeline integration:

```python
from evoid_scheduler import scheduler_processor
from evoid.core.extend import before

# Add to pipeline
before("POST:/orders", "scheduler")

# The processor automatically:
# 1. Checks system load
# 2. Defers low-priority tasks if overloaded
# 3. Reports metrics in ctx.state
```

## API

### `Scheduler`

| Method | Signature | Description |
|--------|-----------|-------------|
| `submit` | `async submit(intent, priority=50)` | Submit intent to queue |
| `cancel` | `async cancel(task_id)` | Cancel queued task |
| `metrics` | `metrics()` | Get system metrics |
| `process_deferred` | `async process_deferred()` | Process deferred tasks |

### `Priority`

| Level | Value | Use Case |
|-------|-------|----------|
| `CRITICAL` | 100 | Payments, auth, security |
| `HIGH` | 75 | User-facing operations |
| `NORMAL` | 50 | Standard processing |
| `LOW` | 25 | Background sync, analytics |
| `BACKGROUND` | 10 | Cleanup, logging |
| `DEFERRED` | 0 | Only when idle |

### `SystemMetrics`

| Property | Type | Description |
|----------|------|-------------|
| `cpu_cores` | `int` | Physical CPU cores |
| `cpu_count_logical` | `int` | Logical processors |
| `load_avg_1m` | `float` | 1-minute load average |
| `load_avg_5m` | `float` | 5-minute load average |
| `load_avg_15m` | `float` | 15-minute load average |
| `memory_total_mb` | `float` | Total memory in MB |
| `memory_available_mb` | `float` | Available memory in MB |
| `is_overloaded` | `bool` | True if load > cores |
| `recommended_concurrency` | `int` | Suggested worker count |

## Configuration

### TOML

```toml
[engines]
scheduler = "scheduler"

[engines.scheduler]
max_workers = 8
load_threshold = 0.8
enable_defer = true
```

### Python

```python
from evoid.config import config

app = config(
    engines={"scheduler": "scheduler"},
)
```

## Rust Backend (Optional)

For maximum performance, install with Rust extensions:

```bash
pip install evoid-scheduler[rust]
```

This enables:
- Lock-free priority queue (no Python GIL contention)
- System metrics via `sysinfo` crate
- ~10x faster queue operations under high concurrency

## How It Works

1. **Submit**: Intent enters priority queue
2. **Check Load**: System metrics collected
3. **Decide**: Execute immediately or defer
4. **Schedule**: Highest priority executes first
5. **Balance**: Distribute across service instances

## Dependencies

- `evoid>=0.4.0` (required)
- `maturin>=1.0.0` (optional, for Rust backend)

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
