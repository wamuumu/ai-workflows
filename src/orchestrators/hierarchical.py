import json

from pydantic import BaseModel
from agents.base import AgentBase
from orchestrators.base import OrchestratorBase
from utils.workflow import WorkflowUtils
from utils.prompt import PromptUtils
from tools.registry import ToolRegistry

class HierarchicalOrchestrator(OrchestratorBase):

    def __init__(self, agents: dict[str, AgentBase]):
        super().__init__(agents)
    
    def generate(self, user_prompt: str, response_model: BaseModel, save: bool = True, show: bool = True, debug: bool = False) -> BaseModel:
        
        if debug:
            print("Generating workflow with HierarchicalOrchestrator...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        plan_prompt = PromptUtils.get_system_prompt("workflow_planning")
        plan_prompt_with_tools = PromptUtils.inject(plan_prompt, ToolRegistry.to_prompt_format())
        generation_prompt = PromptUtils.get_system_prompt("workflow_generation")
        generation_prompt_with_tools = PromptUtils.inject(generation_prompt, ToolRegistry.to_prompt_format())

        if not self.agents.planner:
            raise ValueError("Planner agent not found.")
        
        if not self.agents.generator:
            raise ValueError("Generator agent not found.")
        
        planner_chat = self.agents.planner.init_chat(plan_prompt_with_tools)
        generator_chat = self.agents.generator.init_structured_chat(generation_prompt_with_tools, response_model)
        
        fragments = []
        next_message = user_prompt
        while True:

            plan = planner_chat.send_message(next_message).text

            if debug:
                print("Generated Plan:", plan)
                input("Press Enter to continue or Ctrl+C to exit...")

            if "END" in plan:
                break

            sub_workflow = generator_chat.send_message(plan).text
            sub_workflow = response_model.model_validate_json(sub_workflow)
            sub_workflow = json.loads(sub_workflow.model_dump_json())

            if debug:
                print("Generated Sub-Workflow:", json.dumps(sub_workflow, indent=2))
                input("Press Enter to continue or Ctrl+C to exit...")
            
            fragments.append(sub_workflow)
            next_message = f"Sub-task completed. The result is:\n{sub_workflow}\n"
        
        step_counter = 1
        wf_tmp = { "title": "test", "description": "test", "steps": [] }
        for fragment in fragments:
            for step in fragment["steps"]:
                step["id"] = f"step_{step_counter}"
                step_counter += 1
            wf_tmp["steps"].extend(fragment["steps"])
        
        workflow = response_model.model_validate(wf_tmp)

        if show:
            WorkflowUtils.show(workflow)
        
        if save:
            WorkflowUtils.save_json(workflow)
            WorkflowUtils.save_html(workflow)

        return workflow
        