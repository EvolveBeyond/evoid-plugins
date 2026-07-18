"""EVOID Plugin Base — shared contracts and utilities for all plugins."""

from .contracts import StorageEngine, CacheEngine, LoggerEngine
from .utils import resolve_engine, inject_deps

__all__ = [
    "StorageEngine",
    "CacheEngine",
    "LoggerEngine",
    "resolve_engine",
    "inject_deps",
]
