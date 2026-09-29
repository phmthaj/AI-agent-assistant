import asyncio
import ipaddress
import json
import socket
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.tools.base import BaseTool


class HttpFetchTool(BaseTool):
    name = "http_fetch"
    description = (
        "Fetch a public HTTP/HTTPS URL and return a compact text or JSON preview. "
        "Private network and localhost URLs are blocked."
    )
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Public HTTP or HTTPS URL to fetch.",
            },
            "max_characters": {
                "type": "integer",
                "description": "Maximum response characters to return.",
                "minimum": 200,
                "maximum": 5000,
            },
        },
        "required": ["url"],
        "additionalProperties": False,
    }

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        url = arguments.get("url")
        if not isinstance(url, str) or not url.strip():
            return {"ok": False, "error": "Argument 'url' must be non-empty."}

        max_characters = arguments.get("max_characters", 2000)
        if not isinstance(max_characters, int):
            max_characters = 2000
        max_characters = max(200, min(max_characters, 5000))

        validation_error = self._validate_url(url)
        if validation_error:
            return {"ok": False, "error": validation_error}

        return await asyncio.to_thread(self._fetch, url, max_characters)

    def _validate_url(self, url: str) -> str | None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return "Only http and https URLs are supported."
        if not parsed.hostname:
            return "URL must include a hostname."

        try:
            addresses = socket.getaddrinfo(parsed.hostname, None)
        except socket.gaierror as exc:
            return f"Could not resolve hostname: {exc}"

        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
            ):
                return "Private, local, link-local, multicast, and reserved IPs are blocked."

        return None

    def _fetch(self, url: str, max_characters: int) -> dict[str, Any]:
        request = Request(
            url,
            headers={
                "User-Agent": "ai-agent-backend/0.1",
                "Accept": "application/json,text/plain,text/html;q=0.8,*/*;q=0.5",
            },
        )
        with urlopen(request, timeout=10) as response:
            content_type = response.headers.get("content-type", "")
            raw = response.read(max_characters * 4)
            text = raw.decode("utf-8", errors="replace")

        payload: dict[str, Any] = {
            "ok": True,
            "url": url,
            "status": response.status,
            "content_type": content_type,
            "truncated": len(text) > max_characters,
        }

        preview = text[:max_characters]
        if "application/json" in content_type:
            try:
                payload["json"] = json.loads(preview)
            except json.JSONDecodeError:
                payload["text"] = preview
        else:
            payload["text"] = preview

        return payload
