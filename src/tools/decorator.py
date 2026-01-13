from tools.registry import Tool, ToolRegistry

def tool(*, name: str, description: str, category: str, type: str = "atomic"):
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