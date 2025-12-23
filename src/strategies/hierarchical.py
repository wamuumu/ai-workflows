from strategies.base import StrategyBase
from tools.registry import ToolRegistry
from utils.prompt import PromptUtils

class HierarchicalStrategy(StrategyBase):
    """Hierarchical generation strategy where task is decomposed into subtasks recursively."""

    def __init__(self):
        super().__init__()

    def generate(self, context, debug):
        
        agents = context.agents
        user_prompt = context.prompt
        response_model = context.response_model

        if debug:
            print("Generating workflow with HierarchicalStrategy...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")
        
        planning_prompt = PromptUtils.get_system_prompt("workflow_planning")
        task_generation_prompt = PromptUtils.get_system_prompt("task_generation")
        task_generation_prompt_with_tools = PromptUtils.inject(task_generation_prompt, ToolRegistry.to_prompt_format())

        if not agents.planner:
            raise ValueError("Planner agent not found.")
        
        if not agents.generator:
            raise ValueError("Generator agent not found.")
        
        planner_chat = agents.planner.init_chat(planning_prompt)

        subtasks = []
        next_message = user_prompt

        while True:
            plan = planner_chat.send_message(next_message, category="generation")

            if debug:
                print("Generated Plan:", plan)
                input("Press Enter to continue or Ctrl+C to exit...")

            if "END_PLANNING" in plan.upper().strip():
                break

            subtasks.append(plan)
            next_message = f"Sub-task completed. Continue planning the next sub-task.\n"
        
        fragments = []
        for subtask in subtasks:
            fragment = agents.generator.generate_structured_content(task_generation_prompt_with_tools, subtask, response_model)
            fragments.append(fragment)

            if debug:
                print(f"Subtask: {subtask}\n\n Generated Fragment: {fragment}")
                input("Press Enter to continue or Ctrl+C to exit...")
        
        step_counter = 1
        merged = {
            "title": "Hierarchical Workflow",
            "description": "A workflow generated using hierarchical strategy.",
            "steps": []
        }

        for fragment in fragments:
            for step in fragment.get("steps", []):
                step["id"] = f"step_{step_counter}"
                step_counter += 1
                merged["steps"].append(step)

        return response_model.model_validate(merged)