"""Tests for task-level tools."""

from __future__ import annotations

import httpx
import respx

from kafka_connect_mcp.server import get_task_status, restart_task


def test_get_task_status(mock_api: respx.MockRouter) -> None:
    payload = {"id": 0, "state": "RUNNING", "worker_id": "w1:8083"}
    mock_api.get("/connectors/my-sink/tasks/0/status").mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = get_task_status("my-sink", 0)
    assert result["state"] == "RUNNING"


def test_get_task_status_failed(mock_api: respx.MockRouter) -> None:
    payload = {
        "id": 1,
        "state": "FAILED",
        "worker_id": "w1:8083",
        "trace": "java.lang.RuntimeException: boom",
    }
    mock_api.get("/connectors/my-sink/tasks/1/status").mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = get_task_status("my-sink", 1)
    assert result["state"] == "FAILED"
    assert "boom" in result["trace"]


def test_restart_task(mock_api: respx.MockRouter) -> None:
    mock_api.post("/connectors/my-sink/tasks/0/restart").mock(
        return_value=httpx.Response(204)
    )
    result = restart_task("my-sink", 0)
    assert "restarted" in result.lower()
    assert "my-sink" in result
