"""Tests for evoid-base contracts."""

from evoid_base.contracts import StorageEngine, CacheEngine, LoggerEngine


def test_storage_engine_protocol():
    """StorageEngine protocol defines required methods."""
    assert hasattr(StorageEngine, "write")
    assert hasattr(StorageEngine, "read")
    assert hasattr(StorageEngine, "delete")
    assert hasattr(StorageEngine, "health")


def test_cache_engine_protocol():
    """CacheEngine protocol defines required methods."""
    assert hasattr(CacheEngine, "get")
    assert hasattr(CacheEngine, "set")
    assert hasattr(CacheEngine, "delete")
    assert hasattr(CacheEngine, "exists")
    assert hasattr(CacheEngine, "health")


def test_logger_engine_protocol():
    """LoggerEngine protocol defines required methods."""
    assert hasattr(LoggerEngine, "info")
    assert hasattr(LoggerEngine, "warning")
    assert hasattr(LoggerEngine, "error")
    assert hasattr(LoggerEngine, "debug")
