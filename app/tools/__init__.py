from app.tools.calculator import CalculatorTool
from app.tools.http_fetch import HttpFetchTool
from app.tools.registry import ToolRegistry
from app.tools.text_analyzer import TextAnalyzerTool
from app.tools.time_tool import CurrentTimeTool
from app.tools.unit_converter import UnitConverterTool
from app.tools.web_search import WebSearchTool


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(CurrentTimeTool())
    registry.register(WebSearchTool())
    registry.register(UnitConverterTool())
    registry.register(TextAnalyzerTool())
    registry.register(HttpFetchTool())
    return registry


__all__ = [
    "CalculatorTool",
    "CurrentTimeTool",
    "HttpFetchTool",
    "TextAnalyzerTool",
    "ToolRegistry",
    "UnitConverterTool",
    "WebSearchTool",
    "build_default_registry",
]
