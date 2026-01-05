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

# Load API key from environment or prompt user
load_dotenv()

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")

class GeminiModel(str, Enum):
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"

class GeminiAgent(AgentBase):

    def __init__(self, model_name: str = GeminiModel.GEMINI_2_5_FLASH):
        self.client = Client()
        self.model_name = model_name

    def generate_content(self, system_prompt: str, user_prompt: str, category: str = "generation") -> str:
        
        start = time.time()
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=GenerateContentConfig(
                system_instruction=system_prompt
            )
        )
        end = time.time()
        MetricUtils.update(category, start, end, response.usage_metadata.total_token_count)

        return response.text
            
    def generate_structured_content(self, system_prompt: str, user_prompt: str, response_model: BaseModel, category: str = "generation") -> BaseModel:
        start = time.time()
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type= 'application/json',
                response_schema=response_model
            )
        )
        end = time.time()
        MetricUtils.update(category, start, end, response.usage_metadata.total_token_count)

        try:
            return response_model.model_validate_json(response.text)
        except Exception as e:
            raise ValueError(f"Failed to parse response into {response_model.__name__}: {e}")
        
    def init_chat(self, system_prompt: str):

        class Chat:
            def __init__(self, client: Client, model_name: str, system_prompt: str):
                self.chat_instance = client.chats.create(
                    model=model_name,
                    config=GenerateContentConfig(
                        system_instruction=system_prompt
                    )
                )

            def send_message(self, message: str, category: str = "chat") -> str:
                """Send a message in chat and return the response text."""
                
                start = time.time()
                response = self.chat_instance.send_message(message)
                end = time.time()
                MetricUtils.update(category, start, end, response.usage_metadata.total_token_count)
                
                return response.text

            def get_history(self):
                return self.chat_instance.get_history()
            
        return Chat(self.client, self.model_name, system_prompt)  

    def init_structured_chat(self, system_prompt: str, response_model: BaseModel):

        class StructuredChat:
            def __init__(self, client: Client, model_name: str, system_prompt: str, response_model: BaseModel):
                self.chat_instance = client.chats.create(
                    model=model_name,
                    config=GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type='application/json',
                        response_schema=response_model
                    )
                )
                self.response_model = response_model

            def send_message(self, message: str, category: str = "chat") -> BaseModel:
                """Send a message in chat and return the response text."""
                
                start = time.time()
                response = self.chat_instance.send_message(message)
                end = time.time()
                MetricUtils.update(category, start, end, response.usage_metadata.total_token_count)
                
                try:
                    return self.response_model.model_validate_json(response.text)
                except Exception as e:
                    raise ValueError(f"Failed to parse response into {self.response_model.__name__}: {e}")

            def get_history(self):
                return self.chat_instance.get_history()
        
        return StructuredChat(self.client, self.model_name, system_prompt, response_model)
