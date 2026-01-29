"""
Validation Refinement Feature
=============================

This module implements the ValidationRefinementFeature, a post-generation
enhancement that performs iterative review and refinement cycles on
generated workflows until quality criteria are met.

Main Responsibilities:
    - Establish review-refine dialogue between specialized agents
    - Iterate refinement until reviewer approves or max rounds reached
    - Track workflow evolution across refinement iterations

Key Dependencies:
    - models.responses.review_response: For structured review output
    - features.base: For FeatureBase interface
    - tools.registry: For tool information injection
    - utils.prompt: For prompt template loading

Use Cases:
    - High-quality workflow generation requiring multiple passes
    - Complex workflows benefiting from iterative improvement
    - Quality-critical applications requiring validation

Architecture:
    Uses a dual-agent architecture where:
    - Reviewer agent evaluates workflow quality and identifies issues
    - Refiner agent applies corrections based on reviewer feedback
    - Process iterates until approval or max_rounds exhausted
"""

from models.responses.review_response import ReviewResponse
from features.base import FeatureBase
from tools.registry import ToolRegistry 
from utils.prompt import PromptUtils


class ValidationRefinementFeature(FeatureBase):
    """
    Post-generation feature for iterative validation and refinement.
    
    Implements a review-refine loop where a reviewer agent evaluates
    the workflow and a refiner agent applies corrections. The process
    continues until the reviewer approves or maximum rounds are reached.
    
    Attributes:
        _phase: Set to "post" for post-generation execution.
        max_rounds: Maximum number of review-refine iterations.
    
    Required Agents:
        - reviewer: Agent for evaluating workflow quality.
        - refiner: Agent for applying suggested improvements.
    
    Example:
        >>> feature = ValidationRefinementFeature(max_rounds=5)
        >>> context = feature.apply(context, max_retries=3, debug=False)
    """

    def __init__(self, max_rounds: int = 3):
        """
        Initialize the feature with iteration limit.
        
        Args:
            max_rounds: Maximum review-refine iterations (default: 3).
        """
        self._phase = "post"
        super().__init__(max_rounds=max_rounds)

    def apply(self, context, max_retries, debug):
        """
        Execute iterative validation and refinement process.
        
        Establishes chat sessions with reviewer and refiner agents,
        then alternates between review and refinement phases until
        the reviewer signals approval or max_rounds is exhausted.
        
        Args:
            context: Orchestrator context containing workflow and agents.
            max_retries: Maximum retry attempts for LLM calls.
            debug: Whether to enable debug output.
            
        Returns:
            Modified context with refined workflow.
            
        Raises:
            ValueError: If max_rounds is less than 1.
            ValueError: If no workflow is provided.
            ValueError: If reviewer or refiner agent is not configured.
        """
        # Validate iteration parameter
        if self.max_rounds < 1:
            raise ValueError("max_rounds must be a positive integer.")

        agents = context.agents
        user_prompt = context.prompt
        available_tools = context.available_tools
        workflow = context.workflow

        # Validate workflow exists
        if not workflow:
            raise ValueError("No workflow provided for iterative refinement.")
        
        # Serialize workflow for LLM processing
        workflow_json = workflow.model_dump_json(indent=2)

        if debug:
            print("  Iterative validation and refinement in progress...")
            print("User Prompt:", user_prompt)
            print("Workflow to refine:", workflow_json)
            input("Press Enter to continue or Ctrl+C to exit...")

        # Prepare refinement prompt with tool context
        refine_prompt = PromptUtils.get_system_prompt("workflow_refinement")
        refine_prompt_with_tools = PromptUtils.inject(refine_prompt, ToolRegistry.to_prompt_format(tools=available_tools), original_user_prompt=user_prompt)

        # Prepare review prompt with tool context and original workflow reference
        review_prompt = PromptUtils.get_system_prompt("workflow_review")
        review_prompt_with_tools = PromptUtils.inject(review_prompt, ToolRegistry.to_prompt_format(tools=available_tools), original_user_prompt=user_prompt, original_workflow=workflow_json)

        # Validate required agents are configured
        if not agents.refiner:
            raise ValueError("Refiner agent not found.")
        
        if not agents.reviewer:
            raise ValueError("Reviewer agent not found.")
        
        # Initialize chat sessions for stateful dialogue
        reviewer_chat = agents.reviewer.init_structured_chat(review_prompt_with_tools, ReviewResponse)
        refiner_chat = agents.refiner.init_structured_chat(refine_prompt_with_tools, workflow.__class__)
        
        # Review-refine iteration loop
        for round in range(self.max_rounds):

            next_message = f"Current Workflow State: {workflow_json}"

            # === Review Phase ===
            review_response = reviewer_chat.send_message(next_message, category="review", max_retries=max_retries)

            try:
                review = ReviewResponse.model_validate(review_response)
            except Exception as e:
                raise ValueError(f"Invalid review response format: {e}")

            if debug:
                print(f"\nRound {round+1} review completed:")
                print(f"  Review Response: {review.model_dump_json(indent=2)}\n")
                input("Press Enter to continue or Ctrl+C to exit...")
            
            # Check for reviewer approval signal
            if hasattr(review.result, "end_review") and review.result.end_review:
                break

            next_message = f"Reviewer Comments: {review.model_dump_json(indent=2)}"

            # === Refinement Phase ===
            context.workflow = refiner_chat.send_message(next_message, category="refinement", max_retries=max_retries)
            workflow_json = context.workflow.model_dump_json(indent=2)

            if debug:
                print(f"\nRound {round+1} refinement completed:")
                print(f"  Refined Workflow: {workflow_json}\n")
                input("Press Enter to continue or Ctrl+C to exit...")
        
        return context