import importlib
import pathlib
import inspect

from typing import get_type_hints, get_args, get_origin, Any, Union, List, Dict, Tuple

class Tool:
    def __init__(self, name: str, description: str, category: str, implementation: callable):
        self.name = name
        self.description = description
        self.category = category
        self.function = implementation
        self._inputs = None
        self._outputs = None

    def run(self, **kwargs):
        return self.function(**kwargs)
    
    @property
    def inputs(self) -> dict:
        """Extract parameter information from the function signature."""
        if self._inputs is not None:
            return self._inputs
        
        # Get function signature and type hints
        sig = inspect.signature(self.function)
        type_hints = get_type_hints(self.function)
        
        # Extract parameter details
        params = []
        for param_name, param in sig.parameters.items():
            params.append({
                "name": param_name,
                "required": param.default == inspect.Parameter.empty,
                "default": None if param.default == inspect.Parameter.empty else param.default,
                "type": self.__format_type(type_hints.get(param_name, Any))
            })
        
        self._inputs = params
        return params

    @property
    def outputs(self) -> dict:
        """Extract output information from the function return type."""
        if self._outputs is not None:
            return self._outputs
        
        hints = get_type_hints(self.function)
        rt = hints.get("return", dict)

        # Not a TypedDict → no schema
        if not (isinstance(rt, type) and hasattr(rt, '__annotations__') and hasattr(rt, '__total__')):
            self._outputs = []
            return self._outputs
        
        # Extract fields from TypedDict.__annotations__
        results = []
        for key, type_hint in rt.__annotations__.items():
            results.append({
                "key": key,
                "type": self.__format_type(type_hint)
            })
        
        self._outputs = results
        return results
    
    def __format_type(self, type_hint) -> str:
        """Format type hints into readable strings."""
        if type_hint is inspect.Parameter.empty or type_hint is Any:
            return "any"
        
        origin = get_origin(type_hint)
        args = get_args(type_hint)

        # No origin → normal type
        if origin is None:
            return type_hint.__name__ if hasattr(type_hint, "__name__") else str(type_hint)

        # List
        if origin in (list, List):
            if args:
                return f"list[{self.__format_type(args[0])}]"
            return "list"

        # Dict
        elif origin in (dict, Dict):
            if args:
                return f"dict[{self.__format_type(args[0])}, {self.__format_type(args[1])}]"
            return "dict"

        # Tuple
        elif origin in (tuple, Tuple):
            if args:
                inner = ", ".join(self.__format_type(a) for a in args)
                return f"tuple[{inner}]"
            return "tuple"

        # Union / Optional
        elif origin is Union:
            # Optional[T] is Union[T, NoneType]
            if len(args) == 2 and type(None) in args:
                non_none = args[0] if args[1] is type(None) else args[1]
                return f"Optional[{self.__format_type(non_none)}]"
            else:
                inner = ", ".join(self.__format_type(a) for a in args)
                return f"Union[{inner}]"

        # fallback
        return str(type_hint)
    
    def to_dict(self) -> dict:
        """Convert tool information to dictionary format."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "inputs": self.inputs,
            "outputs": self.outputs
        }

    def to_prompt_format(self) -> str:
        """Format tool information for LLM prompt in a clean, readable way."""
        
        # Build parameter block
        if self.inputs:
            input_lines = []
            for input in self.inputs:
                req = "required" if input["required"] else f"optional (default: {input['default']})"
                input_lines.append(f"- {input['name']} ({input['type']}): {req}")
            inputs_str = "\n\t".join(input_lines)
        else:
            inputs_str = "None"
        
        # -------- Outputs from TypedDict -------
        if self.outputs:
            output_lines = []
            for output in self.outputs:
                output_lines.append(f"- {output['key']} ({output['type']})")
            output_str = "\n\t".join(output_lines)
        else:
            output_str = "(unstructured output)"
        
        # Final formatted block
        return (
            f"[Tool]\n"
            f" |- Name: {self.name}\n"
            f" |- Category: {self.category}\n"
            f" |- Description: {self.description}\n"
            f" |- Input schema:\n\t{inputs_str}\n"
            f" |- Output schema:\n\t{output_str}\n"
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


    