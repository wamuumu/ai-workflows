"""
Tool Registry Module
====================

This module implements the ToolRegistry, a central singleton registry
for managing all available tools in the workflow system.

Main Responsibilities:
    - Auto-discover and load tools from subpackages
    - Register and retrieve tools by name, type, or category
    - Generate formatted tool documentation for LLM prompts

Key Dependencies:
    - tools.tool: For Tool class and ToolType enum

Design Patterns:
    - Singleton pattern via class methods and class-level state
    - Lazy initialization for automatic tool discovery
    - Registry pattern for centralized tool management
"""

import importlib
import pathlib

from typing import List
from tools.tool import Tool, ToolType


class ToolRegistry:
    """
    Central registry for managing workflow tools.
    
    Provides a singleton-style interface for tool registration, discovery,
    and retrieval. Automatically loads tools from subpackages on first access.
    
    Class Attributes:
        _tools: Dictionary mapping tool names to Tool instances.
        _initialized: Flag indicating whether auto-discovery has run.
    
    Usage:
        >>> from tools.registry import ToolRegistry
        >>> tool = ToolRegistry.get("get_weather")
        >>> all_tools = ToolRegistry.get_all_tools()
        >>> weather_tools = ToolRegistry.get_by_category("weather")
    """

    _tools: dict[str, Tool] = {}
    _initialized = False
    
    @classmethod
    def __ensure_initialized(cls):
        """
        Ensure tool auto-discovery has been performed.
        
        Lazily loads all tools from subpackages on first access to
        any registry method requiring tool data.
        """
        if not cls._initialized:
            cls.__load_tools()
            cls._initialized = True
    
    @classmethod
    def __load_tools(cls):
        """
        Auto-discover and load tools from subpackages.
        
        Scans the tools package directory for subpackages with
        __init__.py files and imports them to trigger @tool decorator
        registrations.
        """
        package_dir = pathlib.Path(__file__).parent
        for tools_dir in package_dir.iterdir():
            if tools_dir.is_dir() and (tools_dir / "__init__.py").exists():
                importlib.import_module(f"tools.{tools_dir.name}")

    @classmethod
    def register(cls, tool: Tool):
        """
        Register a tool in the registry.
        
        Called by the @tool decorator to add tools to the registry.
        
        Args:
            tool: Tool instance to register.
            
        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        if tool.name in cls._tools:
            raise ValueError(f"Tool {tool.name} is already registered.")
        cls._tools[tool.name] = tool
    
    @classmethod
    def get(cls, name: str) -> Tool:
        """
        Retrieve a tool by its unique name.
        
        Args:
            name: The tool's registered name.
            
        Returns:
            The Tool instance with the specified name.
            
        Raises:
            ValueError: If no tool with the given name is registered.
        """
        cls.__ensure_initialized()
        tool = cls._tools.get(name)
        if not tool:
            raise ValueError(f"Tool {name} is not registered.")
        return tool
    
    @classmethod
    def get_all_tools(cls) -> List[Tool]:
        """
        Retrieve all registered tools.
        
        Returns:
            List of all Tool instances in the registry.
        """
        cls.__ensure_initialized()
        return list(cls._tools.values())

    @classmethod
    def get_by_type(cls, type: ToolType) -> List[Tool]:
        """
        Retrieve tools filtered by type.
        
        Args:
            type: ToolType to filter by (ATOMIC or MACRO).
            
        Returns:
            List of Tool instances matching the specified type.
        """
        cls.__ensure_initialized()
        return [tool for tool in cls._tools.values() if tool.type == type]
    
    @classmethod
    def get_by_category(cls, category: str) -> List[Tool]:
        """
        Retrieve tools filtered by category.
        
        Args:
            category: Category string to filter by (e.g., "weather").
            
        Returns:
            List of Tool instances in the specified category.
        """
        cls.__ensure_initialized()
        return [tool for tool in cls._tools.values() if tool.category == category]

    @classmethod
    def get_all_tool_names(cls) -> List[str]:
        """
        Retrieve names of all registered tools.
        
        Returns:
            List of tool name strings.
        """
        cls.__ensure_initialized()
        return list(cls._tools.keys())

    @classmethod
    def get_all_input_keys(cls) -> List[str]:
        """
        Retrieve all unique input parameter names across all tools.
        
        Useful for validation and schema analysis.
        
        Returns:
            List of unique input parameter names.
        """
        cls.__ensure_initialized()
        input_keys = set()
        for tool in cls._tools.values():
            for input in tool.inputs:
                input_keys.add(input["name"])
        return list(input_keys)

    @classmethod
    def get_all_output_keys(cls) -> List[str]:
        """
        Retrieve all unique output field names across all tools.
        
        Useful for validation and schema analysis.
        
        Returns:
            List of unique output field names.
        """
        cls.__ensure_initialized()
        output_keys = set()
        for tool in cls._tools.values():
            for output in tool.outputs:
                output_keys.add(output["key"])
        return list(output_keys)

    @classmethod
    def exists(cls, name: str) -> bool:
        """
        Check if a tool is registered.
        
        Args:
            name: Tool name to check.
            
        Returns:
            True if tool exists, False otherwise.
        """
        cls.__ensure_initialized()
        return name in cls._tools
    
    @classmethod
    def to_prompt_format(cls, tools: List[Tool] = None, group_by_category: bool = True) -> str:
        """
        Generate formatted tool documentation for LLM prompts.
        
        Creates a structured text representation of tools suitable for
        inclusion in LLM system prompts or context.
        
        Args:
            tools: List of tools to format (default: all registered tools).
            group_by_category: Whether to group tools by category.
            
        Returns:
            Formatted multi-line string describing available tools.
        """
        cls.__ensure_initialized()
        
        if tools is None:
            tools = list(cls._tools.values())
        
        categories = sorted(set([tool.category for tool in tools]))
        
        # Build header with summary information
        output = "\nAvailable Tools:\n\n"
        output += f"Total tools: {len(tools)}\n"
        output += f"Categories: {', '.join(categories)}\n\n"
        
        if group_by_category:
            # Group tools by category for better organization
            for category in categories:
                output += f"[Category: {category.upper()}]\n\n"
                for tool in tools:
                    if tool.category == category:
                        output += tool.to_prompt_format()
                        output += "\n"
        else:
            # List tools alphabetically
            for tool in sorted(tools, key=lambda t: t.name):
                output += tool.to_prompt_format()
                output += "\n"
        
        return output