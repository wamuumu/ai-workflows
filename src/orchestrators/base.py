import json

from pydantic import BaseModel
from typing import Optional, Type
from agents.base import AgentBase
from agents.google import GeminiAgent
from agents.cerebras import CerebrasAgent, CerebrasModel
from features.base import FeatureBase
from models.execution_response import ExecutionResponse
from strategies.base import StrategyBase
from tools.registry import ToolRegistry
from utils.prompt import PromptUtils
from utils.workflow import WorkflowUtils

class AgentSchema(BaseModel):
    generator: Optional[AgentBase] = CerebrasAgent()
    discriminator: Optional[AgentBase] = GeminiAgent()
    planner: Optional[AgentBase] = CerebrasAgent(CerebrasModel.LLAMA_3_3)
    chatter: Optional[AgentBase] = CerebrasAgent(CerebrasModel.LLAMA_3_3)
    refiner: Optional[AgentBase] = CerebrasAgent(CerebrasModel.LLAMA_3_3)
    executor: Optional[AgentBase] = CerebrasAgent(CerebrasModel.LLAMA_3_3)

    model_config = { "arbitrary_types_allowed": True }

class Context(BaseModel):
    # Input context for orchestrator operations
    agents: AgentSchema
    response_model: Type[BaseModel]
    prompt: str

    # Output context 
    workflow: Optional[BaseModel] = None

    model_config = {"arbitrary_types_allowed": True}

class ConfigurableOrchestrator:

    def __init__(self, strategy: StrategyBase, agents: dict[str, AgentBase] = {}, features: list[FeatureBase] = []):
        self.agents = AgentSchema(**agents)
        self.strategy = strategy
        self.pre_features = [f for f in features if f.get_phase() == "pre"]
        self.post_features = [f for f in features if f.get_phase() == "post"]
    
    def generate(self, user_prompt: str, response_model: BaseModel, save: bool = True, show: bool = True, debug: bool = False) -> BaseModel:
        
        context = Context(agents=self.agents, response_model=response_model, prompt=user_prompt)
        
        for feature in self.pre_features:
            context = feature.apply(context, debug)

        context.workflow = self.strategy.generate(context, debug)

        for feature in self.post_features:
            context = feature.apply(context, debug)
        
        if show:
            WorkflowUtils.show(context.workflow)
        
        if save:
            WorkflowUtils.save_json(context.workflow)
            WorkflowUtils.save_html(context.workflow)

        return context.workflow
    
    def run(self, workflow: BaseModel, debug: bool = False) -> None:

        if debug:
            print("Running workflow...")
            input("Press Enter to continue or Ctrl+C to exit...")

        step_results = {}
        workflow_json = workflow.model_dump_json()
        workflow_obj = json.loads(workflow_json)
        execution_prompt = PromptUtils.get_system_prompt("workflow_execution")

        if not self.agents.executor:
            raise ValueError("Executor agent not found.")

        chat_session = self.agents.executor.init_structured_chat(execution_prompt, ExecutionResponse)
        next_message = workflow.model_dump_json()

        while True:
            try:
                response = chat_session.send_message(next_message, category="execution")
            except Exception as e:
                raise RuntimeError(f"Chat message failed: {e}")
            
            response_schema = ExecutionResponse.model_validate_json(response)
            payload = response_schema.model_dump()
            
            if debug:
                print("Response received:", json.dumps(payload, indent=2), "\n")
                input("Press Enter to continue or Ctrl+C to exit...")
            
            p_step = payload.get("step_id")
            p_action = payload.get("action")
            current_step = next((step for step in workflow_obj["steps"] if step["id"] == p_step), None)

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
                
                retry = False
                try:
                    results = tool.run(**tool_params)
                except Exception as e:
                    results = { "error": str(e) }
                    retry = True
                
                step_results[p_step] = results
                next_message = json.dumps({
                    "step_id": p_step,
                    "tool_results": results,
                    "state": step_results,
                    "resume": True,
                    "retry": retry
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