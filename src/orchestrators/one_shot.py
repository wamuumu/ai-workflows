import time

from pydantic import BaseModel
from agents.base import AgentBase
from orchestrators.base import OrchestratorBase
from utils.workflow import WorkflowUtils
from utils.prompt import PromptUtils
from utils.metric import MetricUtils
from tools.registry import ToolRegistry

class OneShotOrchestrator(OrchestratorBase):

    def __init__(self, agents: dict[str, AgentBase], skip_execution: bool = False):
        super().__init__(agents, skip_execution)
    
    def generate(self, user_prompt: str, response_model: BaseModel, save: bool = True, show: bool = True, debug: bool = False) -> BaseModel:

        if debug:
            print("Generating workflow with OneShotOrchestrator...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        system_prompt = PromptUtils.get_system_prompt("workflow_generation")
        system_prompt_with_tools = PromptUtils.inject(system_prompt, ToolRegistry.to_prompt_format())

        if not self.agents.generator:
            raise ValueError("Generator agent not found.")

        start = time.time()
        workflow = self.agents.generator.generate_structured_content(system_prompt_with_tools, user_prompt, response_model)
        end = time.time()
        MetricUtils.update_generation_metrics({"time_taken": end - start})

        if show:
            WorkflowUtils.show(workflow)
        
        if save:
            WorkflowUtils.save_json(workflow)
            WorkflowUtils.save_html(workflow)
        
        return workflow