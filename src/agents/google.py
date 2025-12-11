import os
import getpass
import json

from google.genai import Client
from google.genai.types import GenerateContentConfig
from pydantic import BaseModel
from enum import Enum
from tools.registry import ToolRegistry
from dotenv import load_dotenv

# Load API key from environment or prompt user
load_dotenv()

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")

class GeminiModel(str, Enum):
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"

class GeminiAgent:
    def __init__(self, model_name: str = GeminiModel.GEMINI_2_5_FLASH):
        self.client = Client()
        self.model_name = model_name
    
    def generate_workflow(self, system_prompt: str, user_prompt: str, response_model: BaseModel, debug: bool = False) -> BaseModel:
        """Generate a workflow in one-shot."""

        if debug:
            print("System Prompt:", system_prompt)
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        return self._call_llm_structured(system_prompt, user_prompt, response_model)

    def chat(self, system_prompt: str, user_prompt: str, debug: bool = False):
        """Engage in a chat using the Gemini model with structured response."""

        if debug:
            print("System Prompt:", system_prompt)
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        # Instantiate a chat session with system prompt    
        chat_session = self.client.chats.create(
            model=self.model_name,
            config=GenerateContentConfig(
                system_instruction=system_prompt
            )
        )

        # Send user prompt and get initial reasoning
        try:
            initial_text = chat_session.send_message(f"Workflow prompt is '{user_prompt}'").text
            print("Initial reasoning:", initial_text, "\n")
        except Exception as e:
            raise RuntimeError(f"Chat message failed: {e}")
        
        # Iterative workflow refinement with questions and answers
        while True:
            user_input = input("Your message (type 'exit'): ")
            if user_input.lower() == 'exit':
                break

            response = chat_session.send_message(user_input).text
            print(f"Response: {response}\n")
        
        messages = chat_session.get_history()
        return messages
    
    def generate_workflow_from_chat(self, messages, system_prompt: str, response_model: BaseModel, debug: bool = False) -> BaseModel:
        """Generate a workflow from the chat history."""

        # Compile chat history into a single prompt
        history_text = "\n".join(
            f"{msg.role.capitalize()}: {msg.parts[0].text}" for msg in messages
        )
        final_prompt = f"Based on the conversation we just had, please generate the required JSON workflow. The conversation was:\n\n---\n{history_text}\n\n---"

        if debug:
            print("System Prompt for final generation:", system_prompt)
            print("Final Prompt for workflow generation:", final_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        return self._call_llm_structured(system_prompt, final_prompt, response_model)

    def execute_workflow(self, system_prompt: str, workflow: BaseModel, response_model: BaseModel, debug : bool = False):
        """Execute the generated workflow."""

        step_results = {}
        workflow_text = workflow.model_dump_json()
        workflow_json = json.loads(workflow_text)

        if debug:
            print("System Prompt for execution:", system_prompt)
            print("Workflow to execute:", workflow_text)
            input("Press Enter to continue or Ctrl+C to exit...")
        
        chat_session = self.client.chats.create(
            model=self.model_name,
            config=GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type='application/json',
                response_schema=response_model
            )
        )

        steps_count = 0
        total_steps = len(workflow_json["steps"])
        next_message = f"Workflow to execute: \n\n{workflow_text}"

        while True:

            try:
                response = chat_session.send_message(next_message).text
            except Exception as e:
                raise RuntimeError(f"Chat message failed during workflow execution: {e}")

            try:
                response_json = json.loads(response)
                response_obj = response_model.model_validate(response_json)
                payload = response_obj.model_dump()
            except Exception as e:
                raise ValueError(f"Failed to parse step response: {e}")
            
            if debug:
                print("Executor received payload:", json.dumps(payload, indent=2))
                input("Press Enter to continue...")
            
            pstep = payload.get("step_id")
            paction = payload.get("action")

            if steps_count >= total_steps:
                print("\nFinal response from workflow execution:")
                print(json.dumps(payload, indent=2))
                break

            elif paction == "call_tool":
                tool_name = payload.get("tool_name")
                parameters = {p["key"]: p["value"] for p in payload.get("tool_parameters", [])}

                print(f"\nExecutor requests tool call for {pstep}: {tool_name} with {parameters}")
                
                tool = ToolRegistry.get(tool_name)
                
                try:
                    results = tool.run(**parameters)
                except Exception as e:
                    raise RuntimeError(f"Tool {tool_name} execution failed: {e}")
                
                step_results[pstep] = results
                next_message = json.dumps({"tool_result": results, "state": step_results, "resume": True})
                if debug:
                    print(f"Tool {tool_name} returned results: {results}")
                    input("Press Enter to continue...")
            elif paction == "call_llm":
                results = payload.get("llm_results")

                print(f"\nExecutor received LLM action for {pstep} with results: {results}")

                step_results[pstep] = results
                next_message = json.dumps({"state": step_results, "resume": True})
                if debug:
                    input("Press Enter to continue...")
            else:
                raise ValueError(f"Unknown step action: {paction}")
            
            steps_count += 1
        
        print("Workflow execution completed.")
            
    def _call_llm_structured(self, system_prompt: str, user_prompt: str, response_model: BaseModel) -> BaseModel:
        """Private method to get the structured response from the model."""
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type= 'application/json',
                response_schema=response_model
            )
        )

        try:
            return response_model.model_validate_json(response.text)
        except Exception as e:
            raise ValueError(f"Failed to parse response into {response_model.__name__}: {e}")