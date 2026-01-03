import os
import json
import time
import logging
import shutil

from pydantic import BaseModel, Field, field_serializer
from typing import Optional, Type, List
from contextlib import contextmanager
from agents.base import AgentBase
from agents.google import GeminiAgent
from agents.cerebras import CerebrasAgent, CerebrasModel
from features.base import FeatureBase
from models.execution_response import ExecutionResponse
from strategies.base import StrategyBase
from tools.registry import Tool, ToolRegistry
from utils.prompt import PromptUtils
from utils.workflow import WorkflowUtils
from utils.metric import MetricUtils
from utils.logger import LoggerUtils

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RUNTIME_DIR = os.path.join(ROOT, "data", "runtime", "tools")

shutil.rmtree(RUNTIME_DIR, ignore_errors=True)
os.makedirs(RUNTIME_DIR)

@contextmanager
def working_directory(path):
    old_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_cwd)

class AgentSchema(BaseModel):
    generator: Optional[AgentBase] = Field(default_factory=lambda: CerebrasAgent(CerebrasModel.GPT_OSS))
    reviewer: Optional[AgentBase] = Field(default_factory=lambda: CerebrasAgent(CerebrasModel.GPT_OSS))
    planner: Optional[AgentBase] = Field(default_factory=lambda: CerebrasAgent(CerebrasModel.GPT_OSS))
    chatter: Optional[AgentBase] = Field(default_factory=lambda: CerebrasAgent(CerebrasModel.GPT_OSS))
    refiner: Optional[AgentBase] = Field(default_factory=lambda: CerebrasAgent(CerebrasModel.GPT_OSS))
    executor: Optional[AgentBase] = Field(default_factory=lambda: CerebrasAgent(CerebrasModel.GPT_OSS))

    model_config = { "arbitrary_types_allowed": True }

    @field_serializer("*")
    def serialize(self, agent):
        if agent is None:
            return None
        return {
            "type": agent.__class__.__name__,
            "model": getattr(agent, "model_name", None)
        }

class Context(BaseModel):
    # Input context for orchestrator operations
    agents: AgentSchema
    response_model: Type[BaseModel]
    prompt: str
    available_tools: List[Tool] 

    # Output context 
    workflow: Optional[BaseModel] = None

    model_config = {"arbitrary_types_allowed": True}

    @field_serializer("response_model")
    def serialize_response_model(self, model):
        return model.__name__

    @field_serializer("available_tools")
    def serialize_tools(self, tools):
        return [tool.name for tool in tools]
    
    @field_serializer("workflow")
    def serialize_workflow(self, workflow):
        if workflow is None:
            return None
        return json.loads(workflow.model_dump_json(indent=2))

class ConfigurableOrchestrator:

    def __init__(self, strategy: StrategyBase, available_tools: List[Tool], agents: dict[str, AgentBase] = {}, features: list[FeatureBase] = []):
        self.agents = AgentSchema(**agents)
        self.strategy = strategy
        self.available_tools = available_tools
        self.pre_features = [f for f in features if f.get_phase() == "pre"]
        self.post_features = [f for f in features if f.get_phase() == "post"]
        self.logger = LoggerUtils()
    
    def generate(self, user_prompt: str, response_model: BaseModel, max_retries: int = 5, save: bool = True, show: bool = True, debug: bool = False) -> BaseModel:
        
        self.logger.log(logging.INFO, f"Workflow generation started...")
        context = Context(agents=self.agents, response_model=response_model, prompt=user_prompt, available_tools=self.available_tools)
        self.logger.log(logging.INFO, f"Initial context: {context.model_dump_json(indent=2)}")
        
        for feature in self.pre_features:
            retry = 0
            while retry < max_retries:
                try:
                    context: Context = feature.apply(context, debug)
                    self.logger.log(logging.INFO, f"Context after pre-feature '{feature.__class__.__name__}': {context.model_dump_json(indent=2)}")
                    break
                except Exception as e:
                    retry += 1
                    retry_time = 2 ** retry
                    self.logger.log(logging.ERROR, f"Error applying pre-feature '{feature.__class__.__name__}': {e}. Retrying {retry}/{max_retries} in {retry_time} seconds...")
                    time.sleep(retry_time)

            if retry == max_retries:
                self.logger.log(logging.ERROR, f"Failed to apply pre-feature '{feature.__class__.__name__}' after {max_retries} retries.")
                raise RuntimeError(f"Error applying pre-feature '{feature.__class__.__name__}': {e}")

        retry = 0
        while retry < max_retries:
            try:
                context.workflow = self.strategy.generate(context, debug)
                break
            except Exception as e:
                retry += 1
                retry_time = 2 ** retry
                self.logger.log(logging.ERROR, f"Error during strategy generation: {e}. Retrying {retry}/{max_retries} in {retry_time} seconds...")
                time.sleep(retry_time)
        
        if not context.workflow:
            self.logger.log(logging.ERROR, f"Failed to generate workflow after {max_retries} retries.")
            raise RuntimeError(f"Failed to generate workflow after {max_retries} retries.")

        self.logger.log(logging.INFO, f"Generated workflow: {context.workflow.model_dump_json(indent=2)}")

        for feature in self.post_features:
            retry = 0
            while retry < max_retries:
                try:
                    context: Context = feature.apply(context, debug)
                    self.logger.log(logging.INFO, f"Context after post-feature '{feature.__class__.__name__}': {context.model_dump_json(indent=2)}")
                    break
                except Exception as e:
                    retry += 1
                    retry_time = 2 ** retry
                    self.logger.log(logging.ERROR, f"Error applying post-feature '{feature.__class__.__name__}': {e}. Retrying {retry}/{max_retries} in {retry_time} seconds...")
                    time.sleep(retry_time)
            
            if retry == max_retries:
                self.logger.log(logging.ERROR, f"Failed to apply post-feature '{feature.__class__.__name__}' after {max_retries} retries.")
                raise RuntimeError(f"Error applying post-feature '{feature.__class__.__name__}': {e}")
        
        self.logger.log(logging.INFO, f"Workflow generation completed.")

        if show:
            try:
                WorkflowUtils.show(context.workflow)
            except Exception as e:
                self.logger.log(logging.ERROR, f"Error showing workflow: {e}")

        if save:
            try:
                WorkflowUtils.save_workflow(context.workflow)
                WorkflowUtils.save_visualization(context.workflow)
            except Exception as e:
                self.logger.log(logging.ERROR, f"Error saving workflow: {e}")
        
        return context.workflow

    def run(self, workflow: BaseModel, max_retries: int = 5, debug: bool = False) -> None:

        self.logger.log(logging.INFO, f"Workflow execution started...")

        if debug:
            print("Running workflow...")
            input("Press Enter to continue or Ctrl+C to exit...")

        state = {}
        execution_prompt = PromptUtils.get_system_prompt("workflow_execution")

        if not self.agents.executor:
            raise ValueError("Executor agent not found.")

        chat_session = self.agents.executor.init_structured_chat(execution_prompt, ExecutionResponse)
        next_message = workflow.model_dump_json()

        while True:

            retry = 0
            while retry < max_retries:
                try:
                    response = chat_session.send_message(next_message, category="execution")
                    break
                except Exception as e:
                    retry += 1
                    retry_time = 2 ** retry
                    self.logger.log(logging.ERROR, f"Error during workflow execution at step with state '{json.dumps(state)}': {e}. Retrying {retry}/{max_retries} in {retry_time} seconds...")
                    time.sleep(retry_time)
            
            if not response:
                self.logger.log(logging.ERROR, f"No response received during workflow execution at step with state '{json.dumps(state)}'.")
                raise RuntimeError(f"No response received during workflow execution at step with state '{json.dumps(state)}'.")
            
            try:
                response_schema = ExecutionResponse.model_validate(response)
            except Exception as e:
                self.logger.log(logging.ERROR, f"Invalid execution response schema: {e}")
                raise ValueError(f"Invalid execution response schema: {e}")

            payload = response_schema.model_dump()
            self.logger.log(logging.INFO, f"Execution response received: {json.dumps(payload, indent=2)}")
            
            if debug:
                print("Response received:", json.dumps(payload, indent=2), "\n")
                input("Press Enter to continue or Ctrl+C to exit...")
            
            step = payload.get("step")

            step_id = step.get("id")
            step_action = step.get("action")
            is_final = step.get("is_final")

            if is_final:
                self.logger.log(logging.INFO, f"Final step '{step_id}' reached. Ending workflow execution.")
                break
            
            if step_action == "call_tool":
                tool_name = step.get("tool_name")
                tool_params = {p["key"]: p["value"] for p in step.get("tool_parameters")}

                if debug:
                    print(f"Calling tool '{tool_name}' with params: {tool_params}\n")
                    input("Press Enter to continue or Ctrl+C to exit...")
                
                try:
                    with working_directory(RUNTIME_DIR):
                        tool = ToolRegistry.get(tool_name)
                        results = tool.run(**tool_params)
                        self.logger.log(logging.INFO, f"Tool '{tool_name}' for step '{step_id}' executed with results: {json.dumps(results, indent=2)}")
                except Exception as e:
                    self.logger.log(logging.ERROR, f"Error executing tool '{tool_name}': {e}")
                    raise RuntimeError(f"Error executing tool '{tool_name}': {e}")
                
                state[step_id] = results
                next_message = json.dumps({
                    "state": state
                })
                
                if debug:
                    print(f"Tool '{tool_name}' returned results: {results}\n")
                    input("Press Enter to continue or Ctrl+C to exit...")
            elif step_action == "call_llm":
                response = step.get("response")

                self.logger.log(logging.INFO, f"LLM action for step '{step_id}' with response: {response}")

                state[step_id] = response
                next_message = json.dumps({
                    "state": state
                })

                if debug:
                    print(f"LLM action for step '{step_id}' with response: {response}\n")
                    input("Press Enter to continue or Ctrl+C to exit...")
            else:
                self.logger.log(logging.ERROR, f"Unknown action '{step_action}' received during workflow execution.")
                raise ValueError(f"Unknown action '{step_action}' received during workflow execution.")
        
        MetricUtils.finish()
        try:
            WorkflowUtils.save_execution(state)
            self.logger.log(logging.INFO, f"Workflow execution completed and saved.")
        except Exception as e:
            self.logger.log(logging.ERROR, f"Error saving workflow: {e}")