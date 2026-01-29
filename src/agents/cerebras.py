"""
Cerebras Agent Module
=====================

This module provides the CerebrasAgent implementation for interfacing with
Cerebras Cloud's large language models through the official Cerebras SDK.

Main Responsibilities:
    - Implement the AgentBase interface for Cerebras models
    - Handle API authentication and client initialization
    - Provide both single-shot and chat-based content generation
    - Support structured JSON responses with strict schema validation
    - Track usage metrics (time, tokens) for each API call

Key Dependencies:
    - cerebras.cloud.sdk: Official Cerebras Cloud Python SDK
    - pydantic: For structured response validation
    - python-dotenv: For secure API key management

Supported Models:
    - GPT-OSS (120B): Large open-source GPT model
    - Llama 3.3 (70B): Meta's Llama 3.3 70B parameter model

Design Notes:
    Unlike the Gemini implementation which uses native chat objects,
    Cerebras chat sessions are managed manually by maintaining a
    message history list, as the Cerebras SDK uses a stateless
    completion-style API.
"""

import os
import getpass
import time

from enum import Enum
from pydantic import BaseModel
from types import SimpleNamespace
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras
from agents.base import AgentBase
from utils.metric import MetricUtils

# Load API key from environment or prompt user interactively
load_dotenv()

if "CEREBRAS_API_KEY" not in os.environ:
    os.environ["CEREBRAS_API_KEY"] = getpass.getpass("Enter your Cerebras API key: ")


class CerebrasModel(str, Enum):
    """
    Enumeration of supported Cerebras model identifiers.
    
    These values correspond to the official model names used in the
    Cerebras Cloud API.
    
    Attributes:
        GPT_OSS: 120B parameter open-source GPT model.
        LLAMA_3_3: Meta's Llama 3.3 70B parameter model.
    """
    GPT_OSS = "gpt-oss-120b"
    LLAMA_3_3 = "llama-3.3-70b"


class CerebrasAgent(AgentBase):
    """
    Concrete implementation of AgentBase for Cerebras Cloud models.
    
    This class wraps the Cerebras Cloud SDK to provide a consistent interface
    for content generation. It supports both unstructured text and structured
    JSON responses with automatic Pydantic model validation using JSON schemas.
    
    Features:
        - Exponential backoff retry logic for transient API failures
        - Automatic token usage tracking via MetricUtils
        - JSON schema-based structured output enforcement
        - Manually managed chat sessions with conversation history
    
    Attributes:
        client: The Cerebras Cloud Client instance.
        model_name: The selected Cerebras model identifier.
    """

    def __init__(self, model_name: str = CerebrasModel.GPT_OSS):
        """
        Initialize the Cerebras agent with a specific model.
        
        Args:
            model_name: The Cerebras model to use. Defaults to GPT_OSS.
        """
        self.client = Cerebras()
        self.model_name = model_name

    def generate_content(self, system_prompt: str, user_prompt: str, category: str = "generation", max_retries: int = 5) -> str:
        """
        Generate unstructured text content using Cerebras.
        
        Uses the chat completions API with system and user messages.
        Implements exponential backoff retry logic for resilience.
        
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
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        for attempt in range(1, max_retries + 1):
            try:
                start = time.time()
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    stream=False
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
        
        MetricUtils.update(category, start, end, response.usage.total_tokens)
        return response.choices[0].message.content

    def generate_structured_content(self, system_prompt: str, user_prompt: str, response_model: BaseModel, category: str = "generation", max_retries: int = 5) -> BaseModel:
        """
        Generate structured content validated against a Pydantic schema.
        
        Uses the Cerebras JSON schema response format to enforce the
        output structure. The response is automatically parsed and validated.
        
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
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        for attempt in range(1, max_retries + 1):
            try:
                start = time.time()
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "workflow_schema",
                            "strict": True,
                            "schema": response_model.model_json_schema()
                        }
                    }
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
    
        MetricUtils.update(category, start, end, response.usage.total_tokens)

        try:
            return response_model.model_validate_json(response.choices[0].message.content)
        except Exception as e:
            raise ValueError(f"Failed to parse response into {response_model.__name__}: {e}")

    def init_chat(self, system_prompt: str):
        """
        Initialize an unstructured chat session with conversation history.
        
        Creates a Chat inner class instance that manually maintains message
        history across multiple exchanges, since Cerebras uses a stateless
        completion API.
        
        Args:
            system_prompt: System-level instructions for the chat session.
            
        Returns:
            A Chat instance supporting multi-turn conversation.
        """

        class Chat:
            """
            Inner class managing stateful unstructured chat sessions.
            
            Unlike the Gemini implementation, this class manually maintains
            the conversation history as a list of message dictionaries,
            since Cerebras uses a stateless completion-style API.
            
            Attributes:
                client: The Cerebras Client instance.
                model_name: The model identifier to use.
                system_prompt: System-level instructions.
                messages: List of conversation messages.
            """
            
            def __init__(self, client: Cerebras, model_name: str, system_prompt: str):
                """
                Initialize the chat session with system instructions.
                
                Args:
                    client: The Cerebras Client instance.
                    model_name: The model identifier to use.
                    system_prompt: System-level instructions.
                """
                self.client = client
                self.model_name = model_name
                self.system_prompt = system_prompt
                self.messages = [{"role": "system", "content": system_prompt}]
            
            def send_message(self, message: str, category: str = "chat", max_retries: int = 5) -> str:
                """
                Send a message in chat and return the response text.
                
                Appends the user message to history, makes the API call,
                and appends the assistant response to history.
                
                Args:
                    message: The user message to send.
                    category: Metric category. Defaults to "chat".
                    max_retries: Maximum retry attempts. Defaults to 5.
                    
                Returns:
                    The assistant's text response.
                    
                Raises:
                    Exception: If all retry attempts fail.
                """
                self.messages.append({"role": "user", "content": message})
                
                for attempt in range(1, max_retries + 1):
                    try:
                        start = time.time()
                        response = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=self.messages,
                            stream=False
                        )
                        end = time.time()
                        break
                    except Exception as e:
                        print(f"Attempt {attempt} failed: {e}")
                        if attempt == max_retries:
                            raise e
                        sleep_time = 2 ** attempt
                        print(f"Retrying in {sleep_time} seconds...")
                        time.sleep(sleep_time)
                
                MetricUtils.update(category, start, end, response.usage.total_tokens)
                
                assistant_message = response.choices[0].message.content
                self.messages.append({"role": "assistant", "content": assistant_message})
                
                return assistant_message
            
            def get_history(self) -> list[dict]:
                """
                Retrieve the full conversation history.
                
                Converts the internal message format to SimpleNamespace objects
                for compatibility with the expected interface.
                
                Returns:
                    List of message objects with role and parts attributes.
                """
                messages = []
                for msg in self.messages:
                    messages.append(SimpleNamespace(
                        role=msg["role"],
                        parts=[SimpleNamespace(text=msg["content"])]
                    ))
                return messages

        return Chat(self.client, self.model_name, system_prompt)    

    def init_structured_chat(self, system_prompt: str, response_model: BaseModel):
        """
        Initialize a structured chat session with schema-validated responses.
        
        Creates a StructuredChat inner class instance that manually maintains
        conversation history and enforces JSON schema validation on all
        assistant responses.
        
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
            the configured response_model schema using JSON schema enforcement.
            
            Attributes:
                client: The Cerebras Client instance.
                model_name: The model identifier to use.
                system_prompt: System-level instructions.
                response_model: The Pydantic model for validation.
                messages: List of conversation messages.
            """
            
            def __init__(self, client: Cerebras, model_name: str, system_prompt: str, response_model: BaseModel):
                """
                Initialize the structured chat session.
                
                Args:
                    client: The Cerebras Client instance.
                    model_name: The model identifier to use.
                    system_prompt: System-level instructions.
                    response_model: Pydantic model for response schema.
                """
                self.client = client
                self.model_name = model_name
                self.system_prompt = system_prompt
                self.response_model = response_model
                self.messages = [{"role": "system", "content": system_prompt}]
            
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
                self.messages.append({"role": "user", "content": message})
                
                for attempt in range(1, max_retries + 1):
                    try:
                        start = time.time()
                        response = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=self.messages,
                            response_format={
                                "type": "json_schema",
                                "json_schema": {
                                    "name": "structured_response_schema",
                                    "strict": True,
                                    "schema": self.response_model.model_json_schema()
                                }
                            }
                        )
                        end = time.time()
                        break
                    except Exception as e:
                        print(f"Attempt {attempt} failed: {e}")
                        if attempt == max_retries:
                            raise e
                        sleep_time = 2 ** attempt
                        print(f"Retrying in {sleep_time} seconds...")
                        time.sleep(sleep_time)
                
                MetricUtils.update(category, start, end, response.usage.total_tokens)
                
                assistant_message = response.choices[0].message.content
                self.messages.append({"role": "assistant", "content": assistant_message})
                
                try:
                    return self.response_model.model_validate_json(assistant_message)
                except Exception as e:
                    raise ValueError(f"Failed to parse response into {self.response_model.__name__}: {e}")

            def get_history(self) -> list[dict]:
                """
                Retrieve the full conversation history.
                
                Converts the internal message format to SimpleNamespace objects
                for compatibility with the expected interface.
                
                Returns:
                    List of message objects with role and parts attributes.
                """
                messages = []
                for msg in self.messages:
                    messages.append(SimpleNamespace(
                        role=msg["role"],
                        parts=[SimpleNamespace(text=msg["content"])]
                    ))
                return messages

        return StructuredChat(self.client, self.model_name, system_prompt, response_model)    
