from tools.registry import Tool, ToolType, ToolRegistry

def tool(*, name: str, description: str, category: str, type: ToolType = ToolType.ATOMIC):
    def decorator(function):
        tool_info = Tool(
            name=name,
            description=description,
            category=category,
            type=type,
            implementation=function
        )
        ToolRegistry.register(tool_info)
        return function
    return decorator