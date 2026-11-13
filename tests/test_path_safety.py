"""Tests that user-supplied names cannot alter the REST endpoint path."""

from __future__ import annotations

import httpx
import pytest
import respx

from kafka_connect_mcp.safety import PolicyBlockedError
from kafka_connect_mcp.server import (
    delete_connector,
    get_connector,
    restart_task,
    validate_connector_config,
)


def test_connector_name_is_path_encoded(mock_api: respx.MockRouter) -> None:
    route = mock_api.get(url__regex=r".*").mock(
        return_value=httpx.Response(200, json={})
    )
    get_connector("a/../../connector-plugins")
    assert route.calls.last.request.url.raw_path == (
        b"/connectors/a%2F..%2F..%2Fconnector-plugins"
    )


def test_name_cannot_target_other_endpoint(mock_api: respx.MockRouter) -> None:
    route = mock_api.delete(url__regex=r".*").mock(
        return_value=httpx.Response(204)
    )
    delete_connector("foo/pause?x=1")
    assert route.calls.last.request.url.raw_path == (
        b"/connectors/foo%2Fpause%3Fx%3D1"
    )


@pytest.mark.parametrize("bad", ["", ".", ".."])
def test_dot_segments_rejected(bad: str) -> None:
    with pytest.raises(ValueError):
        get_connector(bad)


def test_allowlist_not_bypassable_by_traversal(
    mock_api: respx.MockRouter, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("KAFKA_CONNECT_MUTATION_ALLOWLIST", "allowed")
    with pytest.raises(PolicyBlockedError):
        restart_task("allowed/../other", 0)


def test_plugin_class_is_path_encoded(mock_api: respx.MockRouter) -> None:
    route = mock_api.put(url__regex=r".*").mock(
        return_value=httpx.Response(200, json={})
    )
    validate_connector_config("a/../b", {})
    assert route.calls.last.request.url.raw_path == (
        b"/connector-plugins/a%2F..%2Fb/config/validate"
    )
