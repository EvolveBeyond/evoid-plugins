"""Tests for evoid-sqlite plugin."""

import pytest
from evoid_sqlite import SQLiteStorage, create_storage


@pytest.fixture
async def storage(tmp_path):
    db_path = str(tmp_path / "test.db")
    store = create_storage(db_path)
    await store.connect()
    yield store
    await store.close()


@pytest.mark.asyncio
async def test_write_and_read(storage):
    await storage.write("user:1", {"name": "Alice", "age": 30})
    result = await storage.read("user:1")
    assert result == {"name": "Alice", "age": 30}


@pytest.mark.asyncio
async def test_read_missing(storage):
    result = await storage.read("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_delete(storage):
    await storage.write("key1", "value1")
    deleted = await storage.delete("key1")
    assert deleted is True
    result = await storage.read("key1")
    assert result is None


@pytest.mark.asyncio
async def test_namespaces(storage):
    await storage.write("key1", "value1", namespace="ns1")
    await storage.write("key1", "value2", namespace="ns2")

    v1 = await storage.read("key1", namespace="ns1")
    v2 = await storage.read("key1", namespace="ns2")
    assert v1 == "value1"
    assert v2 == "value2"


@pytest.mark.asyncio
async def test_list_keys(storage):
    await storage.write("a", 1)
    await storage.write("b", 2)
    await storage.write("c", 3)

    keys = await storage.list_keys()
    assert sorted(keys) == ["a", "b", "c"]
