from datetime import datetime, timezone
from typing import Any

from app.tools.base import BaseTool


class CurrentTimeTool(BaseTool):
    name = "current_time"
    description = "Return the current UTC time."
    parameters = {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            "timezone": "UTC",
            "iso": datetime.now(timezone.utc).isoformat(),
        }
