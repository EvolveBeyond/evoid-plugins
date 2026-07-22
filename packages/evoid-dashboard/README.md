<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-dashboard?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-dashboard?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-dashboard?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-dashboard</h1>

<p align="center">
  <strong>Monitoring dashboard — Intent Handler system</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#intent-handler">Intent Handler</a> •
  <a href="#api-endpoints">API Endpoints</a>
</p>

---

## Quick Start

```bash
uv add evoid-dashboard
```

### Method 1: Intent Handler (Recommended)

```python
from evoid_dashboard import register_handlers

# Register dashboard as adapter handler
register_handlers(host="0.0.0.0", port=8001)
```

### Method 2: Direct API

```python
from evoid_dashboard import create_dashboard

app = create_dashboard(port=8001)
```

---

## Intent Handler

evoid-dashboard registers monitoring endpoints as Intent handlers.

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/services` | GET | List all registered services |
| `/intents` | GET | List all registered intents |
| `/processors` | GET | List all registered processors |
| `/messages` | GET | Message bus history |
| `/health` | GET | Dashboard health check |

---

## Configuration

### TOML

```toml
[engines]
dashboard = "dashboard"

[engines.options.dashboard]
host = "0.0.0.0"
port = 8001
```

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
