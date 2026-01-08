from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Protocol

class Chat(Protocol):
    def send_message(self, message: str, category: str, max_retries: int) -> str: pass
    def get_history(self) -> list[dict]: pass

class StructuredChat(Protocol):
    def send_message(self, message: str, category: str, max_retries: int) -> BaseModel: pass
    def get_history(self) -> list[dict]: pass

class AgentBase(ABC):
    
    @abstractmethod
    def generate_content(self, system_prompt: str, user_prompt: str, category: str, max_retries: int) -> str:
        """Generate content using the LLM."""
        pass

    @abstractmethod
    def generate_structured_content(self, system_prompt: str, user_prompt: str, response_model: BaseModel, category: str, max_retries: int) -> BaseModel:
        """Generate structured content using the LLM and parse it into the given response model."""
        pass

    @abstractmethod
    def init_chat(self, system_prompt: str) -> Chat:
        """Initialize and return a chat session object."""
        pass

    @abstractmethod
    def init_structured_chat(self, system_prompt: str, response_model: BaseModel) -> StructuredChat:
        """Initialize and return a chat session object."""
        pass