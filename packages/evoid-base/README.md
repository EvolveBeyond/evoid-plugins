# evoid-base

Base contracts and utilities for EVOID plugins.

## Install

```bash
pip install evoid-base
```

## What's Inside

Shared protocols that all EVOID plugins implement:

- `StorageEngine` — `write()`, `read()`, `delete()`, `health()`
- `CacheEngine` — `get()`, `set()`, `delete()`, `exists()`, `health()`
- `LoggerEngine` — `info()`, `warning()`, `error()`, `debug()`

```python
from evoid_base.contracts import StorageEngine, CacheEngine, LoggerEngine
```

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)

## License

MIT
