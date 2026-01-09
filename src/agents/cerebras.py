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

# Load API key from environment or prompt user
load_dotenv()

if "CEREBRAS_API_KEY" not in os.environ:
    os.environ["CEREBRAS_API_KEY"] = getpass.getpass("Enter your Cerebras API key: ")

class CerebrasModel(str, Enum):
    GPT_OSS = "gpt-oss-120b"
    LLAMA_3_3 = "llama-3.3-70b"
    QWEN_3 = "qwen-3-32b"

class CerebrasAgent(AgentBase):

    def __init__(self, model_name: str = CerebrasModel.GPT_OSS):
        self.client = Cerebras()
        self.model_name = model_name

    def generate_content(self, system_prompt: str, user_prompt: str, category: str = "generation", max_retries: int = 5) -> str:
        """Private method to call the LLM and get a text response."""

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
                sleep_time = 2 ** attempt
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
        
        MetricUtils.update(category, start, end, response.usage.total_tokens)
        return response.choices[0].message.content

    def generate_structured_content(self, system_prompt: str, user_prompt: str, response_model: BaseModel, category: str = "generation", max_retries: int = 5) -> BaseModel:
        """Private method to get the structured response from the model."""
        
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
                sleep_time = 2 ** attempt
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
    
        MetricUtils.update(category, start, end, response.usage.total_tokens)

        try:
            return response_model.model_validate_json(response.choices[0].message.content)
        except Exception as e:
            raise ValueError(f"Failed to parse response into {response_model.__name__}: {e}")

    def init_chat(self, system_prompt: str):

        class Chat:
            def __init__(self, client: Cerebras, model_name: str, system_prompt: str):
                self.client = client
                self.model_name = model_name
                self.system_prompt = system_prompt
                self.messages = [{"role": "system", "content": system_prompt}]
            
            def send_message(self, message: str, category: str = "chat", max_retries: int = 5) -> str:
                """Send a message in chat and return the response text."""
                
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
                messages = []
                for msg in self.messages:
                    messages.append(SimpleNamespace(
                        role=msg["role"],
                        parts=[SimpleNamespace(text=msg["content"])]
                    ))
                return messages

        return Chat(self.client, self.model_name, system_prompt)    

    def init_structured_chat(self, system_prompt: str, response_model: BaseModel):

        class StructuredChat:
            def __init__(self, client: Cerebras, model_name: str, system_prompt: str, response_model: BaseModel):
                self.client = client
                self.model_name = model_name
                self.system_prompt = system_prompt
                self.response_model = response_model
                self.messages = [{"role": "system", "content": system_prompt}]
            
            def send_message(self, message: str, category: str = "chat", max_retries: int = 5) -> BaseModel:
                """Send a message in chat and return the response in JSON format."""

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
                messages = []
                for msg in self.messages:
                    messages.append(SimpleNamespace(
                        role=msg["role"],
                        parts=[SimpleNamespace(text=msg["content"])]
                    ))
                return messages

        return StructuredChat(self.client, self.model_name, system_prompt, response_model)    
