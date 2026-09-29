from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    name: str
    description: str
    parameters: dict[str, Any]

    def openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    @abstractmethod
    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
