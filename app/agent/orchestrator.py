import json
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from openai import APIError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import AgentState, ToolExecution
from app.config import Settings
from app.llm import LLMClient
from app.memory import RedisShortTermMemory
from app.models import AgentRun, Conversation, Message, ToolCall
from app.tools import ToolRegistry


SYSTEM_PROMPT = """You are a helpful AI agent.
Use tools when they are useful for accuracy or computation.
When you call tools, inspect their results before answering.
Return a concise final answer to the user."""


class AgentOrchestrator:
    def __init__(
        self,
        db: AsyncSession,
        llm: LLMClient,
        tools: ToolRegistry,
        settings: Settings,
        memory: RedisShortTermMemory | None = None,
    ) -> None:
        self._db = db
        self._llm = llm
        self._tools = tools
        self._settings = settings
        self._memory = memory

    async def run(
        self,
        user_message: str,
        conversation_id: int | None = None,
    ) -> dict[str, Any]:
        conversation = await self._get_or_create_conversation(conversation_id)
        history = await self._load_short_term_history(conversation.id)

        self._db.add(
            Message(
                conversation_id=conversation.id,
                role="user",
                content=user_message,
            )
        )

        agent_run = AgentRun(
            conversation_id=conversation.id,
            status="running",
        )
        self._db.add(agent_run)
        await self._db.flush()

        state = AgentState(
            conversation_id=conversation.id,
            agent_run_id=agent_run.id,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *history,
                {"role": "user", "content": user_message},
            ],
        )

        try:
            answer = await self._agent_loop(state)
        except Exception:
            agent_run.status = "failed"
            agent_run.finished_at = datetime.utcnow()
            await self._db.commit()
            raise

        self._db.add(
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content=answer,
            )
        )
        agent_run.status = "completed"
        agent_run.finished_at = datetime.utcnow()
        await self._db.commit()
        await self._remember_turn(
            conversation_id=conversation.id,
            user_message=user_message,
            assistant_answer=answer,
        )

        return {
            "conversation_id": conversation.id,
            "agent_run_id": agent_run.id,
            "answer": answer,
            "tool_calls": [
                {
                    "tool_name": item.name,
                    "arguments": item.arguments,
                    "result": item.result,
                }
                for item in state.tool_executions
            ],
        }

    async def _agent_loop(self, state: AgentState) -> str:
        tools_schema = self._tools.openai_tools_schema()

        for _ in range(self._settings.agent_max_steps):
            try:
                assistant_message = await self._llm.chat(
                    messages=state.messages,
                    tools=tools_schema,
                )
            except APIError as exc:
                raise HTTPException(
                    status_code=502,
                    detail=f"LLM provider error: {exc}",
                ) from exc

            tool_calls = assistant_message.tool_calls or []
            if not tool_calls:
                content = assistant_message.content or ""
                if not content.strip():
                    return "I could not produce a final answer."
                return content

            state.messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        tool_call.model_dump()
                        for tool_call in tool_calls
                    ],
                }
            )

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                arguments = self._parse_tool_arguments(
                    tool_call.function.arguments
                )
                result = await self._tools.execute(tool_name, arguments)

                state.tool_executions.append(
                    ToolExecution(
                        name=tool_name,
                        arguments=arguments,
                        result=result,
                    )
                )
                self._db.add(
                    ToolCall(
                        agent_run_id=state.agent_run_id,
                        tool_name=tool_name,
                        arguments=arguments,
                        result=result,
                    )
                )
                await self._db.flush()

                state.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        return (
            "I reached the maximum number of tool steps before producing a "
            "final answer."
        )

    async def _get_or_create_conversation(
        self,
        conversation_id: int | None,
    ) -> Conversation:
        if conversation_id is None:
            conversation = Conversation()
            self._db.add(conversation)
            await self._db.flush()
            return conversation

        conversation = await self._db.get(Conversation, conversation_id)
        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )
        return conversation

    async def _load_history(
        self,
        conversation_id: int,
        limit: int | None = None,
    ) -> list[dict[str, str]]:
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
        )
        if limit is not None:
            statement = statement.limit(limit)

        result = await self._db.execute(statement)
        rows = list(reversed(result.scalars().all()))
        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in rows
        ]

    async def _load_short_term_history(
        self,
        conversation_id: int,
    ) -> list[dict[str, str]]:
        if self._memory is not None:
            messages = await self._memory.get_messages(conversation_id)
            if messages:
                return messages

        return await self._load_history(
            conversation_id,
            limit=self._settings.short_term_memory_max_messages,
        )

    async def _remember_turn(
        self,
        conversation_id: int,
        user_message: str,
        assistant_answer: str,
    ) -> None:
        if self._memory is None:
            return

        await self._memory.append_messages(
            conversation_id,
            [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_answer},
            ],
        )

    def _parse_tool_arguments(self, raw_arguments: str | None) -> dict[str, Any]:
        if not raw_arguments:
            return {}
        try:
            value = json.loads(raw_arguments)
        except json.JSONDecodeError:
            return {"raw": raw_arguments}
        if isinstance(value, dict):
            return value
        return {"value": value}
