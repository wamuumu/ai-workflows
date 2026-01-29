"""
Monolithic Strategy Module
==========================

This module implements the MonolithicStrategy, a one-shot workflow
generation approach where the entire workflow is produced in a single
LLM call.

Main Responsibilities:
    - Generate complete workflow in single API call
    - Inject tool information into generation prompt
    - Return fully-formed workflow model

Key Dependencies:
    - strategies.base: For StrategyBase interface
    - tools.registry: For tool information injection
    - utils.prompt: For prompt template loading

Use Cases:
    - Simple workflows with clear requirements
    - Fast generation with lower latency requirements
    - Baseline generation for comparison with iterative strategies

Trade-offs:
    - Pros: Fast, single API call, lower cost
    - Cons: No iterative refinement, may miss complex dependencies
"""

from strategies.base import StrategyBase
from tools.registry import ToolRegistry
from utils.prompt import PromptUtils


class MonolithicStrategy(StrategyBase):
    """
    One-shot workflow generation strategy.
    
    Generates the complete workflow in a single LLM call without
    iterative building or multi-phase analysis. Best suited for
    straightforward workflows where requirements are clear.
    
    Attributes:
        None specific to this strategy.
    
    Required Agents:
        - generator: Agent for producing the complete workflow.
    """

    def __init__(self):
        """Initialize the monolithic strategy with no additional parameters."""
        super().__init__()

    def generate(self, context, max_retries, debug):
        """
        Generate complete workflow in a single LLM call.
        
        Constructs a system prompt with tool information and sends
        the user prompt to the generator agent for one-shot workflow
        production.
        
        Args:
            context: Orchestrator context containing prompt, agents,
                tools, and response model specification.
            max_retries: Maximum retry attempts for LLM API calls.
            debug: Whether to enable debug output.
            
        Returns:
            Complete workflow model as specified by context.response_model.
            
        Raises:
            ValueError: If generator agent is not configured.
        """
        agents = context.agents
        user_prompt = context.prompt
        available_tools = context.available_tools
        response_model = context.response_model
        
        if debug:
            print("Generating workflow with MonolithicStrategy...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        # Validate generator agent is configured
        if not agents.generator:
            raise ValueError("Generator agent not found.")
        
        # Load and prepare generation prompt with tool context
        system_prompt = PromptUtils.get_system_prompt("workflow_generation")
        system_prompt_with_tools = PromptUtils.inject(system_prompt, ToolRegistry.to_prompt_format(tools=available_tools))

        # Generate complete workflow in single call
        return agents.generator.generate_structured_content(system_prompt_with_tools, user_prompt, response_model, max_retries=max_retries)