"""Safety policy for mutating Kafka Connect operations."""

from __future__ import annotations

import os

CAPABILITY_ENVS: dict[str, str] = {
    "create": "KAFKA_CONNECT_ENABLE_CREATE",
    "update": "KAFKA_CONNECT_ENABLE_UPDATE",
    "delete": "KAFKA_CONNECT_ENABLE_DELETE",
    "pause_resume": "KAFKA_CONNECT_ENABLE_PAUSE_RESUME",
    "restart": "KAFKA_CONNECT_ENABLE_RESTART",
}

TOOL_CAPABILITIES: dict[str, str] = {
    "create_connector": "create",
    "update_connector_config": "update",
    "delete_connector": "delete",
    "pause_connector": "pause_resume",
    "resume_connector": "pause_resume",
    "restart_connector": "restart",
    "restart_task": "restart",
}


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


def _env_csv(name: str) -> set[str]:
    raw = os.getenv(name, "")
    values = (v.strip() for v in raw.split(","))
    return {v for v in values if v}


class PolicyBlockedError(RuntimeError):
    """Raised when a mutating tool is blocked by policy."""

    def __init__(
        self,
        *,
        tool: str,
        reason: str,
        required_env: list[str],
        connector: str | None = None,
    ) -> None:
        self.details = {
            "type": "policy_blocked",
            "tool": tool,
            "reason": reason,
            "required_env": required_env,
            "connector": connector,
        }
        required = ", ".join(required_env)
        connector_hint = f" for connector '{connector}'" if connector else ""
        super().__init__(
            f"{tool} is blocked{connector_hint}: {reason}. "
            f"Set {required} to enable."
        )


def enforce_mutation_allowed(
    *,
    tool: str,
    connector: str | None = None,
) -> None:
    """Ensure the requested mutating tool is enabled by current policy."""
    capability = TOOL_CAPABILITIES[tool]
    capability_env = CAPABILITY_ENVS[capability]
    if not _env_bool(capability_env, False):
        raise PolicyBlockedError(
            tool=tool,
            connector=connector,
            reason=f"capability '{capability}' is disabled",
            required_env=[f"{capability_env}=true"],
        )

    allowlist = _env_csv("KAFKA_CONNECT_MUTATION_ALLOWLIST")
    if connector and allowlist and connector not in allowlist:
        raise PolicyBlockedError(
            tool=tool,
            connector=connector,
            reason="connector is not in KAFKA_CONNECT_MUTATION_ALLOWLIST",
            required_env=[
                f"KAFKA_CONNECT_MUTATION_ALLOWLIST={connector}",
            ],
        )
