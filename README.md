# EVOID Plugins

A collection of official plugins for the [EVOID](https://github.com/EvolveBeyond/EVOID) runtime.

Each plugin is an independent Python package. Install only what you need.

## Available Plugins

| Plugin | Package | Description |
|--------|---------|-------------|
| SQLite Storage | `evoid-sqlite` | SQLite storage engine |
| PostgreSQL Storage | `evoid-postgresql` | PostgreSQL storage engine |
| Redis Cache | `evoid-redis` | Redis cache engine |
| Smart Storage | `evoid-smart-storage` | Multi-DB routing, schema enforcement, multi-tenancy |
| DI Engine | `evoid-di` | Dependency injection engine |
| Auth Engine | `evoid-auth` | Authentication & authorization |
| Background Tasks | `evoid-tasks` | Background task scheduling |
| Loguru Logger | `evoid-loguru` | Loguru logging engine |

## Installation

```bash
# Install individual plugins
pip install evoid-sqlite
pip install evoid-redis

# Or install with EVOID extras
pip install "evoid[sqlite,redis]"
```

## Development

Each plugin lives in its own directory with its own `pyproject.toml`:

```
evoid-plugins/
├── packages/
│   ├── evoid-sqlite/
│   │   ├── pyproject.toml
│   │   └── evoid_sqlite/
│   ├── evoid-postgresql/
│   │   ├── pyproject.toml
│   │   └── evoid_postgresql/
│   ├── evoid-redis/
│   │   ├── pyproject.toml
│   │   └── evoid_redis/
│   ├── evoid-di/
│   │   ├── pyproject.toml
│   │   └── evoid_di/
│   ├── evoid-auth/
│   │   ├── pyproject.toml
│   │   └── evoid_auth/
│   ├── evoid-tasks/
│   │   ├── pyproject.toml
│   │   └── evoid_tasks/
│   └── evoid-loguru/
│       ├── pyproject.toml
│       └── evoid_loguru/
├── pyproject.toml          # Workspace root
└── README.md
```

## Plugin Standard

Every plugin must have:

1. `pyproject.toml` with `evoid>=0.4.0` dependency
2. `evoid_plugin.json` manifest
3. `register_plugin()` entry point
4. IOP-compliant code (data + functions, no classes with behavior)

See [Plugin Standard](https://evolvebeyond.github.io/EVOID/learn/plugin-standard/) for details.

## License

MIT
