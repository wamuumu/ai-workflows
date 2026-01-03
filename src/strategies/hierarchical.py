import time

from strategies.base import StrategyBase
from tools.registry import ToolRegistry
from utils.prompt import PromptUtils

class HierarchicalStrategy(StrategyBase):
    """Hierarchical generation strategy where task is decomposed into subtasks recursively."""

    def __init__(self):
        super().__init__()

    def generate(self, context, max_retries, debug):
        
        agents = context.agents
        user_prompt = context.prompt
        available_tools = context.available_tools
        response_model = context.response_model

        if debug:
            print("Generating workflow with HierarchicalStrategy...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")
        
        planning_prompt = PromptUtils.get_system_prompt("workflow_planning")
        task_generation_prompt = PromptUtils.get_system_prompt("task_generation")
        task_generation_prompt_with_tools = PromptUtils.inject(task_generation_prompt, ToolRegistry.to_prompt_format(tools=available_tools))
        merge_prompt = PromptUtils.get_system_prompt("task_merge")

        if not agents.planner:
            raise ValueError("Planner agent not found.")
        
        if not agents.generator:
            raise ValueError("Generator agent not found.")
        
        planner_chat = agents.planner.init_chat(planning_prompt)

        subtasks = []
        next_message = user_prompt

        while True:
            retry = 0
            while retry < max_retries:
                try:
                    plan = planner_chat.send_message(next_message, category="generation")
                    break
                except Exception as e:
                    retry += 1
                    retry_time = 2 ** retry
                    print(f"Planning retry {retry}/{max_retries} after error: {e}. Retrying in {retry_time} seconds...")
                    time.sleep(retry_time)
            
            if retry == max_retries:
                raise RuntimeError("Max retries exceeded during task planning.")

            if "END_PLANNING" in plan.upper().strip():
                break

            subtasks.append(plan)
            next_message = f"Sub-task completed. Continue planning the next sub-task.\n"
        
        if debug:
            print("Final Subtasks:", subtasks)
            input("Press Enter to continue or Ctrl+C to exit...")
        
        fragments = []
        for subtask in subtasks:
            retry = 0
            while retry < max_retries:
                try:
                    fragment = agents.generator.generate_structured_content(task_generation_prompt_with_tools, subtask, response_model)
                    fragments.append(fragment)
                    break
                except Exception as e:
                    retry += 1
                    retry_time = 2 ** retry
                    print(f"Generation retry {retry}/{max_retries} after error: {e}. Retrying in {retry_time} seconds...")
                    time.sleep(retry_time)
            
            if retry == max_retries:
                raise RuntimeError("Max retries exceeded during subtask generation.")

            if debug:
                print(f"\n\nSubtask: {subtask}\n Generated Fragment: {fragment}")
                input("Press Enter to continue or Ctrl+C to exit...")

        fragment_string = "\n\n".join([f.model_dump_json() for f in fragments])
        print("Generated Fragments JSON:", fragment_string)
        
        retry = 0
        while retry < max_retries:
            try:
                merged = agents.planner.generate_structured_content(merge_prompt, fragment_string, response_model)
                return response_model.model_validate(merged)
            except Exception as e:
                retry += 1
                retry_time = 2 ** retry
                print(f"Merging retry {retry}/{max_retries} after error: {e}. Retrying in {retry_time} seconds...")
                time.sleep(retry_time)
        
        if retry == max_retries:
            raise RuntimeError("Max retries exceeded during task merging.")
        