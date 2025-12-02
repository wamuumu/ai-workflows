from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseData(ABC):
    """Abstract mocked data source class."""

    name: str
    description: str

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @property
    @abstractmethod
    def data(self) -> Dict[str, Any]:
        """Return the mocked data."""
        raise NotImplementedError("Each data source must implement its own data property.")