import os
import json
import logging
import shutil

from pydantic import BaseModel, Field, field_serializer
from typing import Optional, Type, List
from contextlib import contextmanager
from agents.base import AgentBase
from agents.google import GeminiAgent, GeminiModel
from agents.cerebras import CerebrasAgent, CerebrasModel
from features.base import FeatureBase
from models.responses.execution_response import ExecutionResponse
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

        if debug:
            self.logger.log(logging.INFO, f"Initial context: {context.model_dump_json(indent=2)}")
        
        for feature in self.pre_features:
            context: Context = feature.apply(context, max_retries, debug)
            self.logger.log(logging.INFO, f"Context after pre-feature '{feature.__class__.__name__}': {context.model_dump_json(indent=2)}")

        context.workflow = self.strategy.generate(context, max_retries, debug)

        self.logger.log(logging.INFO, f"Generated workflow: {context.workflow.model_dump_json(indent=2)}")

        for feature in self.post_features:
            context: Context = feature.apply(context, max_retries, debug)
            self.logger.log(logging.INFO, f"Context after post-feature '{feature.__class__.__name__}': {context.model_dump_json(indent=2)}")
        
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
            self.logger.log(logging.INFO, "Running workflow...")
            input("Press Enter to continue or Ctrl+C to exit...")

        state = {}
        execution_prompt = PromptUtils.get_system_prompt("workflow_execution")

        if not self.agents.executor:
            raise ValueError("Executor agent not found.")

        chat_session = self.agents.executor.init_structured_chat(execution_prompt, ExecutionResponse)
        next_message = workflow.model_dump_json()

        while True:

            response = chat_session.send_message(next_message, category="execution", max_retries=max_retries)
            
            try:
                response_schema = ExecutionResponse.model_validate(response)
            except Exception as e:
                self.logger.log(logging.ERROR, f"Invalid execution response schema: {e}")
                raise ValueError(f"Invalid execution response schema: {e}")

            payload = response_schema.model_dump()
            self.logger.log(logging.INFO, f"Execution response received: {json.dumps(payload, indent=2)}")
            
            if debug:
                self.logger.log(logging.INFO, f"Response received: {json.dumps(payload, indent=2)}")
                input("Press Enter to continue or Ctrl+C to exit...")
            
            step = payload.get("step")

            step_id = str(step.get("id"))
            step_action = step.get("action")
            is_final = step.get("is_final")

            if is_final:
                self.logger.log(logging.INFO, f"Final step '{step_id}' reached. Ending workflow execution.")
                break
            
            if step_action == "call_tool":
                tool_name = step.get("tool_name")
                parameters = {p.get("key"): p.get("value") for p in step.get("parameters", [])}

                if debug:
                    self.logger.log(logging.INFO, f"Calling tool '{tool_name}' with: {parameters}")
                    input("Press Enter to continue or Ctrl+C to exit...")
                
                try:
                    with working_directory(RUNTIME_DIR):
                        tool = ToolRegistry.get(tool_name)
                        results = tool.run(**parameters)
                        self.logger.log(logging.INFO, f"Tool '{tool_name}' for step '{step_id}' executed with results: {json.dumps(results, indent=2)}")
                except Exception as e:
                    self.logger.log(logging.ERROR, f"Error executing tool '{tool_name}': {e}")
                    raise RuntimeError(f"Error executing tool '{tool_name}': {e}")
                
                state[step_id] = results
                next_message = json.dumps({
                    "state": state
                })
                
                if debug:
                    self.logger.log(logging.INFO, f"Tool '{tool_name}' returned: {results}")
                    input("Press Enter to continue or Ctrl+C to exit...")
            elif step_action == "call_llm":
                response = step.get("response")

                self.logger.log(logging.INFO, f"LLM action for step '{step_id}' with response: {response}")

                state[step_id] = response
                next_message = json.dumps({
                    "state": state
                })

                if debug:
                    self.logger.log(logging.INFO, f"LLM action for step '{step_id}' with response: {response}")
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