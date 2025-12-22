from strategies.base import StrategyBase
from tools.registry import ToolRegistry
from utils.prompt import PromptUtils
from utils.workflow import WorkflowUtils

class MonolithicStrategy(StrategyBase):
    """One-shot generation strategy where a single agent generates the entire workflow in one go."""

    def __init__(self):
        super().__init__()

    def generate(self, context, save, show, debug):

        agents = context.agents
        user_prompt = context.prompt
        response_model = context.response_model
        
        if debug:
            print("Generating workflow with MonolithicStrategy...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        if not agents.generator:
            raise ValueError("Generator agent not found.")
        
        system_prompt = PromptUtils.get_system_prompt("workflow_generation")
        system_prompt = PromptUtils.inject(system_prompt, ToolRegistry.to_prompt_format())

        workflow = agents.generator.generate_structured_content(system_prompt, user_prompt, response_model)

        if show:
            WorkflowUtils.show(workflow)
        
        if save:
            WorkflowUtils.save_json(workflow)
            WorkflowUtils.save_html(workflow)
        
        return workflow