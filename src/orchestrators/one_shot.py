from pydantic import BaseModel
from utils.workflow import WorkflowUtils
from agents.base import AgentBase

class OneShotOrchestrator:

    def __init__(self, llm_agent: AgentBase):
        super().__init__(llm_agent)
    
    def generate(self, system_prompt: str, user_prompt: str, response_model: BaseModel, save: bool = True, show: bool = True, debug: bool = False) -> BaseModel:

        if debug:
            print("Generating workflow with OneShotOrchestrator...")
            print("System Prompt:", system_prompt)
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        workflow = self.llm_agent.generate_structured_content(system_prompt, user_prompt, response_model)

        if show:
            WorkflowUtils.show(workflow)
        
        if save:
            WorkflowUtils.save_json(workflow)
            WorkflowUtils.save_html(workflow)
        
        return workflow