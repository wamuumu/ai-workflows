import os
import getpass
import json

from cerebras.cloud.sdk import Cerebras
from pydantic import BaseModel
from enum import Enum
from tools.registry import ToolRegistry
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
            input("Press Enter to continue or Ctrl+C to exit...")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self._call_llm_structured(messages, response_model)

    def chat(self, system_prompt: str, user_prompt: str, debug: bool = False):
        """Chat using the Cerebras model with multi-turn conversation."""

        ### Debug prints (same as your Gemini version)
        if debug:
            print("System Prompt:", system_prompt)
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

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
        
        # Compile chat history into a single prompt
        history_text = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}" for msg in messages
        )
        final_prompt = f"{system_prompt}\n\nChat History:\n{history_text}\n\nPlease provide the final workflow."

        if debug:
            print("System Prompt for final generation:", system_prompt)
            print("Final Prompt:", final_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": final_prompt}
        ]

        return self._call_llm_structured(messages, response_model)
        
    def execute_workflow(self, system_prompt: str, workflow: BaseModel, response_model: BaseModel, debug : bool = False):
        """Execute the generated workflow."""
        
        step_results = {}
        workflow_text = workflow.model_dump_json()
        workflow_json = json.loads(workflow_text)

        if debug:
            print("System Prompt for final generation:", system_prompt)
            print("Workflow JSON:", workflow_text)
            input("Press Enter to continue or Ctrl+C to exit...")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Workflow to execute: \n\n{workflow_text}"}
        ]

        steps_count = 0
        total_steps = len(workflow_json["steps"])

        while True:
            response: BaseModel = self._call_llm_structured(messages, response_model)

            try:
                payload = response.model_dump()
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
                messages.append({"role": "assistant", "content": json.dumps(payload)})
                messages.append({"role": "system", "content": json.dumps({"tool_result": results, "state": step_results, "resume": True})})
                if debug:
                    print(f"Tool {tool_name} returned results: {results}")
                    input("Press Enter to continue...")
            elif paction == "call_llm":
                results = payload.get("llm_results")

                print(f"\nExecutor received LLM action for {pstep} with results: {results}")

                step_results[pstep] = results
                messages.append({"role": "assistant", "content": json.dumps(payload)})
                messages.append({"role": "system", "content": json.dumps({"state": step_results, "resume": True})})
                if debug:
                    input("Press Enter to continue...")
            else:
                raise ValueError(f"Unknown step action: {paction}")

            steps_count += 1
        
        print("Workflow execution completed.")
            
    def _call_llm(self, messages: list) -> str:
        """Private method to call the LLM and get a text response."""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=False
        )

        return response.choices[0].message.content

    def _call_llm_structured(self, messages: list, response_model: BaseModel) -> BaseModel:
        """Private method to get the structured response from the model."""
        
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

        json_data = json.dumps(json.loads(response.choices[0].message.content))

        try:
            return response_model.model_validate_json(json_data)
        except Exception as e:
            raise ValueError(f"Failed to parse response into {response_model.__name__}: {e}")

        
