import json
import time

from pydantic import BaseModel
from agents.base import AgentBase
from orchestrators.base import OrchestratorBase
from utils.workflow import WorkflowUtils
from utils.prompt import PromptUtils
from utils.metric import MetricUtils
from tools.registry import ToolRegistry

class GenerativeAdversarialOrchestrator(OrchestratorBase):

    def __init__(self, agents: dict[str, AgentBase], max_rounds: int, skip_execution: bool = False):
        super().__init__(agents, skip_execution)
        self.max_rounds = max_rounds
    
    def generate(self, user_prompt: str, response_model: BaseModel, save: bool = True, show: bool = True, debug: bool = False) -> BaseModel:
        
        if not self.max_rounds or self.max_rounds < 1:
            raise ValueError("max_rounds must be a positive integer.")

        if debug:
            print("Generating workflow with GenerativeAdversarialOrchestrator...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        generation_prompt = PromptUtils.get_system_prompt("workflow_generation")
        generation_prompt_with_tools = PromptUtils.inject(generation_prompt, ToolRegistry.to_prompt_format())
        critique_prompt = PromptUtils.get_system_prompt("workflow_critique")
        critique_prompt_with_tools = PromptUtils.inject(critique_prompt, ToolRegistry.to_prompt_format(), workflow_expected_schema=response_model.model_json_schema(), user_prompt=user_prompt)
        
        if not self.agents.generator:
            raise ValueError("Generator agent not found.")

        if not self.agents.discriminator:
            raise ValueError("Discriminator agent not found.")
        
        generator_chat = self.agents.generator.init_structured_chat(generation_prompt_with_tools, response_model)
        discriminator_chat = self.agents.discriminator.init_chat(critique_prompt_with_tools)
        
        next_message = user_prompt
        for _ in range(self.max_rounds):
            
            start = time.time()
            response = generator_chat.send_message(next_message)
            end = time.time()
            MetricUtils.update("generation", start, end, response.usage_metadata.total_token_count)

            workflow = json.dumps(json.loads(response.text), indent=2)
            if debug:
                print("Generated Plan:", workflow)
                input("Press Enter to continue or Ctrl+C to exit...")
            
            start = time.time()
            critique = discriminator_chat.send_message(workflow)
            end = time.time()
            MetricUtils.update("generation", start, end, critique.usage_metadata.total_token_count)
            
            critique_text = critique.text
            if debug:
                print("Discriminator Critique:", critique_text)
                input("Press Enter to continue or Ctrl+C to exit...")
            
            if "END_CRITIQUE" in critique_text.upper().strip():
                break
            
            next_message = f"Please revise the workflow based on the following critique:\n{critique_text}\n"

        workflow = response_model.model_validate_json(response.text)

        if show:
            WorkflowUtils.show(workflow)
        
        if save:
            WorkflowUtils.save_json(workflow)
            WorkflowUtils.save_html(workflow)

        return workflow
        