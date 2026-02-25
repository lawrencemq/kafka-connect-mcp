"""Tests for cluster-level tools."""

from __future__ import annotations

import httpx
import respx

from kafka_connect_mcp.server import get_cluster_info


def test_get_cluster_info(mock_api: respx.MockRouter) -> None:
    payload = {
        "version": "7.7.0-ce",
        "commit": "abc123",
        "kafka_cluster_id": "cluster-1",
    }
    mock_api.get("/").mock(return_value=httpx.Response(200, json=payload))

    result = get_cluster_info()
    assert result["version"] == "7.7.0-ce"
    assert result["kafka_cluster_id"] == "cluster-1"
