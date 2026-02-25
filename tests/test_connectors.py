"""Tests for connector CRUD tools."""

from __future__ import annotations

import httpx
import pytest
import respx

from kafka_connect_mcp.server import (
    create_connector,
    delete_connector,
    get_connector,
    get_connector_config,
    get_connector_status,
    list_connectors,
    pause_connector,
    restart_connector,
    resume_connector,
    update_connector_config,
)


def test_list_connectors(mock_api: respx.MockRouter) -> None:
    mock_api.get("/connectors").mock(
        return_value=httpx.Response(200, json=["sink-a", "source-b"])
    )
    assert list_connectors() == ["sink-a", "source-b"]


def test_list_connectors_empty(mock_api: respx.MockRouter) -> None:
    mock_api.get("/connectors").mock(
        return_value=httpx.Response(200, json=[])
    )
    assert list_connectors() == []


def test_get_connector(mock_api: respx.MockRouter) -> None:
    payload = {
        "name": "my-sink",
        "config": {"connector.class": "FileStreamSink"},
        "tasks": [{"connector": "my-sink", "task": 0}],
    }
    mock_api.get("/connectors/my-sink").mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = get_connector("my-sink")
    assert result["name"] == "my-sink"
    assert result["config"]["connector.class"] == "FileStreamSink"


def test_get_connector_not_found(mock_api: respx.MockRouter) -> None:
    mock_api.get("/connectors/missing").mock(
        return_value=httpx.Response(404, json={"error_code": 404, "message": "not found"})
    )
    with pytest.raises(httpx.HTTPStatusError):
        get_connector("missing")


def test_get_connector_status(mock_api: respx.MockRouter) -> None:
    payload = {
        "name": "my-sink",
        "connector": {"state": "RUNNING", "worker_id": "w1:8083"},
        "tasks": [{"id": 0, "state": "RUNNING", "worker_id": "w1:8083"}],
    }
    mock_api.get("/connectors/my-sink/status").mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = get_connector_status("my-sink")
    assert result["connector"]["state"] == "RUNNING"


def test_get_connector_config(mock_api: respx.MockRouter) -> None:
    cfg = {"connector.class": "FileStreamSink", "topics": "test-topic"}
    mock_api.get("/connectors/my-sink/config").mock(
        return_value=httpx.Response(200, json=cfg)
    )
    result = get_connector_config("my-sink")
    assert result["topics"] == "test-topic"


def test_create_connector(mock_api: respx.MockRouter) -> None:
    config = {"connector.class": "FileStreamSink", "topics": "test"}
    response_payload = {"name": "new-sink", "config": config, "tasks": []}

    route = mock_api.post("/connectors").mock(
        return_value=httpx.Response(201, json=response_payload)
    )
    result = create_connector("new-sink", config)
    assert result["name"] == "new-sink"

    # Verify the request body
    request = route.calls[0].request
    import json
    body = json.loads(request.content)
    assert body["name"] == "new-sink"
    assert body["config"] == config


def test_create_connector_conflict(mock_api: respx.MockRouter) -> None:
    mock_api.post("/connectors").mock(
        return_value=httpx.Response(409, json={"error_code": 409, "message": "already exists"})
    )
    with pytest.raises(httpx.HTTPStatusError):
        create_connector("dup", {"connector.class": "X"})


def test_update_connector_config(mock_api: respx.MockRouter) -> None:
    new_config = {"connector.class": "FileStreamSink", "topics": "updated"}
    response_payload = {"name": "my-sink", "config": new_config, "tasks": []}

    mock_api.put("/connectors/my-sink/config").mock(
        return_value=httpx.Response(200, json=response_payload)
    )
    result = update_connector_config("my-sink", new_config)
    assert result["config"]["topics"] == "updated"


def test_delete_connector(mock_api: respx.MockRouter) -> None:
    mock_api.delete("/connectors/my-sink").mock(
        return_value=httpx.Response(204)
    )
    result = delete_connector("my-sink")
    assert "my-sink" in result
    assert "deleted" in result.lower()


def test_delete_connector_not_found(mock_api: respx.MockRouter) -> None:
    mock_api.delete("/connectors/missing").mock(
        return_value=httpx.Response(404, json={"error_code": 404, "message": "not found"})
    )
    with pytest.raises(httpx.HTTPStatusError):
        delete_connector("missing")


def test_pause_connector(mock_api: respx.MockRouter) -> None:
    mock_api.put("/connectors/my-sink/pause").mock(
        return_value=httpx.Response(202)
    )
    result = pause_connector("my-sink")
    assert "paused" in result.lower()


def test_resume_connector(mock_api: respx.MockRouter) -> None:
    mock_api.put("/connectors/my-sink/resume").mock(
        return_value=httpx.Response(202)
    )
    result = resume_connector("my-sink")
    assert "resumed" in result.lower()


def test_restart_connector_simple(mock_api: respx.MockRouter) -> None:
    route = mock_api.post("/connectors/my-sink/restart").mock(
        return_value=httpx.Response(204)
    )
    result = restart_connector("my-sink")
    assert "restarted" in result.lower()
    # No query params by default
    assert route.calls[0].request.url.params.multi_items() == []


def test_restart_connector_with_tasks(mock_api: respx.MockRouter) -> None:
    route = mock_api.post("/connectors/my-sink/restart").mock(
        return_value=httpx.Response(204)
    )
    restart_connector("my-sink", include_tasks=True, only_failed=True)
    params = dict(route.calls[0].request.url.params.multi_items())
    assert params["includeTasks"] == "true"
    assert params["onlyFailed"] == "true"
