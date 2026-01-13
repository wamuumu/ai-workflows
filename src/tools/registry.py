import importlib
import pathlib

from typing import List
from tools.tool import Tool, ToolType


class ToolRegistry:
    """Registry to manage available tools."""

    _tools: dict[str, Tool] = {}
    _initialized = False
    
    @classmethod
    def __ensure_initialized(cls):
        if not cls._initialized:
            cls.__load_tools()
            cls._initialized = True
    
    @classmethod
    def __load_tools(cls):
        package_dir = pathlib.Path(__file__).parent
        for tools_dir in package_dir.iterdir():
            if tools_dir.is_dir() and (tools_dir / "__init__.py").exists():
                importlib.import_module(f"tools.{tools_dir.name}")

    @classmethod
    def register(cls, tool: Tool):
        """Register a tool class."""
        if tool.name in cls._tools:
            raise ValueError(f"Tool {tool.name} is already registered.")
        cls._tools[tool.name] = tool
    
    @classmethod
    def get(cls, name: str) -> Tool:
        """Retrieve a tool by name."""
        cls.__ensure_initialized()
        tool = cls._tools.get(name)
        if not tool:
            raise ValueError(f"Tool {name} is not registered.")
        return tool
    
    @classmethod
    def get_all_tools(cls) -> List[Tool]:
        """Retrieve all registered tools."""
        cls.__ensure_initialized()
        return list(cls._tools.values())

    @classmethod
    def get_by_type(cls, type: ToolType) -> List[Tool]:
        """Retrieve tools by type."""
        cls.__ensure_initialized()
        return [tool for tool in cls._tools.values() if tool.type == type]
    
    @classmethod
    def get_by_category(cls, category: str) -> List[Tool]:
        """Retrieve tools by category."""
        cls.__ensure_initialized()
        return [tool for tool in cls._tools.values() if tool.category == category]

    @classmethod
    def get_all_tool_names(cls) -> List[str]:
        """Retrieve all registered tool names."""
        cls.__ensure_initialized()
        return list(cls._tools.keys())

    @classmethod
    def get_all_input_keys(cls) -> List[str]:
        """Retrieve all input keys from all registered tools."""
        cls.__ensure_initialized()
        input_keys = set()
        for tool in cls._tools.values():
            for input in tool.inputs:
                input_keys.add(input["name"])
        return list(input_keys)

    @classmethod
    def get_all_output_keys(cls) -> List[str]:
        """Retrieve all output keys from all registered tools."""
        cls.__ensure_initialized()
        output_keys = set()
        for tool in cls._tools.values():
            for output in tool.outputs:
                output_keys.add(output["key"])
        return list(output_keys)
    
    @classmethod
    def to_prompt_format(cls, tools: List[Tool] = None, group_by_category: bool = True) -> str:
        """Generate a formatted string representation of the provided tools for LLM prompts."""
        cls.__ensure_initialized()
        
        if tools is None:
            tools = list(cls._tools.values())
        
        categories = sorted(set([tool.category for tool in tools]))
        
        output = "\nAvailable Tools:\n\n"
        output += f"Total tools: {len(tools)}\n"
        output += f"Categories: {', '.join(categories)}\n\n"
        
        if group_by_category:
            for category in categories:
                output += f"[Category: {category.upper()}]\n\n"
                for tool in tools:
                    if tool.category == category:
                        output += tool.to_prompt_format()
                        output += "\n"
        else:
            for tool in sorted(tools, key=lambda t: t.name):
                output += tool.to_prompt_format()
                output += "\n"
        
        return output


    