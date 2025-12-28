from strategies.base import StrategyBase
from tools.registry import ToolRegistry
from utils.prompt import PromptUtils

class MonolithicStrategy(StrategyBase):
    """One-shot generation strategy where a single agent generates the entire workflow in one go."""

    def __init__(self):
        super().__init__()

    def generate(self, context, debug):

        agents = context.agents
        user_prompt = context.prompt
        available_tools = context.available_tools
        response_model = context.response_model
        
        if debug:
            print("Generating workflow with MonolithicStrategy...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        if not agents.generator:
            raise ValueError("Generator agent not found.")
        
        system_prompt = PromptUtils.get_system_prompt("workflow_generation")
        system_prompt_with_tools = PromptUtils.inject(system_prompt, ToolRegistry.to_prompt_format(tools=available_tools))

        return agents.generator.generate_structured_content(system_prompt_with_tools, user_prompt, response_model)