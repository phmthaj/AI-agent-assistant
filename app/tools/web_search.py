import asyncio
import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from app.tools.base import BaseTool


class WebSearchTool(BaseTool):
    name = "web_search"
    description = (
        "Search the web for a short query using DuckDuckGo Instant Answer. "
        "Use this only for lightweight public facts."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query.",
            }
        },
        "required": ["query"],
        "additionalProperties": False,
    }

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = arguments.get("query")
        if not isinstance(query, str) or not query.strip():
            return {
                "ok": False,
                "error": "Argument 'query' must be a non-empty string.",
            }

        payload = await asyncio.to_thread(self._search, query)

        related = payload.get("RelatedTopics") or []
        snippets = []
        for item in related:
            if "Text" in item:
                snippets.append(item["Text"])
            for topic in item.get("Topics", []):
                if "Text" in topic:
                    snippets.append(topic["Text"])
            if len(snippets) >= 3:
                break

        return {
            "ok": True,
            "query": query,
            "abstract": payload.get("AbstractText") or "",
            "answer": payload.get("Answer") or "",
            "related": snippets[:3],
            "source": payload.get("AbstractURL") or "",
        }

    def _search(self, query: str) -> dict[str, Any]:
        params = urlencode(
            {
                "q": query,
                "format": "json",
                "no_redirect": "1",
                "no_html": "1",
            }
        )
        with urlopen(f"https://api.duckduckgo.com/?{params}", timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
