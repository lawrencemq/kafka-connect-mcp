"""Shared fixtures for Kafka Connect MCP tests."""

from __future__ import annotations

import pytest
import respx

from kafka_connect_mcp import server


@pytest.fixture(autouse=True)
def _mock_connect_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point all tests at a fake base URL so nothing hits the network."""
    monkeypatch.setattr(server, "CONNECT_URL", "http://fake-connect:8083")


@pytest.fixture(autouse=True)
def _enable_mutating_tools_for_existing_tests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep existing mutation tests explicit now that read-only is the default."""
    monkeypatch.setenv("KAFKA_CONNECT_ENABLE_CREATE", "true")
    monkeypatch.setenv("KAFKA_CONNECT_ENABLE_UPDATE", "true")
    monkeypatch.setenv("KAFKA_CONNECT_ENABLE_DELETE", "true")
    monkeypatch.setenv("KAFKA_CONNECT_ENABLE_PAUSE_RESUME", "true")
    monkeypatch.setenv("KAFKA_CONNECT_ENABLE_RESTART", "true")


@pytest.fixture()
def mock_api() -> respx.MockRouter:
    """Provide a respx mock router scoped to the fake Connect URL."""
    with respx.mock(base_url="http://fake-connect:8083") as router:
        yield router
