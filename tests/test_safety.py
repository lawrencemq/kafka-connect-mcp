"""Tests for read-only safe mode and mutation feature gates."""

from __future__ import annotations

import httpx
import pytest
import respx

from kafka_connect_mcp.safety import PolicyBlockedError
from kafka_connect_mcp.server import (
    create_connector,
    delete_connector,
    restart_task,
)


def test_create_capability_blocks_mutations_by_default(
    monkeypatch: pytest.MonkeyPatch, mock_api: respx.MockRouter
) -> None:
    monkeypatch.delenv("KAFKA_CONNECT_ENABLE_CREATE", raising=False)

    with pytest.raises(PolicyBlockedError) as exc:
        create_connector("new-sink", {"connector.class": "FileStreamSink"})

    assert exc.value.details["reason"] == "capability 'create' is disabled"
    assert "KAFKA_CONNECT_ENABLE_CREATE=true" in exc.value.details["required_env"]
    assert len(mock_api.calls) == 0


def test_capability_gate_blocks_when_disabled(
    monkeypatch: pytest.MonkeyPatch, mock_api: respx.MockRouter
) -> None:
    monkeypatch.setenv("KAFKA_CONNECT_ENABLE_DELETE", "false")

    with pytest.raises(PolicyBlockedError) as exc:
        delete_connector("my-sink")

    assert exc.value.details["reason"] == "capability 'delete' is disabled"
    assert "KAFKA_CONNECT_ENABLE_DELETE=true" in exc.value.details["required_env"]
    assert len(mock_api.calls) == 0


def test_allowlist_blocks_non_listed_connector(
    monkeypatch: pytest.MonkeyPatch, mock_api: respx.MockRouter
) -> None:
    monkeypatch.setenv("KAFKA_CONNECT_ENABLE_RESTART", "true")
    monkeypatch.setenv("KAFKA_CONNECT_MUTATION_ALLOWLIST", "allowed-a,allowed-b")

    with pytest.raises(PolicyBlockedError) as exc:
        restart_task("my-sink", 0)

    assert (
        exc.value.details["reason"]
        == "connector is not in KAFKA_CONNECT_MUTATION_ALLOWLIST"
    )
    assert exc.value.details["connector"] == "my-sink"
    assert len(mock_api.calls) == 0


def test_allowlist_allows_listed_connector(
    monkeypatch: pytest.MonkeyPatch, mock_api: respx.MockRouter
) -> None:
    monkeypatch.setenv("KAFKA_CONNECT_ENABLE_RESTART", "true")
    monkeypatch.setenv("KAFKA_CONNECT_MUTATION_ALLOWLIST", "my-sink")
    mock_api.post("/connectors/my-sink/tasks/0/restart").mock(
        return_value=httpx.Response(204)
    )

    result = restart_task("my-sink", 0)
    assert "restarted" in result.lower()
