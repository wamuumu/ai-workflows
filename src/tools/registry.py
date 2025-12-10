import pkgutil
import importlib
import pathlib
import inspect

from typing import get_type_hints, get_args, get_origin, Any

class Tool:
    def __init__(self, name: str, description: str, category: str, implementation: callable):
        self.name = name
        self.description = description
        self.category = category
        self.function = implementation
        self._parameters = None
        self._return_type = None

    def run(self, **kwargs):
        return self.function(**kwargs)
    
    @property
    def parameters(self) -> dict:
        """Extract parameter information from the function signature."""
        if self._parameters is not None:
            return self._parameters
        
        sig = inspect.signature(self.function)
        type_hints = get_type_hints(self.function)
        
        params = {}
        for param_name, param in sig.parameters.items():
            param_info = {
                "name": param_name,
                "required": param.default == inspect.Parameter.empty,
                "default": None if param.default == inspect.Parameter.empty else param.default,
                "type": self.__format_type(type_hints.get(param_name, Any))
            }
            params[param_name] = param_info
        
        self._parameters = params
        return params

    @property
    def return_type(self) -> str:
        """Extract return type information."""
        if self._return_type is not None:
            return self._return_type
        
        type_hints = get_type_hints(self.function)
        return_hint = type_hints.get('return', dict)
        self._return_type = self.__format_type(return_hint)
        return self._return_type
    
    def __format_type(self, type_hint) -> str:
        """Format type hints into readable strings."""
        if type_hint == inspect.Parameter.empty or type_hint is Any:
            return "any"
        
        origin = get_origin(type_hint)
        if origin is None:
            return type_hint.__name__ if hasattr(type_hint, '__name__') else str(type_hint)
        
        args = get_args(type_hint)
        if origin is list:
            if args:
                return f"list[{self._format_type(args[0])}]"
            return "list"
        elif origin is dict:
            if args:
                return f"dict[{self._format_type(args[0])}, {self._format_type(args[1])}]"
            return "dict"
        elif origin is tuple:
            return "tuple"
        else:
            return str(type_hint)
    
    def to_dict(self) -> dict:
        """Convert tool information to dictionary format."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": self.parameters,
            "return_type": self.return_type
        }

    def to_prompt_format(self) -> str:
        """Format tool information for LLM prompt in a clean, readable way."""
        
        # Build parameter block
        if self.parameters:
            params_lines = []
            for name, info in self.parameters.items():
                req = "required" if info["required"] else f"optional (default: {info['default']})"
                params_lines.append(f"- {name} ({info['type']}): {req}")
            params_str = "\n\t".join(params_lines)
        else:
            params_str = "None"
        
        # Final formatted block
        return (
            f"[Tool]\n"
            f" |- Name: {self.name}\n"
            f" |- Category: {self.category}\n"
            f" |- Description: {self.description}\n"
            f" |- Parameters:\n\t{params_str}\n"
            f" |- Returns: {self.return_type}\n"
        )


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
    def get_all(cls) -> dict[str, Tool]:
        """Retrieve all registered tools."""
        cls.__ensure_initialized()
        return cls._tools.copy()
    
    @classmethod
    def get_by_category(cls, category: str) -> dict[str, Tool]:
        """Retrieve tools by category."""
        cls.__ensure_initialized()
        return {name: tool for name, tool in cls._tools.items() if tool.category == category}
    
    @classmethod
    def get_categories(cls) -> list[str]:
        """List all tool categories."""
        cls.__ensure_initialized()
        return list(set(tool.category for tool in cls._tools.values()))
    
    @classmethod
    def to_dict(cls) -> dict:
        """Convert all tools to dictionary format."""
        cls.__ensure_initialized()
        return {
            "tools": [tool.to_dict() for tool in cls._tools.values()],
            "categories": cls.get_categories(),
            "total_tools": len(cls._tools)
        }
    
    @classmethod
    def to_prompt_format(cls, group_by_category: bool = True) -> str:
        """Generate a formatted string representation of all tools for LLM prompts."""
        cls.__ensure_initialized()
        
        output = "\nAvailable Tools:\n\n"
        output += f"Total tools: {len(cls._tools)}\n"
        output += f"Categories: {', '.join(cls.get_categories())}\n\n"
        
        if group_by_category:
            categories = sorted(cls.get_categories())
            for category in categories:
                output += f"[Category: {category.upper()}]\n\n"
                tools = cls.get_by_category(category)
                for tool_name in sorted(tools.keys()):
                    output += tools[tool_name].to_prompt_format()
                    output += "\n"
        else:
            for tool_name in sorted(cls._tools.keys()):
                output += cls._tools[tool_name].to_prompt_format()
                output += "\n"
        
        return output


    