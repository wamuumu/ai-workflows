"""
Incremental Strategy Module
===========================

This module implements the IncrementalStrategy, an iterative workflow
generation approach that builds workflows in batches of 1-3 steps
per LLM call.

Main Responsibilities:
    - Generate workflow steps incrementally in small batches
    - Maintain context through sliding window optimization
    - Handle workflow completion detection

Key Dependencies:
    - models.responses.incremental_next_step: For batch step response models
    - strategies.base: For StrategyBase interface
    - tools.registry: For tool information and validation
    - utils.prompt: For prompt template loading

Use Cases:
    - Complex workflows requiring step-by-step reasoning
    - Long workflows that exceed single-prompt token limits
    - Scenarios requiring fine-grained generation control

Optimizations:
    - Batch generation: Produces 1-3 steps per call to reduce API overhead
    - Sliding window: Keeps recent steps in full detail, summarizes older steps
    - Early termination: Detects workflow completion via is_complete flag

Trade-offs:
    - Pros: Better handling of complex logic, reduces hallucination
    - Cons: Higher latency, more API calls, higher cost
"""

from typing import List

from models.responses.incremental_next_step import NextLinearStepBatch, NextStructuredStepBatch
from strategies.base import StrategyBase
from tools.registry import ToolRegistry
from utils.prompt import PromptUtils


class IncrementalStrategy(StrategyBase):
    """
    Incremental batch-based workflow generation strategy.
    
    Builds workflows iteratively by generating 1-3 steps at a time,
    maintaining context through a sliding window mechanism that
    summarizes older steps while preserving recent step details.
    
    Attributes:
        max_steps: Maximum number of steps allowed in workflow.
        context_window_size: Number of recent steps to keep in full detail.
    
    Required Agents:
        - generator: Agent for producing workflow step batches.
    """

    def __init__(self, max_steps: int = 20, context_window_size: int = 3):
        """
        Initialize the incremental strategy with configuration.
        
        Args:
            max_steps: Maximum steps before forced termination (default: 20).
            context_window_size: Recent steps to keep in full detail (default: 3).
        """
        super().__init__()
        self.max_steps = max_steps
        self.context_window_size = context_window_size

    def _summarize_steps(self, steps: List) -> str:
        """
        Summarize older steps while preserving recent step details.
        
        Implements sliding window context management by creating compact
        summaries of older steps (beyond context_window_size) while
        maintaining full JSON representation of recent steps.
        
        Args:
            steps: List of workflow steps generated so far.
            
        Returns:
            Formatted string with summarized older steps and full
            detail for recent steps within the context window.
        """
        # All steps fit in window - return full representation
        if len(steps) <= self.context_window_size:
            return "\n".join([f"Step {i+1}: {s.model_dump_json()}" for i, s in enumerate(steps)])
        
        # Split into older (to summarize) and recent (to keep full)
        older_steps = steps[:-self.context_window_size]
        recent_steps = steps[-self.context_window_size:]
        
        # Create compact summary of older steps
        summary_parts = ["[SUMMARIZED EARLIER STEPS]"]
        for i, step in enumerate(older_steps):
            step_id = getattr(step, 'id', f'step_{i+1}')
            action = getattr(step, 'action', 'unknown')
            transitions = getattr(step, 'transitions', []) or [getattr(step, 'transition', None)]
            
            if action == "call_tool":
                # Summarize tool step with outputs and transitions
                tool_name = getattr(step, 'tool_name', 'unknown')
                if not ToolRegistry.exists(tool_name):
                    summary_parts.append(f"  Step {step_id}: Broken step! DON'T USE THIS!\n")
                    continue
                outputs = ""
                for out in ToolRegistry.get(tool_name).outputs:
                    outputs += f"{out.get("key")} ({out.get("type")}), "
                outputs = outputs.rstrip(", ")
                next_steps = ""
                for transition in transitions:
                    if transition:
                        next_steps += f"{getattr(transition, 'next_step', 'unknown')} ({getattr(transition, 'condition', 'unknown')}), "
                next_steps = next_steps.rstrip(", ")
                summary_parts.append(f"  Step {step_id}: call_tool({tool_name}) with outputs: '{outputs}'")
                if next_steps:
                    summary_parts.append(f"  Step {step_id} transitions to steps: {next_steps}\n")
            elif action == "call_llm":
                # Summarize LLM step with truncated prompt
                prompt_preview = getattr(step, 'prompt', '')[:50] + "..."
                next_steps = ""
                for transition in transitions:
                    if transition:
                        next_steps += f"{getattr(transition, 'next_step', 'unknown')} ({getattr(transition, 'condition', 'unknown')}), "
                next_steps = next_steps.rstrip(", ")
                summary_parts.append(f"  Step {step_id}: call_llm(\"{prompt_preview}\") with output: 'response'")
                if next_steps:
                    summary_parts.append(f"  Step {step_id} transitions to steps: {next_steps}\n")
            else:
                # Final step indicator
                summary_parts.append(f"  Step {step_id}: final_step")
        
        # Append full detail for recent steps
        summary_parts.append("\n[RECENT STEPS - FULL DETAIL]")
        for step in recent_steps:
            summary_parts.append(step.model_dump_json())
        
        return "\n".join(summary_parts)

    def generate(self, context, max_retries, debug):
        """
        Generate workflow incrementally in step batches.
        
        Iteratively generates 1-3 steps at a time, maintaining context
        through sliding window summarization until the workflow is
        complete or max_steps is reached.
        
        Args:
            context: Orchestrator context containing prompt, agents,
                tools, and response model specification.
            max_retries: Maximum retry attempts for LLM API calls.
            debug: Whether to enable debug output.
            
        Returns:
            Complete workflow model assembled from generated steps.
            
        Raises:
            ValueError: If generator agent is not configured.
            ValueError: If response structure is invalid.
        """
        agents = context.agents
        user_prompt = context.prompt
        available_tools = context.available_tools
        response_model = context.response_model

        if debug:
            print("Generating workflow with IncrementalStrategy...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        # Validate generator agent is configured
        if not agents.generator:
            raise ValueError("Generator agent not found.")
        
        # Initialize empty workflow state
        steps = []
        step_counter = 1
        
        # Load and prepare incremental generation prompt
        system_prompt = PromptUtils.get_system_prompt("incremental_generation")
        system_prompt_with_tools = PromptUtils.inject(system_prompt, ToolRegistry.to_prompt_format(tools=available_tools))
        
        # Select batch response model based on target workflow type
        next_step_response_model = NextLinearStepBatch if response_model.__name__ == "LinearWorkflow" else NextStructuredStepBatch
        
        # Prepare initial generation message
        next_message = f"""User Request: {user_prompt} \n\n Current Workflow State: Empty (no steps yet)"""

        # === Incremental Generation Loop ===
        while step_counter <= self.max_steps:
            
            # Generate next batch of steps
            response = agents.generator.generate_structured_content(system_prompt_with_tools, next_message, next_step_response_model, max_retries=max_retries)
            
            # Validate response structure
            try:
                parsed_response = next_step_response_model.model_validate(response)
            except Exception as e:
                raise ValueError(f"Invalid response structure at step {step_counter}: {e}")

            generated_steps_count = len(parsed_response.steps)

            if debug:
                print(f"\nGenerated {generated_steps_count} step(s)")
                print(f"  Reasoning: {parsed_response.reasoning}")
                for step in parsed_response.steps:
                    print(f"  Step: {step.model_dump_json(indent=2)}")
                print(f"  Is complete: {parsed_response.is_complete}")
                input("Press Enter to continue or Ctrl+C to exit...")
            
            # Accumulate generated steps
            steps.extend(parsed_response.steps)
            
            # Check for workflow completion
            if parsed_response.is_complete:
                
                if debug:
                    print(f"Workflow has been completed in {len(steps)} steps. Returning final workflow object.")

                # Extract workflow metadata from final step
                title = "N/A"
                description = "N/A"
                target_objective = user_prompt
                metadata = None

                for step in reversed(steps):
                    if hasattr(step, 'is_final') and step.is_final:
                        title = step.workflow_title
                        description = step.workflow_description
                        target_objective = step.target_objective
                        metadata = step.metadata
                        break
                
                # Sanitize final steps by removing embedded metadata
                for step in steps:
                    if hasattr(step, 'is_final') and step.is_final:
                        del step.workflow_title
                        del step.workflow_description
                        del step.target_objective
                        del step.metadata

                # Assemble and return complete workflow
                return response_model(
                    title=title,
                    description=description,
                    target_objective=target_objective,
                    metadata=metadata,
                    steps=steps
                )
            
            # Prepare next iteration with sliding window context
            step_counter += generated_steps_count
            workflow_state = self._summarize_steps(steps)
            next_message = f"User Request: {user_prompt} \n\n Current Workflow State:\n{workflow_state}"