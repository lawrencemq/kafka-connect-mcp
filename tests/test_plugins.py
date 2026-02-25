"""Tests for plugin tools."""

from __future__ import annotations

import httpx
import respx

from kafka_connect_mcp.server import list_connector_plugins, validate_connector_config


def test_list_connector_plugins(mock_api: respx.MockRouter) -> None:
    payload = [
        {"class": "org.apache.kafka.connect.file.FileStreamSinkConnector", "type": "sink"},
        {"class": "org.apache.kafka.connect.file.FileStreamSourceConnector", "type": "source"},
    ]
    mock_api.get("/connector-plugins").mock(
        return_value=httpx.Response(200, json=payload)
    )
    result = list_connector_plugins()
    assert len(result) == 2
    assert result[0]["type"] == "sink"


def test_validate_connector_config(mock_api: respx.MockRouter) -> None:
    validation_response = {
        "name": "FileStreamSinkConnector",
        "error_count": 1,
        "configs": [
            {
                "value": {"name": "topics", "value": None, "errors": ["Missing required config"]},
            }
        ],
    }
    mock_api.put("/connector-plugins/FileStreamSinkConnector/config/validate").mock(
        return_value=httpx.Response(200, json=validation_response)
    )
    result = validate_connector_config(
        "FileStreamSinkConnector", {"connector.class": "FileStreamSinkConnector"}
    )
    assert result["error_count"] == 1


def test_validate_connector_config_clean(mock_api: respx.MockRouter) -> None:
    validation_response = {
        "name": "FileStreamSinkConnector",
        "error_count": 0,
        "configs": [],
    }
    mock_api.put("/connector-plugins/FileStreamSinkConnector/config/validate").mock(
        return_value=httpx.Response(200, json=validation_response)
    )
    result = validate_connector_config(
        "FileStreamSinkConnector",
        {"connector.class": "FileStreamSinkConnector", "topics": "test", "file": "/tmp/out"},
    )
    assert result["error_count"] == 0
