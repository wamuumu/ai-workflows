"""
Agent Base Module
=================

This module defines the abstract base class and protocol interfaces for LLM agents
in the AI-Workflows framework. It establishes a unified interface that all concrete
agent implementations (e.g., Gemini, Cerebras) must adhere to.

Main Responsibilities:
    - Define the AgentBase abstract class with required methods for content generation
    - Specify Chat and StructuredChat protocols for conversational interactions
    - Ensure consistent API across different LLM provider implementations

Key Dependencies:
    - abc: For abstract base class functionality
    - pydantic: For structured data validation via BaseModel
    - typing: For Protocol definitions enabling structural subtyping
"""

from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Protocol


class Chat(Protocol):
    """
    Protocol defining the interface for unstructured chat sessions.
    
    This protocol specifies the methods that any chat session implementation
    must provide to support multi-turn conversations with plain text responses.
    
    Methods:
        send_message: Send a message and receive a text response.
        get_history: Retrieve the conversation history.
    """
    
    def send_message(self, message: str, category: str, max_retries: int) -> str:
        """
        Send a message in the chat session and return the response.
        
        Args:
            message: The user message to send.
            category: Metric category for tracking (e.g., 'chat', 'execution').
            max_retries: Maximum number of retry attempts on failure.
            
        Returns:
            The assistant's response as plain text.
        """
        pass
    
    def get_history(self) -> list[dict]:
        """
        Retrieve the full conversation history.
        
        Returns:
            List of message dictionaries containing role and content.
        """
        pass


class StructuredChat(Protocol):
    """
    Protocol defining the interface for structured chat sessions.
    
    Similar to Chat, but responses are parsed and validated against
    a Pydantic model schema, enabling type-safe structured outputs.
    
    Methods:
        send_message: Send a message and receive a validated BaseModel response.
        get_history: Retrieve the conversation history.
    """
    
    def send_message(self, message: str, category: str, max_retries: int) -> BaseModel:
        """
        Send a message and receive a structured, validated response.
        
        Args:
            message: The user message to send.
            category: Metric category for tracking purposes.
            max_retries: Maximum number of retry attempts on failure.
            
        Returns:
            Response parsed and validated as the configured Pydantic model.
        """
        pass
    
    def get_history(self) -> list[dict]:
        """
        Retrieve the full conversation history.
        
        Returns:
            List of message dictionaries containing role and content.
        """
        pass


class AgentBase(ABC):
    """
    Abstract base class for all LLM agent implementations.
    
    This class defines the contract that all concrete agent implementations
    must fulfill. It provides two modes of operation:
    
    1. Single-shot generation: Generate content from a single prompt
    2. Chat sessions: Multi-turn conversations with state preservation
    
    Each mode supports both unstructured (plain text) and structured
    (Pydantic model) responses.
    
    Subclasses must implement all abstract methods to integrate with
    specific LLM providers (e.g., Google Gemini, Cerebras).
    """
    
    @abstractmethod
    def generate_content(self, system_prompt: str, user_prompt: str, category: str, max_retries: int) -> str:
        """
        Generate unstructured text content using the LLM.
        
        Args:
            system_prompt: System-level instructions defining agent behavior.
            user_prompt: The user's input prompt or query.
            category: Metric category for usage tracking.
            max_retries: Maximum retry attempts for transient failures.
            
        Returns:
            Generated text response from the LLM.
            
        Raises:
            Exception: If generation fails after all retry attempts.
        """
        pass

    @abstractmethod
    def generate_structured_content(self, system_prompt: str, user_prompt: str, response_model: BaseModel, category: str, max_retries: int) -> BaseModel:
        """
        Generate structured content validated against a Pydantic model.
        
        This method ensures the LLM output conforms to the specified schema,
        enabling type-safe downstream processing.
        
        Args:
            system_prompt: System-level instructions defining agent behavior.
            user_prompt: The user's input prompt or query.
            response_model: Pydantic model class defining the expected response schema.
            category: Metric category for usage tracking.
            max_retries: Maximum retry attempts for transient failures.
            
        Returns:
            Validated instance of the response_model populated with LLM output.
            
        Raises:
            ValueError: If response cannot be parsed into the specified model.
            Exception: If generation fails after all retry attempts.
        """
        pass

    @abstractmethod
    def init_chat(self, system_prompt: str) -> Chat:
        """
        Initialize an unstructured chat session.
        
        Creates a stateful chat session that maintains conversation history
        across multiple message exchanges.
        
        Args:
            system_prompt: System-level instructions for the chat session.
            
        Returns:
            A Chat-compliant object for multi-turn conversation.
        """
        pass

    @abstractmethod
    def init_structured_chat(self, system_prompt: str, response_model: BaseModel) -> StructuredChat:
        """
        Initialize a structured chat session with schema-validated responses.
        
        Creates a stateful chat session where all assistant responses are
        automatically parsed and validated against the specified model.
        
        Args:
            system_prompt: System-level instructions for the chat session.
            response_model: Pydantic model class for response validation.
            
        Returns:
            A StructuredChat-compliant object for type-safe multi-turn conversation.
        """
        pass