from typing import List

from models.responses.incremental_next_step import NextLinearStepBatch, NextStructuredStepBatch
from strategies.base import StrategyBase
from tools.registry import ToolRegistry
from utils.prompt import PromptUtils

class IncrementalStrategy(StrategyBase):
    """Incremental construction strategy that builds workflows in batches of 1-3 steps.
    
    Optimizations:
    - Batch generation: Generates 1-3 steps per LLM call to reduce API calls
    - Sliding window context: Only keeps last K steps in full detail, summarizes older steps
    """

    def __init__(self, max_steps: int = 20, context_window_size: int = 6):
        super().__init__()
        self.max_steps = max_steps
        self.context_window_size = context_window_size  # Number of recent steps to keep in full detail (2 batches)

    def _summarize_steps(self, steps: List) -> str:
        """Summarize older steps to reduce context size while preserving key information."""
        
        if len(steps) <= self.context_window_size:
            # All steps fit in window, return full representation
            return "\n".join([f"Step {i+1}: {s.model_dump_json()}" for i, s in enumerate(steps)])
        
        # Split into older (to summarize) and recent (to keep full)
        older_steps = steps[:-self.context_window_size]
        recent_steps = steps[-self.context_window_size:]
        
        # Create compact summary of older steps
        summary_parts = ["[SUMMARIZED EARLIER STEPS]"]
        for i, step in enumerate(older_steps):
            step_id = getattr(step, 'id', f'step_{i+1}')
            action = getattr(step, 'action', 'unknown')
            if action == "call_tool":
                tool_name = getattr(step, 'tool_name', 'unknown')
                outputs = ", ".join([key for key in ToolRegistry.get(tool_name).outputs])
                summary_parts.append(f"  {step_id}: call_tool({tool_name}) producing outputs: '{outputs}'")
            elif action == "call_llm":
                prompt_preview = getattr(step, 'prompt', '')[:50] + "..."
                summary_parts.append(f"  {step_id}: call_llm(\"{prompt_preview}\") producing output: 'response'")
            else:
                summary_parts.append(f"  {step_id}: final_step")
        
        summary_parts.append("\n[RECENT STEPS - FULL DETAIL]")
        for step in recent_steps:
            summary_parts.append(step.model_dump_json())
        
        return "\n".join(summary_parts)

    def generate(self, context, max_retries, debug):
        
        agents = context.agents
        user_prompt = context.prompt
        available_tools = context.available_tools
        response_model = context.response_model

        if debug:
            print("Generating workflow with IncrementalStrategy...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        if not agents.generator:
            raise ValueError("Generator agent not found.")
        
        # Initialize empty workflow
        steps = []
        step_counter = 1
        
        # System prompt for incremental generation
        system_prompt = PromptUtils.get_system_prompt("incremental_generation")
        system_prompt_with_tools = PromptUtils.inject(system_prompt, ToolRegistry.to_prompt_format(tools=available_tools))
        
        next_step_response_model = NextLinearStepBatch if response_model.__name__ == "LinearWorkflow" else NextStructuredStepBatch
        
        # Initial message
        next_message = f"""User Request: {user_prompt} \n\n Current Workflow State: Empty (no steps yet)"""

        # Incrementally build workflow
        while step_counter <= self.max_steps:
            
            # Generate next step(s)
            response = agents.generator.generate_structured_content(system_prompt_with_tools, next_message, next_step_response_model, max_retries=max_retries)
            
            try:
                # Validate response structure
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
            
            # Add step to workflow
            steps.extend(parsed_response.steps)
            
            # Check if workflow is complete
            if parsed_response.is_complete:
                
                if debug:
                    print(f"Workflow has been completed in {len(steps)} steps. Returning final workflow object.")

                # Take the last FinalStep generated and extract workflow metadata
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
                
                # Sanitize final steps by removing metadata
                for step in steps:
                    if hasattr(step, 'is_final') and step.is_final:
                        del step.workflow_title
                        del step.workflow_description
                        del step.target_objective
                        del step.metadata

                return response_model(
                    title=title,
                    description=description,
                    target_objective=target_objective,
                    metadata=metadata,
                    steps=steps
                )
            
            # Prepare next message with sliding window context
            step_counter += generated_steps_count
            workflow_state = self._summarize_steps(steps)
            next_message = f"User Request: {user_prompt} \n\n Current Workflow State:\n{workflow_state}"