import json
import time

from pydantic import BaseModel
from agents.base import AgentBase
from orchestrators.base import OrchestratorBase
from utils.workflow import WorkflowUtils
from utils.prompt import PromptUtils
from utils.metric import MetricUtils
from tools.registry import ToolRegistry

class HierarchicalOrchestrator(OrchestratorBase):

    def __init__(self, agents: dict[str, AgentBase], skip_execution: bool = False):
        super().__init__(agents, skip_execution)
    
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
        
        fragments = []
        next_message = user_prompt
        while True:
            
            start = time.time()
            plan = planner_chat.send_message(next_message).text
            end = time.time()
            MetricUtils.update_generation_metrics({"time_taken": end - start})

            if debug:
                print("Generated Plan:", plan)
                input("Press Enter to continue or Ctrl+C to exit...")

            if plan.strip() == "END":
                break
            
            start = time.time()
            sub_workflow = self.agents.generator.generate_structured_content(generation_prompt_with_tools, plan, response_model)
            end = time.time()
            MetricUtils.update_generation_metrics({"time_taken": end - start})
            
            sub_workflow_dict = sub_workflow.model_dump()
            fragments.append(sub_workflow_dict)

            if debug:
                print("Generated Sub-Workflow:", json.dumps(sub_workflow_dict, indent=2))
                input("Press Enter to continue or Ctrl+C to exit...")
            
            next_message = f"Sub-task completed. Output produced:\n{json.dumps(sub_workflow_dict, indent=2)}\n"
        
        step_counter = 1
        wf_tmp = { "title": "test", "description": "test", "steps": [] }
        for fragment in fragments:
            for step in fragment.get("steps", []):
                step["id"] = f"step_{step_counter}"
                step_counter += 1
            wf_tmp["steps"].extend(fragment.get("steps", []))
        
        workflow = response_model.model_validate(wf_tmp)

        if show:
            WorkflowUtils.show(workflow)
        
        if save:
            WorkflowUtils.save_json(workflow)
            WorkflowUtils.save_html(workflow)

        return workflow
        