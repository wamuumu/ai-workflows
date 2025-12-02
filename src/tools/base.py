from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseTool(ABC):
    """Abstract base class for all tools."""

    name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None

    def __init__(self, name: str, description: str, parameters: Optional[Dict[str, Any]] = None):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    def __repr__(self):
        formatted = f"{self.name}: {self.description}\n"
        if self.parameters:
            formatted += f" | Input: {self.parameters}\n"
        return formatted
    
    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """Run the tool with the given keyword arguments."""
        raise NotImplementedError("Each tool must implement its own run method.")