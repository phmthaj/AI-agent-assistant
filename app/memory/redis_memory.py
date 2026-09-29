import json
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import Settings


class RedisShortTermMemory:
    """Short-lived conversation context backed by Redis.

    PostgreSQL remains the source of truth. Redis is used as a fast, volatile
    working memory for the recent turns that should be sent back to the LLM.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )

    async def get_messages(
        self,
        conversation_id: int,
    ) -> list[dict[str, str]]:
        try:
            raw_messages = await self._client.lrange(
                self._key(conversation_id),
                0,
                -1,
            )
        except RedisError:
            return []

        messages: list[dict[str, str]] = []
        for item in raw_messages:
            try:
                message = json.loads(item)
            except json.JSONDecodeError:
                continue

            role = message.get("role")
            content = message.get("content")
            if role in {"user", "assistant"} and isinstance(content, str):
                messages.append({"role": role, "content": content})

        return messages

    async def append_messages(
        self,
        conversation_id: int,
        messages: list[dict[str, Any]],
    ) -> None:
        if not messages:
            return

        key = self._key(conversation_id)
        encoded = [
            json.dumps(
                {
                    "role": message["role"],
                    "content": message["content"],
                },
                ensure_ascii=False,
            )
            for message in messages
            if message.get("role") in {"user", "assistant"}
            and isinstance(message.get("content"), str)
        ]
        if not encoded:
            return

        try:
            await self._client.rpush(key, *encoded)
            await self._client.ltrim(
                key,
                -self._settings.short_term_memory_max_messages,
                -1,
            )
            await self._client.expire(
                key,
                self._settings.short_term_memory_ttl_seconds,
            )
        except RedisError:
            return

    async def clear(self, conversation_id: int) -> None:
        try:
            await self._client.delete(self._key(conversation_id))
        except RedisError:
            return

    def _key(self, conversation_id: int) -> str:
        return f"agent:conversation:{conversation_id}:short_term_memory"
