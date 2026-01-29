"""
Tool Decorator Module
=====================

This module provides the @tool decorator for easy tool registration,
allowing functions to be declared as tools with metadata.

Main Responsibilities:
    - Provide declarative tool registration syntax
    - Wrap functions with tool metadata
    - Auto-register tools with the ToolRegistry

Key Dependencies:
    - tools.registry: For Tool class and ToolRegistry
    - tools.tool: For ToolType enum

Usage Example:
    >>> from tools.decorator import tool
    >>> from tools.tool import ToolType
    >>>
    >>> @tool(name="get_weather", description="Get weather data",
    ...       category="weather", type=ToolType.ATOMIC)
    ... def get_weather(city: str) -> WeatherResult:
    ...     return {"temperature": 20, "conditions": "sunny"}
"""

from tools.registry import Tool, ToolType, ToolRegistry


def tool(*, name: str, description: str, category: str, type: ToolType = ToolType.ATOMIC):
    """
    Decorator for registering functions as workflow tools.
    
    Wraps a function with tool metadata and automatically registers
    it with the ToolRegistry. The decorated function remains callable
    normally while also being available as a registered tool.
    
    Args:
        name: Unique identifier for the tool.
        description: Human-readable description of functionality.
        category: Classification category for grouping.
        type: ToolType (default: ATOMIC).
        
    Returns:
        Decorator function that registers the tool and returns
        the original function unchanged.
        
    Example:
        >>> @tool(name="add_numbers", description="Add two numbers",
        ...       category="math")
        ... def add(a: int, b: int) -> int:
        ...     return a + b
    """
    def decorator(function):
        """Inner decorator that creates and registers the Tool."""
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