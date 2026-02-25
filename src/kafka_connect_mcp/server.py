"""Kafka Connect MCP Server.

Translates MCP tool calls into Kafka Connect REST API requests.
"""

from __future__ import annotations

import os

import httpx
from fastmcp import FastMCP
from kafka_connect_mcp.safety import enforce_mutation_allowed

CONNECT_URL = os.environ.get("KAFKA_CONNECT_URL", "http://localhost:8083")

mcp = FastMCP("kafka-connect", instructions="Manage Kafka Connect connectors")


def _client() -> httpx.Client:
    return httpx.Client(base_url=CONNECT_URL, timeout=30)


# ── Cluster ───────────────────────────────────────────────────


@mcp.tool()
def get_cluster_info() -> dict:
    """Get Kafka Connect cluster information and version."""
    with _client() as c:
        return c.get("/").json()


# ── Connectors ────────────────────────────────────────────────


@mcp.tool()
def list_connectors() -> list[str]:
    """List all connector names in the cluster."""
    with _client() as c:
        return c.get("/connectors").json()


@mcp.tool()
def get_connector(name: str) -> dict:
    """Get connector info including config and tasks."""
    with _client() as c:
        resp = c.get(f"/connectors/{name}")
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def get_connector_status(name: str) -> dict:
    """Get the status of a connector and all its tasks."""
    with _client() as c:
        resp = c.get(f"/connectors/{name}/status")
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def get_connector_config(name: str) -> dict:
    """Get the configuration for a connector."""
    with _client() as c:
        resp = c.get(f"/connectors/{name}/config")
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def create_connector(name: str, config: dict) -> dict:
    """Create a new connector.

    The config dict should include 'connector.class' and all required
    properties for that connector type.
    """
    enforce_mutation_allowed(tool="create_connector", connector=name)
    with _client() as c:
        resp = c.post("/connectors", json={"name": name, "config": config})
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def update_connector_config(name: str, config: dict) -> dict:
    """Update (or create) a connector's configuration. This is a full replace."""
    enforce_mutation_allowed(tool="update_connector_config", connector=name)
    with _client() as c:
        resp = c.put(f"/connectors/{name}/config", json=config)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def delete_connector(name: str) -> str:
    """Delete a connector and all its tasks."""
    enforce_mutation_allowed(tool="delete_connector", connector=name)
    with _client() as c:
        resp = c.delete(f"/connectors/{name}")
        resp.raise_for_status()
        return f"Connector '{name}' deleted."


@mcp.tool()
def pause_connector(name: str) -> str:
    """Pause a running connector."""
    enforce_mutation_allowed(tool="pause_connector", connector=name)
    with _client() as c:
        resp = c.put(f"/connectors/{name}/pause")
        resp.raise_for_status()
        return f"Connector '{name}' paused."


@mcp.tool()
def resume_connector(name: str) -> str:
    """Resume a paused connector."""
    enforce_mutation_allowed(tool="resume_connector", connector=name)
    with _client() as c:
        resp = c.put(f"/connectors/{name}/resume")
        resp.raise_for_status()
        return f"Connector '{name}' resumed."


@mcp.tool()
def restart_connector(
    name: str, include_tasks: bool = False, only_failed: bool = False
) -> str:
    """Restart a connector. Optionally restart its tasks too."""
    enforce_mutation_allowed(tool="restart_connector", connector=name)
    with _client() as c:
        params: dict[str, str] = {}
        if include_tasks:
            params["includeTasks"] = "true"
        if only_failed:
            params["onlyFailed"] = "true"
        resp = c.post(f"/connectors/{name}/restart", params=params)
        resp.raise_for_status()
        return f"Connector '{name}' restarted."


# ── Tasks ─────────────────────────────────────────────────────


@mcp.tool()
def get_task_status(connector_name: str, task_id: int) -> dict:
    """Get the status of a specific task for a connector."""
    with _client() as c:
        resp = c.get(f"/connectors/{connector_name}/tasks/{task_id}/status")
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def restart_task(connector_name: str, task_id: int) -> str:
    """Restart a specific task."""
    enforce_mutation_allowed(tool="restart_task", connector=connector_name)
    with _client() as c:
        resp = c.post(
            f"/connectors/{connector_name}/tasks/{task_id}/restart"
        )
        resp.raise_for_status()
        return f"Task {task_id} of '{connector_name}' restarted."


# ── Plugins ───────────────────────────────────────────────────


@mcp.tool()
def list_connector_plugins() -> list[dict]:
    """List available connector plugins on the cluster."""
    with _client() as c:
        return c.get("/connector-plugins").json()


@mcp.tool()
def validate_connector_config(plugin_class: str, config: dict) -> dict:
    """Validate a connector config against its plugin's schema.

    Returns per-field validation errors if any.
    """
    with _client() as c:
        resp = c.put(
            f"/connector-plugins/{plugin_class}/config/validate", json=config
        )
        return resp.json()


# ── Entry point ───────────────────────────────────────────────


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="MCP transport (default: stdio)",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for SSE transport"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port for SSE transport"
    )
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
