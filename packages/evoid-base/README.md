<p align="center">
  <img src="https://img.shields.io/pypi/v/evoid-base?style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI">
  <img src="https://img.shields.io/pypi/pyversions/evoid-base?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/pypi/l/evoid-base?style=for-the-badge" alt="License">
</p>

<h1 align="center">evoid-base</h1>

<p align="center">
  <strong>Shared contracts and protocols for all EVOID plugins</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#contracts">Contracts</a> •
  <a href="#installation">Install</a> •
  <a href="https://evolvebeyond.github.io/EVOID/">Docs</a>
</p>

---

## What is this?

`evoid-base` defines the interface contracts that all EVOID storage, cache, and logging plugins implement. You don't install this directly — it comes with `evoid`. But if you're writing a custom plugin, these are the protocols you implement.

## Contracts

### StorageEngine

```python
from evoid_base.contracts import StorageEngine

class StorageEngine(Protocol):
    async def read(self, key: str) -> Any | None: ...
    async def write(self, key: str, value: Any) -> bool: ...
    async def delete(self, key: str) -> bool: ...
    async def health(self) -> bool: ...
```

### CacheEngine

```python
from evoid_base.contracts import CacheEngine

class CacheEngine(Protocol):
    async def get(self, key: str) -> Any | None: ...
    async def set(self, key: str, value: Any, ttl: float | None = None) -> bool: ...
    async def delete(self, key: str) -> bool: ...
    async def health(self) -> bool: ...
```

### LoggerEngine

```python
from evoid_base.contracts import LoggerEngine

class LoggerEngine(Protocol):
    def info(self, msg: str, **kwargs) -> None: ...
    def warning(self, msg: str, **kwargs) -> None: ...
    def error(self, msg: str, **kwargs) -> None: ...
    def debug(self, msg: str, **kwargs) -> None: ...
```

## Writing a Plugin

Implement the contract as plain functions or a class:

```python
from evoid.engines.plugin import register
from evoid_base.contracts import StorageEngine

class MyStorage:
    async def read(self, key: str) -> Any | None:
        ...

    async def write(self, key: str, value: Any) -> bool:
        ...

    async def delete(self, key: str) -> bool:
        ...

    async def health(self) -> bool:
        return True

def register_plugin():
    register("my-storage", "storage", MyStorage, version="1.0.0")
```

## Installation

```bash
pip install evoid-base
```

Or via EVOID CLI:

```bash
evo install base
```

## Links

- [EVOID Runtime](https://github.com/EvolveBeyond/EVOID)
- [Documentation](https://evolvebeyond.github.io/EVOID/)
- [Plugin Standard](https://evolvebeyond.github.io/EVOID/learn/plugin-standard/)

## License

MIT
