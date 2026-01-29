"""
Refinement Feature
==================

This module implements the RefinementFeature, a post-generation enhancement
that refines generated workflows by having an LLM agent review and improve
the workflow structure and content.

Main Responsibilities:
    - Take generated workflow and refine it for quality
    - Inject tool information for context-aware refinement
    - Preserve workflow structure while improving content

Key Dependencies:
    - features.base: For FeatureBase interface
    - tools.registry: For tool information injection
    - utils.prompt: For prompt template loading

Use Cases:
    - Post-generation quality improvement
    - Single-pass workflow enhancement
    - Automated workflow optimization
"""

from features.base import FeatureBase
from tools.registry import ToolRegistry 
from utils.prompt import PromptUtils


class RefinementFeature(FeatureBase):
    """
    Post-generation feature for single-pass workflow refinement.
    
    Sends the generated workflow back to an LLM agent for refinement
    with access to tool information and the original user prompt for
    context-aware improvements.
    
    Attributes:
        _phase: Set to "post" for post-generation execution.
    
    Required Agents:
        - refiner: Agent for applying workflow improvements.
    """

    def __init__(self):
        """Initialize the feature with post-generation phase."""
        self._phase = "post"
        super().__init__()

    def apply(self, context, max_retries, debug):
        """
        Refine the generated workflow through LLM review.
        
        Sends the workflow JSON to the refiner agent along with tool
        information and the original prompt for contextual refinement.
        
        Args:
            context: Orchestrator context containing workflow and agents.
            max_retries: Maximum retry attempts for LLM calls.
            debug: Whether to enable debug output.
            
        Returns:
            Modified context with refined workflow.
            
        Raises:
            ValueError: If no workflow is provided for refinement.
            ValueError: If refiner agent is not configured.
        """
        agents = context.agents
        user_prompt = context.prompt
        available_tools = context.available_tools
        workflow = context.workflow

        # Validate workflow exists for refinement
        if not workflow:
            raise ValueError("No workflow provided for refinement.")
        
        # Serialize workflow for LLM processing
        workflow_json = workflow.model_dump_json(indent=2)

        if debug:
            print("Refining workflow...")
            print("User Prompt:", user_prompt)
            print("Workflow to refine:", workflow_json)
            input("Press Enter to continue or Ctrl+C to exit...")

        # Load and prepare refinement prompt with tool context
        refine_prompt = PromptUtils.get_system_prompt("workflow_refinement")
        refine_prompt_with_tools = PromptUtils.inject(refine_prompt, ToolRegistry.to_prompt_format(tools=available_tools), original_user_prompt=user_prompt)

        # Validate refiner agent is configured
        if not agents.refiner:
            raise ValueError("Refiner agent not found.")
        
        # Generate refined workflow maintaining original structure type
        context.workflow = agents.refiner.generate_structured_content(refine_prompt_with_tools, workflow_json, workflow.__class__, category="refinement", max_retries=max_retries)
        
        return context