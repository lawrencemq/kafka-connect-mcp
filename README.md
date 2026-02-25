# kafka-connect-mcp

An MCP server that exposes [Kafka Connect REST API](https://docs.confluent.io/platform/current/connect/references/restapi.html) operations as tools, letting LLMs manage connectors, tasks, and plugins through natural language.

## Tools

| Tool | Kafka Connect Endpoint | Description |
|------|----------------------|-------------|
| `get_cluster_info` | `GET /` | Cluster version and metadata |
| `list_connectors` | `GET /connectors` | List all connector names |
| `get_connector` | `GET /connectors/{name}` | Connector info, config, and tasks |
| `get_connector_status` | `GET /connectors/{name}/status` | Connector and task states |
| `get_connector_config` | `GET /connectors/{name}/config` | Connector configuration |
| `create_connector` | `POST /connectors` | Create a new connector |
| `update_connector_config` | `PUT /connectors/{name}/config` | Replace connector configuration |
| `delete_connector` | `DELETE /connectors/{name}` | Delete a connector |
| `pause_connector` | `PUT /connectors/{name}/pause` | Pause a connector |
| `resume_connector` | `PUT /connectors/{name}/resume` | Resume a paused connector |
| `restart_connector` | `POST /connectors/{name}/restart` | Restart a connector (optionally tasks) |
| `get_task_status` | `GET /connectors/{name}/tasks/{id}/status` | Status of a specific task |
| `restart_task` | `POST /connectors/{name}/tasks/{id}/restart` | Restart a specific task |
| `list_connector_plugins` | `GET /connector-plugins` | Available plugins on the cluster |
| `validate_connector_config` | `PUT /connector-plugins/{name}/config/validate` | Validate config against plugin schema |

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- A running Kafka Connect cluster (or use the included Docker Compose)

### Install

```bash
uv sync
```

### Add to Claude Code

```bash
claude mcp add kafka-connect \
  -e KAFKA_CONNECT_URL=http://localhost:8083 \
  -- uv --directory /path/to/kafka-connect-mcp run kafka-connect-mcp
```

### Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `KAFKA_CONNECT_URL` | `http://localhost:8083` | Kafka Connect REST API base URL |

## Running

### stdio (default, for Claude Code)

```bash
KAFKA_CONNECT_URL=http://localhost:8083 uv run kafka-connect-mcp
```

### SSE (for Docker / remote)

```bash
uv run kafka-connect-mcp --transport sse --host 0.0.0.0 --port 8000
```

### Docker Compose (full stack)

Spins up Zookeeper, Kafka, Kafka Connect (with the Datagen plugin), and the MCP server:

```bash
docker compose up --build -d
```

| Service | Port | Description |
|---------|------|-------------|
| zookeeper | 2181 | ZooKeeper |
| kafka | 9092 | Kafka broker |
| kafka-connect | 8083 | Kafka Connect REST API |
| mcp-server | 8000 | MCP server (SSE transport) |

### Example: create a Datagen connector

Once the stack is up, ask Claude to create a datagen connector, or do it directly:

```bash
curl -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "datagen-users",
    "config": {
      "connector.class": "io.confluent.kafka.connect.datagen.DatagenConnector",
      "kafka.topic": "users",
      "quickstart": "users",
      "key.converter": "org.apache.kafka.connect.storage.StringConverter",
      "value.converter": "org.apache.kafka.connect.json.JsonConverter",
      "value.converter.schemas.enable": "false",
      "max.interval": "1000",
      "tasks.max": "1"
    }
  }'
```

## Tests

```bash
uv run pytest tests/ -v
```

Tests use [respx](https://lundberg.github.io/respx/) to mock HTTP calls to the Kafka Connect API -- no running cluster required.

## Project structure

```
kafka-connect-mcp/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── src/kafka_connect_mcp/
│   ├── __init__.py
│   └── server.py            # All MCP tools and entry point
└── tests/
    ├── conftest.py           # Shared fixtures (mock URL + respx router)
    ├── test_cluster.py
    ├── test_connectors.py
    ├── test_tasks.py
    └── test_plugins.py
```
