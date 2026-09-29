from typing import Any

from app.tools.base import BaseTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def openai_tools_schema(self) -> list[dict[str, Any]]:
        return [tool.openai_schema() for tool in self._tools.values()]

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        tool = self._tools.get(tool_name)
        if tool is None:
            return {
                "ok": False,
                "error": f"Unknown tool: {tool_name}",
            }

        try:
            return await tool.execute(arguments)
        except Exception as exc:
            return {
                "ok": False,
                "error": str(exc),
            }
