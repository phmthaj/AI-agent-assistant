from typing import Any

from openai import AsyncOpenAI

from app.config import Settings


class LLMClient:
    """Small wrapper around an OpenAI-compatible chat completions API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = AsyncOpenAI(
            base_url=settings.openai_api_base,
            api_key=settings.openai_api_key,
        )

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        kwargs: dict[str, Any] = {
            "model": self._settings.openai_model,
            "messages": messages,
            "max_tokens": self._settings.llm_max_tokens,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self._client.chat.completions.create(**kwargs)
        return response.choices[0].message
