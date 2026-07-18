"""Tests for evoid-dashboard."""

import json
import pytest
from unittest.mock import patch, MagicMock
from evoid_dashboard.collectors import (
    collect_services,
    collect_intents,
    collect_processors,
    collect_system_info,
)


class TestCollectors:
    def test_collect_services(self):
        result = collect_services()
        assert isinstance(result, list)

    def test_collect_intents(self):
        result = collect_intents()
        assert isinstance(result, list)

    def test_collect_processors(self):
        result = collect_processors()
        assert isinstance(result, list)

    def test_collect_system_info(self):
        result = collect_system_info()
        assert "python" in result
        assert "evoid_version" in result


class TestASGIApp:
    @pytest.mark.asyncio
    async def test_index_returns_html(self):
        from evoid_dashboard.app import app

        sent = []
        async def send(msg):
            sent.append(msg)

        await app({"type": "http", "path": "/", "method": "GET"}, None, send)

        assert sent[0]["status"] == 200
        body = sent[1]["body"]
        assert b"EVOID Dashboard" in body

    @pytest.mark.asyncio
    async def test_api_all_returns_json(self):
        from evoid_dashboard.app import app

        sent = []
        async def send(msg):
            sent.append(msg)

        await app({"type": "http", "path": "/api/all", "method": "GET"}, None, send)

        assert sent[0]["status"] == 200
        body = json.loads(sent[1]["body"])
        assert "services" in body
        assert "intents" in body

    @pytest.mark.asyncio
    async def test_404(self):
        from evoid_dashboard.app import app

        sent = []
        async def send(msg):
            sent.append(msg)

        await app({"type": "http", "path": "/nonexistent", "method": "GET"}, None, send)

        assert sent[0]["status"] == 404
