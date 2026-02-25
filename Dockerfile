FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies first for layer caching
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --no-dev --no-install-project

# Copy source and install the project
COPY src/ src/
RUN uv sync --no-dev

ENV KAFKA_CONNECT_URL=http://kafka-connect:8083

EXPOSE 8000

ENTRYPOINT ["uv", "run", "kafka-connect-mcp", "--transport", "sse"]
