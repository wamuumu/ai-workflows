"""
Google Gemini Agent Module
==========================

This module provides the GeminiAgent implementation for interfacing with
Google's Gemini family of large language models through the Google GenAI SDK.

Main Responsibilities:
    - Implement the AgentBase interface for Google Gemini models
    - Handle API authentication and client initialization
    - Provide both single-shot and chat-based content generation
    - Support structured JSON responses with schema validation
    - Track usage metrics (time, tokens) for each API call

Key Dependencies:
    - google.genai: Official Google GenAI Python SDK
    - pydantic: For structured response validation
    - python-dotenv: For secure API key management

Supported Models:
    - Gemini 2.5 Flash: High-performance model for complex tasks
    - Gemini 2.5 Flash Lite: Lightweight variant for faster inference
"""

import os
import getpass
import time

from enum import Enum
from pydantic import BaseModel
from google.genai import Client
from dotenv import load_dotenv
from google.genai.types import GenerateContentConfig
from agents.base import AgentBase
from utils.metric import MetricUtils

# Load API key from environment or prompt user interactively
load_dotenv()

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")


class GeminiModel(str, Enum):
    """
    Enumeration of supported Google Gemini model identifiers.
    
    These values correspond to the official model names used in the
    Google GenAI API. Using an enum ensures type safety and prevents
    typos in model selection.
    
    Attributes:
        GEMINI_2_5_FLASH: Full-featured Gemini 2.5 Flash model.
        GEMINI_2_5_FLASH_LITE: Optimized lightweight variant.
    """
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"


class GeminiAgent(AgentBase):
    """
    Concrete implementation of AgentBase for Google Gemini models.
    
    This class wraps the Google GenAI SDK to provide a consistent interface
    for content generation. It supports both unstructured text and structured
    JSON responses with automatic Pydantic model validation.
    
    Features:
        - Exponential backoff retry logic for transient API failures
        - Automatic token usage tracking via MetricUtils
        - Support for system instructions and JSON schema responses
        - Stateful chat sessions with conversation history
    
    Attributes:
        client: The Google GenAI Client instance.
        model_name: The selected Gemini model identifier.
    """

    def __init__(self, model_name: str = GeminiModel.GEMINI_2_5_FLASH):
        """
        Initialize the Gemini agent with a specific model.
        
        Args:
            model_name: The Gemini model to use. Defaults to GEMINI_2_5_FLASH.
        """
        self.client = Client()
        self.model_name = model_name

    def generate_content(self, system_prompt: str, user_prompt: str, category: str = "generation", max_retries: int = 5) -> str:
        """
        Generate unstructured text content using Gemini.
        
        Implements exponential backoff retry logic to handle transient
        API failures gracefully.
        
        Args:
            system_prompt: System-level instructions for the model.
            user_prompt: The user's input to process.
            category: Metric category for tracking. Defaults to "generation".
            max_retries: Maximum retry attempts. Defaults to 5.
            
        Returns:
            The generated text response.
            
        Raises:
            Exception: If all retry attempts are exhausted.
        """
        for attempt in range(1, max_retries + 1):
            try:
                start = time.time()
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=GenerateContentConfig(
                        system_instruction=system_prompt
                    )
                )
                end = time.time()
                break
            except Exception as e:
                print(f"Attempt {attempt} failed: {e}")
                if attempt == max_retries:
                    raise e
                # Exponential backoff: 2^attempt seconds
                sleep_time = 2 ** attempt
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)

        MetricUtils.update(category, start, end, response.usage_metadata.total_token_count)

        return response.text
            
    def generate_structured_content(self, system_prompt: str, user_prompt: str, response_model: BaseModel, category: str = "generation", max_retries: int = 5) -> BaseModel:
        """
        Generate structured content validated against a Pydantic schema.
        
        This method configures the model to return JSON that conforms to
        the provided response_model schema. The response is automatically
        parsed and validated.
        
        Args:
            system_prompt: System-level instructions for the model.
            user_prompt: The user's input to process.
            response_model: Pydantic model class defining the expected schema.
            category: Metric category for tracking. Defaults to "generation".
            max_retries: Maximum retry attempts. Defaults to 5.
            
        Returns:
            Validated instance of response_model.
            
        Raises:
            ValueError: If the response cannot be parsed into the model.
            Exception: If all retry attempts are exhausted.
        """
        for attempt in range(1, max_retries + 1):
            try:
                start = time.time()
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type='application/json',
                        response_schema=response_model
                    )
                )
                end = time.time()
                break
            except Exception as e:
                print(f"Attempt {attempt} failed: {e}")
                if attempt == max_retries:
                    raise e
                # Exponential backoff: 2^attempt seconds
                sleep_time = 2 ** attempt
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
        
        MetricUtils.update(category, start, end, response.usage_metadata.total_token_count)

        try:
            return response_model.model_validate_json(response.text)
        except Exception as e:
            raise ValueError(f"Failed to parse response into {response_model.__name__}: {e}")
        
    def init_chat(self, system_prompt: str):
        """
        Initialize an unstructured chat session with conversation history.
        
        Creates a Chat inner class instance that maintains state across
        multiple message exchanges.
        
        Args:
            system_prompt: System-level instructions for the chat session.
            
        Returns:
            A Chat instance supporting multi-turn conversation.
        """

        class Chat:
            """
            Inner class managing stateful unstructured chat sessions.
            
            This class wraps the Google GenAI chat API to provide
            conversation history tracking and retry logic.
            
            Attributes:
                chat_instance: The underlying GenAI chat object.
            """
            
            def __init__(self, client: Client, model_name: str, system_prompt: str):
                """
                Initialize the chat session with system instructions.
                
                Args:
                    client: The GenAI Client instance.
                    model_name: The model identifier to use.
                    system_prompt: System-level instructions.
                """
                self.chat_instance = client.chats.create(
                    model=model_name,
                    config=GenerateContentConfig(
                        system_instruction=system_prompt
                    )
                )

            def send_message(self, message: str, category: str = "chat", max_retries: int = 5) -> str:
                """
                Send a message in chat and return the response text.
                
                Args:
                    message: The user message to send.
                    category: Metric category. Defaults to "chat".
                    max_retries: Maximum retry attempts. Defaults to 5.
                    
                Returns:
                    The assistant's text response.
                    
                Raises:
                    Exception: If all retry attempts fail.
                """
                for attempt in range(1, max_retries + 1):
                    try:
                        start = time.time()
                        response = self.chat_instance.send_message(message)
                        end = time.time()
                        break
                    except Exception as e:
                        print(f"Attempt {attempt} failed: {e}")
                        if attempt == max_retries:
                            raise e
                        sleep_time = 2 ** attempt
                        print(f"Retrying in {sleep_time} seconds...")
                        time.sleep(sleep_time)
                
                MetricUtils.update(category, start, end, response.usage_metadata.total_token_count)
                
                return response.text

            def get_history(self):
                """
                Retrieve the full conversation history.
                
                Returns:
                    List of messages in the conversation.
                """
                return self.chat_instance.get_history()
            
        return Chat(self.client, self.model_name, system_prompt)  

    def init_structured_chat(self, system_prompt: str, response_model: BaseModel):
        """
        Initialize a structured chat session with schema-validated responses.
        
        Creates a StructuredChat inner class instance that automatically
        parses and validates all assistant responses against the provided
        Pydantic model.
        
        Args:
            system_prompt: System-level instructions for the chat session.
            response_model: Pydantic model class for response validation.
            
        Returns:
            A StructuredChat instance for type-safe multi-turn conversation.
        """

        class StructuredChat:
            """
            Inner class managing stateful structured chat sessions.
            
            All responses are automatically parsed and validated against
            the configured response_model schema.
            
            Attributes:
                chat_instance: The underlying GenAI chat object.
                response_model: The Pydantic model for validation.
            """
            
            def __init__(self, client: Client, model_name: str, system_prompt: str, response_model: BaseModel):
                """
                Initialize the structured chat session.
                
                Args:
                    client: The GenAI Client instance.
                    model_name: The model identifier to use.
                    system_prompt: System-level instructions.
                    response_model: Pydantic model for response schema.
                """
                self.chat_instance = client.chats.create(
                    model=model_name,
                    config=GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type='application/json',
                        response_schema=response_model
                    )
                )
                self.response_model = response_model

            def send_message(self, message: str, category: str = "chat", max_retries: int = 5) -> BaseModel:
                """
                Send a message and receive a validated structured response.
                
                Args:
                    message: The user message to send.
                    category: Metric category. Defaults to "chat".
                    max_retries: Maximum retry attempts. Defaults to 5.
                    
                Returns:
                    Validated instance of the configured response_model.
                    
                Raises:
                    ValueError: If response parsing fails.
                    Exception: If all retry attempts fail.
                """
                for attempt in range(1, max_retries + 1):
                    try:
                        start = time.time()
                        response = self.chat_instance.send_message(message)
                        end = time.time()
                        break
                    except Exception as e:
                        print(f"Attempt {attempt} failed: {e}")
                        if attempt == max_retries:
                            raise e
                        sleep_time = 2 ** attempt
                        print(f"Retrying in {sleep_time} seconds...")
                        time.sleep(sleep_time)
                
                MetricUtils.update(category, start, end, response.usage_metadata.total_token_count)
                
                try:
                    return self.response_model.model_validate_json(response.text)
                except Exception as e:
                    raise ValueError(f"Failed to parse response into {self.response_model.__name__}: {e}")

            def get_history(self):
                """
                Retrieve the full conversation history.
                
                Returns:
                    List of messages in the conversation.
                """
                return self.chat_instance.get_history()
        
        return StructuredChat(self.client, self.model_name, system_prompt, response_model)
