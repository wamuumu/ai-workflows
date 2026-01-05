import time

from features.base import FeatureBase
from tools.registry import ToolRegistry 
from utils.prompt import PromptUtils

class ValidationRefinementFeature(FeatureBase):
    """Enhancement feature for iterative validation and refinement."""

    def __init__(self, max_rounds: int = 5):
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
        
        reviewer_chat = agents.reviewer.init_chat(review_prompt_with_tools)
        refiner_chat = agents.refiner.init_structured_chat(refine_prompt_with_tools, workflow.__class__)
        
        for round in range(self.max_rounds):

            next_message = f"Current Workflow State: {workflow_json}"

            # Review phase
            retry = 0
            while retry < max_retries:
                try:
                    review_response = reviewer_chat.send_message(next_message, category="review")
                    break
                except Exception as e:
                    retry += 1
                    retry_time = 2 ** retry
                    print(f"Review retry {retry}/{max_retries} after error: {e}. Retrying in {retry_time} seconds...")
                    time.sleep(retry_time)
            
            if retry == max_retries:
                raise RuntimeError("Max retries exceeded during workflow review.")

            if debug:
                print(f"\nRound {round+1} review completed:")
                print(f"  Review Comments: {review_response}\n")
                input("Press Enter to continue or Ctrl+C to exit...")
            
            if "END_REVIEW" in review_response.upper().strip():
                break

            next_message = f"Reviewer Comments: {review_response}"

            # Refinement phase
            retry = 0
            while retry < max_retries:
                try:
                    context.workflow = refiner_chat.send_message(next_message, category="refinement")
                    workflow_json = context.workflow.model_dump_json(indent=2)
                    break
                except Exception as e:
                    retry += 1
                    retry_time = 2 ** retry
                    print(f"Refinement retry {retry}/{max_retries} after error: {e}. Retrying in {retry_time} seconds...")
                    time.sleep(retry_time)
            
            if retry == max_retries:
                raise RuntimeError("Max retries exceeded during workflow refinement.")

            if debug:
                print(f"\nRound {round+1} refinement completed:")
                print(f"  Refined Workflow: {workflow_json}\n")
                input("Press Enter to continue or Ctrl+C to exit...")
        
        return context