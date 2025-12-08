from tools.registry import Tool, ToolRegistry
from typing import Optional

def tool(*, name: str, description: str, category: Optional[str] = None):
    def decorator(function):
        tool_info = Tool(
            name=name,
            description=description,
            category=category,
            implementation=function
        )
        ToolRegistry.register(tool_info)
        return function
    return decorator