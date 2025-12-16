import time 

from pydantic import BaseModel
from agents.base import AgentBase
from orchestrators.base import OrchestratorBase
from utils.workflow import WorkflowUtils
from utils.metric import MetricUtils

class ChatDrivenOrchestrator(OrchestratorBase):

    def __init__(self, agents: dict[str, AgentBase], skip_execution: bool = False):
        super().__init__(agents, skip_execution)
    
    def generate(self, user_prompt: str, response_model: BaseModel, save: bool = True, show: bool = True, debug: bool = False) -> BaseModel:
        
        chat_history = self.chat_with_user(user_prompt, debug=debug)

        start = time.time()
        workflow = self.generate_from_messages(chat_history, response_model, debug=debug)
        end = time.time()
        MetricUtils.update_generation_metrics({"time_taken": end - start})

        if show:
            WorkflowUtils.show(workflow)
        
        if save:
            WorkflowUtils.save_json(workflow)
            WorkflowUtils.save_html(workflow)
        
        return workflow