from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: int | None = None


class ToolCallResponse(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


class ChatResponse(BaseModel):
    conversation_id: int
    agent_run_id: int
    answer: str
    tool_calls: list[ToolCallResponse] = []
