import json

from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Optional
from models.response import Response
from agents.base import AgentBase
from utils.prompt import PromptUtils
from tools.registry import ToolRegistry

class AgentSchema(BaseModel):
    generator: Optional[AgentBase] = None
    planner: Optional[AgentBase] = None
    chatter: Optional[AgentBase] = None
    refiner: Optional[AgentBase] = None
    executor: Optional[AgentBase] = None

    model_config = { "arbitrary_types_allowed": True }

class OrchestratorBase(ABC):

    def __init__(self, agents: dict[str, AgentBase]):
        self.agents = AgentSchema(**agents)

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, response_model: BaseModel, save: bool = True, show: bool = True, debug: bool = False) -> BaseModel:
        pass

    def chat_with_user(self, user_prompt: str, debug: bool = False) -> str:

        if debug:
            print("Chatting with user...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        chat_prompt = PromptUtils.get_system_prompt("chat_clarification")
        chat_prompt_with_tools = PromptUtils.inject(chat_prompt, ToolRegistry.to_prompt_format())

        if not self.agents.get("chatter"):
            raise ValueError("Chatter agent not found.")

        chat_session = self.agents.get("chatter").init_chat(chat_prompt_with_tools)
        next_message = user_prompt

        while True:
            try:
                response = chat_session.send_message(next_message).text
            except Exception as e:
                raise RuntimeError(f"Chat message failed: {e}")
            
            print(f"\nLLM: {response}\n")
            
            next_message = input("User: ")
            if next_message.lower() in ["exit", "quit", "q"]:
                break
        
        return chat_session.get_history()

    def generate_from_messages(self, messages, response_model: BaseModel, debug: bool = False) -> BaseModel:
        
        user_prompt = messages[1].parts[0].text
        history = "\n".join([f"{msg.role.capitalize()}: {msg.parts[0].text}" for msg in messages[2:]])  # Skip system prompt and first user message

        if debug:
            print("Generating workflow from chat messages...")
            print("Chat History:", history)
            input("Press Enter to continue or Ctrl+C to exit...")

        system_prompt = PromptUtils.get_system_prompt("workflow_generation")
        system_prompt_with_tools_and_chat = PromptUtils.inject(system_prompt, ToolRegistry.to_prompt_format(), chat_history=history)

        if not self.agents.get("generator"):
            raise ValueError("Generator agent not found.")

        return self.agents.get("generator").generate_structured_content(system_prompt_with_tools_and_chat, user_prompt, response_model)

    def refine(self, user_prompt: str, workflow: BaseModel, debug: bool = False) -> BaseModel:

        workflow_json = workflow.model_dump_json()

        if debug:
            print("Refining workflow...")
            print("User Prompt:", user_prompt)
            print("Workflow to refine:", workflow_json)
            input("Press Enter to continue or Ctrl+C to exit...")

        refine_prompt = PromptUtils.get_system_prompt("workflow_refinement")
        refine_prompt_with_tools = PromptUtils.inject(refine_prompt, ToolRegistry.to_prompt_format(), original_user_prompt=user_prompt)

        if not self.agents.get("refiner"):
            raise ValueError("Refiner agent not found.")

        return self.agents.get("refiner").generate_structured_content(refine_prompt_with_tools, workflow_json, workflow.__class__)
    
    def run(self, workflow: BaseModel, debug: bool = False) -> None:

        if debug:
            print("Running workflow...")
            input("Press Enter to continue or Ctrl+C to exit...")

        step_results = {}
        workflow_json = json.loads(workflow.model_dump_json())
        execution_prompt = PromptUtils.get_system_prompt("workflow_execution")

        if not self.agents.get("executor"):
            raise ValueError("Executor agent not found.")

        chat_session = self.agents.get("executor").init_structured_chat(execution_prompt, Response)
        next_message = workflow.model_dump_json()

        while True:
            try:
                response = chat_session.send_message(next_message).text
                response_schema = Response.model_validate_json(response)
                payload = response_schema.model_dump()
            except Exception as e:
                raise RuntimeError(f"Chat message failed: {e}")
            
            if debug:
                print("Response received:", json.dumps(payload, indent=2), "\n")
                input("Press Enter to continue or Ctrl+C to exit...")
            
            p_step = payload.get("step_id")
            p_action = payload.get("action")
            current_step = next((step for step in workflow_json["steps"] if step["id"] == p_step), None)

            if not current_step:
                raise ValueError(f"Step ID '{p_step}' not found in workflow.")

            if current_step["is_final"]:
                break

            if p_action == "call_tool":
                tool_name = payload.get("tool_name")
                tool_params = {p["key"]: p["value"] for p in payload.get("tool_parameters", [])}

                if debug:
                    print(f"Calling tool '{tool_name}' with params: {tool_params}\n")
                    input("Press Enter to continue or Ctrl+C to exit...")
                
                tool = ToolRegistry.get(tool_name)
                
                try:
                    results = tool.run(**tool_params)
                except Exception as e:
                    raise RuntimeError(f"Tool '{tool_name}' execution failed: {e}")
                
                step_results[p_step] = results
                next_message = json.dumps({
                    "step_id": p_step,
                    "tool_results": results,
                    "state": step_results,
                    "resume": True
                })
                
                if debug:
                    print(f"Tool '{tool_name}' returned results: {results}\n")
                    input("Press Enter to continue or Ctrl+C to exit...")
            elif p_action == "call_llm":
                results = payload.get("llm_results")
                step_results[p_step] = results
                next_message = json.dumps({
                    "step_id": p_step,
                    "llm_results": results,
                    "state": step_results,
                    "resume": True
                })

                if debug:
                    print(f"LLM action for step '{p_step}' with results: {results}\n")
                    input("Press Enter to continue or Ctrl+C to exit...")
            else:
                raise ValueError(f"Unknown action '{p_action}' received during workflow execution.")
        
        print("\nWorkflow execution completed!")