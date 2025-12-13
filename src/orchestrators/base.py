from abc import ABC, abstractmethod
from pydantic import BaseModel
from models.response import Response
from agents.base import AgentBase
from utils.prompt import PromptUtils
from tools.registry import ToolRegistry

class OrchestratorBase(ABC):

    def __init__(self, llm_agent: AgentBase):
        self.llm_agent = llm_agent

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, response_model: BaseModel, save: bool = True, show: bool = True, debug: bool = False) -> BaseModel:
        pass

    @abstractmethod
    def generate_from_messages(self, system_prompt: str, messages: list[dict[str, str]], response_model: BaseModel, debug: bool = False) -> BaseModel:
        # ! Remember to format chat messages in a compatible way

        history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in messages])

        if debug:
            print("Generating workflow from chat messages...")
            print("System Prompt:", system_prompt)
            print("Chat History:", history)
            input("Press Enter to continue or Ctrl+C to exit...")
        
        self.llm_agent.generate_structured_content(system_prompt, history, response_model)


    @abstractmethod
    def refine(self, system_prompt: str, user_prompt: str, workflow: BaseModel, debug: bool = False) -> BaseModel:

        if debug:
            print("Refining workflow...")
            print("System Prompt:", system_prompt)
            print("Existing Workflow:", workflow.model_dump_json())
            input("Press Enter to continue or Ctrl+C to exit...")

        refine_prompt = PromptUtils.get_system_prompt("workflow_refinement")
        refine_prompt_with_tools = PromptUtils.inject(refine_prompt, ToolRegistry.to_prompt_format(), original_prompt=user_prompt)
        return self.llm_agent.generate_structured_content(refine_prompt_with_tools, user_prompt, workflow.__class__)
    
    @abstractmethod
    def run(self, workflow: BaseModel, debug: bool = False) -> None:

        if debug:
            print("Running workflow...")
            input("Press Enter to continue or Ctrl+C to exit...")

        execute_workflow_prompt = PromptUtils.get_system_prompt("workflow_execution")
        self.llm_agent.execute_workflow(execute_workflow_prompt, workflow, response_model=Response)