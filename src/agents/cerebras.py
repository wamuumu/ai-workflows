import os
import getpass
import json

from cerebras.cloud.sdk import Cerebras
from pydantic import BaseModel
from enum import Enum
from dotenv import load_dotenv

# Load API key from environment or prompt user
load_dotenv()

if "CEREBRAS_API_KEY" not in os.environ:
    os.environ["CEREBRAS_API_KEY"] = getpass.getpass("Enter your Cerebras API key: ")

class CerebrasModel(str, Enum):
    GPT_OSS = "gpt-oss-120b"
    LLAMA_3_3 = "llama-3.3-70b"
    LLAMA_3_1 = "llama3.1-8b"
    QWEN_3 = "qwen-3-32b"

class CerebrasAgent:
    def __init__(self, model_name: str = CerebrasModel.GPT_OSS):
        self.client = Cerebras()
        self.model_name = model_name
    
    def generate_workflow(self, system_prompt: str, user_prompt: str, response_model: BaseModel, debug: bool = False) -> BaseModel:
        """Generate a workflow in one-shot."""

        if debug:
            print("System Prompt:", system_prompt)
            print("User Prompt:", user_prompt)
            exit = input("Continue? (y/n): ")
            if exit.lower() != 'y':
                raise KeyboardInterrupt("Execution stopped by user.")
        
        return self._call_llm_structured(system_prompt, user_prompt, response_model)

    def chat(self, system_prompt: str, user_prompt: str, debug: bool = False):
        """Chat using the Cerebras model with multi-turn conversation."""

        ### Debug prints (same as your Gemini version)
        if debug:
            print("System Prompt:", system_prompt)
            print("User Prompt:", user_prompt)
            cont = input("Continue? (y/n): ")
            if cont.lower() != "y":
                raise KeyboardInterrupt("Execution stopped by user.")

        # Keep the full conversation history
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Workflow prompt is '{user_prompt}'"}
        ]

        # Send initial user message
        try:
            initial_text = self._call_llm(messages)
            print("Initial reasoning:", initial_text, "\n")
        except Exception as e:
            raise RuntimeError(f"Chat message failed: {e}")

        # Start interactive loop
        while True:
            user_input = input("Your message (type 'exit'): ")
            if user_input.lower() == "exit":
                break

            # Append user message
            messages.append({"role": "user", "content": user_input})
            response = self._call_llm(messages)
            print("Response:", response, "\n")

            # Append model response to conversation history
            messages.append({"role": "assistant", "content": response})
        
        return messages
    
    def generate_workflow_from_chat(self, messages: list, system_prompt: str, response_model: BaseModel, debug: bool = False) -> BaseModel:
        """Generate a workflow from the chat history."""
        
        if debug:
            print("System Prompt for final generation:", system_prompt)
            cont = input("Continue? (y/n): ")
            if cont.lower() != "y":
                raise KeyboardInterrupt("Execution stopped by user.")

        # Compile chat history into a single prompt
        history_text = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}" for msg in messages
        )
        final_prompt = f"{system_prompt}\n\nChat History:\n{history_text}\n\nPlease provide the final workflow."

        return self._call_llm_structured(system_prompt, final_prompt, response_model)
        
    def execute_workflow(self, system_prompt: str, workflow: BaseModel):
        raise NotImplementedError("Workflow execution is not implemented yet.")

    def _call_llm(self, messages: list) -> str:
        """Private method to call the LLM and get a text response."""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=False
        )

        return response.choices[0].message.content

    def _call_llm_structured(self, system_prompt: str, user_prompt: str, response_model: BaseModel) -> BaseModel:
        """Private method to get the structured response from the model."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "workflow_schema",
                    "stritct": True,
                    "schema": response_model.model_json_schema()
                }
            }
        )

        json_data = json.dumps(json.loads(response.choices[0].message.content))

        try:
            return response_model.model_validate_json(json_data)
        except Exception as e:
            raise ValueError(f"Failed to parse response into {response_model.__name__}: {e}")

        
