import pkgutil
import importlib
import pathlib

class Tool:
    def __init__(self, name: str, description: str, category: str, implementation: callable):
        self.name = name
        self.description = description
        self.category = category
        self.function = implementation

    def run(self, **kwargs):
        return self.function(**kwargs)

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
                for module in pkgutil.iter_modules([str(tools_dir)], prefix=f"tools.{tools_dir.name}."):
                    importlib.import_module(module.name)

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
    def list_tools(cls) -> list[str]:
        """List all registered tools."""
        cls.__ensure_initialized()
        return list(cls._tools.keys())


    