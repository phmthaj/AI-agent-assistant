from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolExecution:
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


@dataclass
class AgentState:
    conversation_id: int
    agent_run_id: int
    messages: list[dict[str, Any]]
    tool_executions: list[ToolExecution] = field(default_factory=list)
