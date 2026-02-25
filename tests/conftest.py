"""Shared fixtures for Kafka Connect MCP tests."""

from __future__ import annotations

import pytest
import respx

from kafka_connect_mcp import server


@pytest.fixture(autouse=True)
def _mock_connect_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point all tests at a fake base URL so nothing hits the network."""
    monkeypatch.setattr(server, "CONNECT_URL", "http://fake-connect:8083")


@pytest.fixture()
def mock_api() -> respx.MockRouter:
    """Provide a respx mock router scoped to the fake Connect URL."""
    with respx.mock(base_url="http://fake-connect:8083") as router:
        yield router
