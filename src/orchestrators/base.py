import json
import time

from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
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

class MetricSet(BaseModel):
    time_taken: float = 0
    number_of_calls: int = 0

class MetricSchema(BaseModel):
    generation: MetricSet = Field(default_factory=MetricSet)
    execution: MetricSet = Field(default_factory=MetricSet)

class OrchestratorBase(ABC):

    def __init__(self, agents: dict[str, AgentBase]):
        self.agents = AgentSchema(**agents)
        self.metrics = MetricSchema()
        self.skip_execution = True

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

        if not self.agents.chatter:
            raise ValueError("Chatter agent not found.")

        chat_session = self.agents.chatter.init_chat(chat_prompt_with_tools)
        next_message = user_prompt

        while True:
            try:
                start = time.time()
                response = chat_session.send_message(next_message).text
                end = time.time()
                self.metrics.generation.time_taken += end - start
                self.metrics.generation.number_of_calls += 1
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

        if not self.agents.generator:
            raise ValueError("Generator agent not found.")

        start = time.time()
        workflow = self.agents.generator.generate_structured_content(system_prompt_with_tools_and_chat, user_prompt, response_model)
        end = time.time()
        self.metrics.generation.time_taken += end - start
        self.metrics.generation.number_of_calls += 1
        return workflow

    def refine(self, user_prompt: str, workflow: BaseModel, debug: bool = False) -> BaseModel:

        workflow_json = workflow.model_dump_json()

        if debug:
            print("Refining workflow...")
            print("User Prompt:", user_prompt)
            print("Workflow to refine:", workflow_json)
            input("Press Enter to continue or Ctrl+C to exit...")

        refine_prompt = PromptUtils.get_system_prompt("workflow_refinement")
        refine_prompt_with_tools = PromptUtils.inject(refine_prompt, ToolRegistry.to_prompt_format(), original_user_prompt=user_prompt)

        if not self.agents.refiner:
            raise ValueError("Refiner agent not found.")

        start = time.time()
        workflow = self.agents.refiner.generate_structured_content(refine_prompt_with_tools, workflow_json, workflow.__class__)
        end = time.time()
        self.metrics.generation.time_taken += end - start
        self.metrics.generation.number_of_calls += 1
        return workflow
    
    def run(self, workflow: BaseModel, debug: bool = False) -> None:

        if self.skip_execution:
            return

        if debug:
            print("Running workflow...")
            input("Press Enter to continue or Ctrl+C to exit...")

        step_results = {}
        workflow_json = json.loads(workflow.model_dump_json())
        execution_prompt = PromptUtils.get_system_prompt("workflow_execution")

        if not self.agents.executor:
            raise ValueError("Executor agent not found.")

        chat_session = self.agents.executor.init_structured_chat(execution_prompt, Response)
        next_message = workflow.model_dump_json()

        while True:
            try:
                start = time.time()
                response = chat_session.send_message(next_message).text
                end = time.time()
                self.metrics.execution.time_taken += end - start
                self.metrics.execution.number_of_calls += 1
            except Exception as e:
                raise RuntimeError(f"Chat message failed: {e}")
            
            response_schema = Response.model_validate_json(response)
            payload = response_schema.model_dump()
            
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
    
    def display_metrics(self):
        print("\nOrchestrator Metrics:")
        dumped_metrics = self.metrics.model_dump()
        for phase, metrics in dumped_metrics.items():
            print(f"  {phase.capitalize()}:")
            for metric_name, value in metrics.items():
                if metric_name == "time_taken":
                    print(f"    {metric_name.replace('_', ' ').capitalize()}: {value:.2f} seconds")
                else:
                    print(f"    {metric_name.replace('_', ' ').capitalize()}: {value}")