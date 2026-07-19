<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-dashboard?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-dashboard?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-dashboard?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-dashboard</h1>

<p align="center">
  <strong>Monitoring dashboard for EVOID — service map, DB viewer, logs</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#api-endpoints">API</a> •
  <a href="#installation">Install</a> •
  <a href="https://evolvebeyond.github.io/EVOID/">Docs</a>
</p>

---

## Quick Start

```bash
pip install evoid-dashboard
```

```python
from evoid_dashboard import create_dashboard

# Start on port 8001
create_dashboard(port=8001)
```

Open `http://localhost:8001` to see:
- Service map with connections
- All registered Intents and processors
- Message bus history
- Database connections
- System info (Python version, platform, EVOID version)

The dashboard auto-refreshes every 5 seconds.

## What It Shows

### Service Map
Groups intents and processors by service prefix. See how your services connect.

### Intent Registry
Every registered intent with level, timeout, priority, and metadata.

### Processor List
All registered processors with coroutine detection.

### Message Bus History
Recent message bus events — source, intent, target.

### Database Viewer
Storage engine introspection from the plugin registry.

### Pipeline Overrides
Custom pipeline configurations from `evoid.core.extend`.

### System Info
Python version, platform, EVOID version.

## API Endpoints

| Path | Returns |
|------|---------|
| `/` | Full SPA HTML dashboard |
| `/api/services` | Services grouped by name |
| `/api/intents` | All registered intents |
| `/api/processors` | All processors |
| `/api/messages` | Message bus history |
| `/api/databases` | Storage engine info |
| `/api/pipelines` | Pipeline overrides |
| `/api/system` | System information |
| `/api/all` | Aggregated payload |

## Configuration

### TOML

```toml
[engines]
dashboard = "dashboard"

[engines.dashboard]
host = "0.0.0.0"
port = 8001
```

### Python

```python
from evoid_dashboard import create_dashboard

create_dashboard(host="0.0.0.0", port=8001)
```

## API

### `create_dashboard(host: str, port: int)`

Starts the dashboard ASGI server.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | `str` | `"0.0.0.0"` | Bind address |
| `port` | `int` | `8001` | Port number |

## Optional Dependencies

- `jinja2>=3.1.0` — for HTML templating
- `uvicorn>=0.30.0` — for ASGI server

Install with:

```bash
pip install "evoid-dashboard[full]"
```

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Collection](https://evolvebeyond.github.io/EVOID/learn/plugin-collection/)

## License

MIT
