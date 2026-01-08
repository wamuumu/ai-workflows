from features.base import FeatureBase
from tools.registry import ToolRegistry 
from utils.prompt import PromptUtils

class RefinementFeature(FeatureBase):
    """Enhancement feature for workflow refinement."""

    def __init__(self):
        self._phase = "post"
        super().__init__()

    def apply(self, context, max_retries, debug):

        agents = context.agents
        user_prompt = context.prompt
        available_tools = context.available_tools
        workflow = context.workflow

        if not workflow:
            raise ValueError("No workflow provided for refinement.")
        
        workflow_json = workflow.model_dump_json(indent=2)

        if debug:
            print("Refining workflow...")
            print("User Prompt:", user_prompt)
            print("Workflow to refine:", workflow_json)
            input("Press Enter to continue or Ctrl+C to exit...")

        refine_prompt = PromptUtils.get_system_prompt("workflow_refinement")
        refine_prompt_with_tools = PromptUtils.inject(refine_prompt, ToolRegistry.to_prompt_format(tools=available_tools), original_user_prompt=user_prompt)

        if not agents.refiner:
            raise ValueError("Refiner agent not found.")
        
        context.workflow = agents.refiner.generate_structured_content(refine_prompt_with_tools, workflow_json, workflow.__class__, category="refinement", max_retries=max_retries)
        
        return context