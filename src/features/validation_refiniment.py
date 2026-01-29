from models.responses.review_response import ReviewResponse
from features.base import FeatureBase
from tools.registry import ToolRegistry 
from utils.prompt import PromptUtils

class ValidationRefinementFeature(FeatureBase):
    """Enhancement feature for iterative validation and refinement."""

    def __init__(self, max_rounds: int = 3):
        self._phase = "post"
        super().__init__(max_rounds=max_rounds)

    def apply(self, context, max_retries, debug):

        if self.max_rounds < 1:
            raise ValueError("max_rounds must be a positive integer.")

        agents = context.agents
        user_prompt = context.prompt
        available_tools = context.available_tools
        workflow = context.workflow

        if not workflow:
            raise ValueError("No workflow provided for iterative refinement.")
        
        workflow_json = workflow.model_dump_json(indent=2)

        if debug:
            print("  Iterative validation and refinement in progress...")
            print("User Prompt:", user_prompt)
            print("Workflow to refine:", workflow_json)
            input("Press Enter to continue or Ctrl+C to exit...")

        refine_prompt = PromptUtils.get_system_prompt("workflow_refinement")
        refine_prompt_with_tools = PromptUtils.inject(refine_prompt, ToolRegistry.to_prompt_format(tools=available_tools), original_user_prompt=user_prompt)

        review_prompt = PromptUtils.get_system_prompt("workflow_review")
        review_prompt_with_tools = PromptUtils.inject(review_prompt, ToolRegistry.to_prompt_format(tools=available_tools), original_user_prompt=user_prompt, original_workflow=workflow_json)

        if not agents.refiner:
            raise ValueError("Refiner agent not found.")
        
        if not agents.reviewer:
            raise ValueError("Reviewer agent not found.")
        
        reviewer_chat = agents.reviewer.init_structured_chat(review_prompt_with_tools, ReviewResponse)
        refiner_chat = agents.refiner.init_structured_chat(refine_prompt_with_tools, workflow.__class__)
        
        for round in range(self.max_rounds):

            next_message = f"Current Workflow State: {workflow_json}"

            # Review phase
            review_response = reviewer_chat.send_message(next_message, category="review", max_retries=max_retries)

            try:
                review = ReviewResponse.model_validate(review_response)
            except Exception as e:
                raise ValueError(f"Invalid review response format: {e}")

            if debug:
                print(f"\nRound {round+1} review completed:")
                print(f"  Review Response: {review.model_dump_json(indent=2)}\n")
                input("Press Enter to continue or Ctrl+C to exit...")
            
            if hasattr(review.result, "end_review") and review.result.end_review:
                break

            next_message = f"Reviewer Comments: {review.model_dump_json(indent=2)}"

            # Refinement phase
            context.workflow = refiner_chat.send_message(next_message, category="refinement", max_retries=max_retries)
            workflow_json = context.workflow.model_dump_json(indent=2)

            if debug:
                print(f"\nRound {round+1} refinement completed:")
                print(f"  Refined Workflow: {workflow_json}\n")
                input("Press Enter to continue or Ctrl+C to exit...")
        
        return context