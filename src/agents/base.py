from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any

class AgentBase(ABC):
    
    @abstractmethod
    def generate_content(self, system_prompt: str, user_prompt: str) -> str:
        """Generate content using the LLM."""
        pass

    @abstractmethod
    def generate_structured_content(self, system_prompt: str, user_prompt: str, response_model: BaseModel) -> BaseModel:
        """Generate structured content using the LLM and parse it into the given response model."""
        pass

    @abstractmethod
    def init_chat(self, system_prompt: str) -> Any:
        """Initialize and return a chat session object."""
        pass

    @abstractmethod
    def init_structured_chat(self, system_prompt: str, response_model: BaseModel) -> Any:
        """Initialize and return a chat session object."""
        pass