"""
Tool Definition Module
======================

This module defines the core Tool class and ToolType enumeration used
throughout the workflow system for representing executable tools.

Main Responsibilities:
    - Define Tool data structure with metadata and implementation
    - Extract input/output schemas from Python type hints
    - Format tool information for LLM prompts

Key Dependencies:
    - inspect: For function signature analysis
    - typing: For type hint processing

Design Patterns:
    - Property pattern for lazy evaluation of inputs/outputs
    - Type hint introspection for schema extraction
"""

import inspect

from enum import Enum
from typing import get_type_hints, get_args, get_origin, Any, Union, List, Dict, Tuple


class ToolType(Enum):
    """
    Enumeration of tool types in the workflow system.
    
    Attributes:
        ATOMIC: Single-purpose tool performing one operation.
        MACRO: Composite tool combining multiple atomic operations.
    """
    ATOMIC = "atomic"
    MACRO = "macro"


class Tool:
    """
    Represents an executable tool in the workflow system.
    
    Encapsulates tool metadata (name, description, category) along with
    its implementation function. Provides automatic schema extraction
    from Python type hints for inputs and outputs.
    
    Attributes:
        name: Unique identifier for the tool.
        description: Human-readable description of tool functionality.
        category: Classification category (e.g., "weather", "finance").
        type: ToolType indicating atomic or macro tool.
        function: The actual implementation callable.
    
    Example:
        >>> def get_weather(city: str) -> WeatherResult:
        ...     return {"temperature": 20, "conditions": "sunny"}
        >>> tool = Tool("get_weather", "Get weather data", "weather",
        ...             ToolType.ATOMIC, get_weather)
        >>> result = tool.run(city="London")
    """
    
    def __init__(self, name: str, description: str, category: str, type: ToolType, implementation: callable):
        """
        Initialize a Tool instance.
        
        Args:
            name: Unique identifier for the tool.
            description: Human-readable description.
            category: Classification category for grouping.
            type: ToolType (ATOMIC or MACRO).
            implementation: The callable function implementing the tool.
        """
        self.name = name
        self.description = description
        self.category = category
        self.type = type
        self.function = implementation
        self._inputs = None  # Lazy-loaded input schema
        self._outputs = None  # Lazy-loaded output schema

    def run(self, **kwargs):
        """
        Execute the tool with provided arguments.
        
        Args:
            **kwargs: Keyword arguments passed to the tool function.
            
        Returns:
            The result of the tool function execution.
        """
        return self.function(**kwargs)
    
    @property
    def inputs(self) -> list[dict]:
        """
        Extract parameter information from the function signature.
        
        Analyzes the tool function's signature and type hints to build
        a schema describing required and optional parameters.
        
        Returns:
            List of parameter dictionaries with keys:
            - name: Parameter name
            - required: Whether parameter is required
            - default: Default value if optional
            - type: Formatted type string
        """
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
    def outputs(self) -> list[dict]:
        """
        Extract output information from the function return type.
        
        Analyzes the tool function's return type hint, expecting a
        TypedDict for structured output schema extraction.
        
        Returns:
            List of output field dictionaries with keys:
            - key: Field name
            - type: Formatted type string
            Returns empty list if return type is not a TypedDict.
        """
        if self._outputs is not None:
            return self._outputs
        
        hints = get_type_hints(self.function)
        rt = hints.get("return", dict)

        # Not a TypedDict → no schema available
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
        """
        Format type hints into human-readable strings.
        
        Recursively processes complex type hints (List, Dict, Union, etc.)
        into readable string representations for documentation.
        
        Args:
            type_hint: A Python type hint to format.
            
        Returns:
            Formatted string representation of the type.
        """
        if type_hint is inspect.Parameter.empty or type_hint is Any:
            return "any"
        
        origin = get_origin(type_hint)
        args = get_args(type_hint)

        # No origin → simple type
        if origin is None:
            return type_hint.__name__ if hasattr(type_hint, "__name__") else str(type_hint)

        # List[T] handling
        if origin in (list, List):
            if args:
                return f"list[{self.__format_type(args[0])}]"
            return "list"

        # Dict[K, V] handling
        elif origin in (dict, Dict):
            if args:
                return f"dict[{self.__format_type(args[0])}, {self.__format_type(args[1])}]"
            return "dict"

        # Tuple[T, ...] handling
        elif origin in (tuple, Tuple):
            if args:
                inner = ", ".join(self.__format_type(a) for a in args)
                return f"tuple[{inner}]"
            return "tuple"

        # Union / Optional handling
        elif origin is Union:
            # Optional[T] is Union[T, NoneType]
            if len(args) == 2 and type(None) in args:
                non_none = args[0] if args[1] is type(None) else args[1]
                return f"Optional[{self.__format_type(non_none)}]"
            else:
                inner = ", ".join(self.__format_type(a) for a in args)
                return f"Union[{inner}]"

        # Fallback for unrecognized types
        return str(type_hint)

    def to_prompt_format(self) -> str:
        """
        Format tool information for inclusion in LLM prompts.
        
        Generates a structured, human-readable representation of the
        tool's metadata, inputs, and outputs suitable for LLM context.
        
        Returns:
            Formatted multi-line string describing the tool.
        """
        # Build parameter block
        if self.inputs:
            input_lines = []
            for input in self.inputs:
                req = "required" if input["required"] else f"optional (default: {input['default']})"
                input_lines.append(f"- {input['name']} ({input['type']}): {req}")
            inputs_str = "\n\t".join(input_lines)
        else:
            inputs_str = "None"
        
        # Build output block from TypedDict schema
        if self.outputs:
            output_lines = []
            for output in self.outputs:
                output_lines.append(f"- {output['key']} ({output['type']})")
            output_str = "\n\t".join(output_lines)
        else:
            output_str = "(unstructured output)"
        
        # Assemble final formatted block
        return (
            f"[Tool]\n"
            f" |- Name: {self.name}\n"
            f" |- Category: {self.category}\n"
            f" |- Description: {self.description}\n"
            f" |- Tool type: {self.type.value}\n"
            f" |- Input schema:\n\t{inputs_str}\n"
            f" |- Output schema:\n\t{output_str}\n"
        )