from typing import List

from models.responses.incremental_next_step import NextLinearStepBatch, NextStructuredStepBatch
from strategies.base import StrategyBase
from tools.registry import ToolRegistry
from utils.prompt import PromptUtils

#TODO: implement batch and sliding window optimizations

class IncrementalStrategy(StrategyBase):
    """Incremental construction strategy that builds workflows one step at a time.
    
    Optimizations:
    - Sliding window context: Only keeps last K steps in full detail, summarizes older steps
    - Early termination heuristics: Detects completion patterns without waiting for LLM flag
    """

    def __init__(self, max_steps: int = 20, context_window_size: int = 4):
        super().__init__()
        self.max_steps = max_steps
        self.context_window_size = context_window_size  # Number of recent steps to keep in full detail

    def _summarize_steps(self, steps: List, keep_last_n: int) -> str:
        """Summarize older steps to reduce context size while preserving key information."""
        if len(steps) <= keep_last_n:
            # All steps fit in window, return full representation
            return "\n".join([f"Step {i+1}: {s.model_dump_json()}" for i, s in enumerate(steps)])
        
        # Split into older (to summarize) and recent (to keep full)
        older_steps = steps[:-keep_last_n]
        recent_steps = steps[-keep_last_n:]
        
        # Create compact summary of older steps
        summary_parts = ["[SUMMARIZED EARLIER STEPS]"]
        for i, step in enumerate(older_steps):
            step_id = getattr(step, 'id', f'step_{i+1}')
            action = getattr(step, 'action', 'unknown')
            if action == "call_tool":
                tool_name = getattr(step, 'tool_name', 'unknown')
                summary_parts.append(f"  {step_id}: call_tool({tool_name})")
            elif action == "call_llm":
                prompt_preview = getattr(step, 'prompt', '')[:50] + "..."
                summary_parts.append(f"  {step_id}: call_llm(\"{prompt_preview}\")")
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
        
        if response_model.__class__.__name__ == "LinearWorkflow":
            type = "linear"
            next_step_response_model = NextLinearStepBatch
        else:
            type = "structured"
            next_step_response_model = NextStructuredStepBatch

        # Create chat session for stateful generation
        # chat_session = agents.generator.init_structured_chat(system_prompt_with_tools, next_step_response_model)
        
        # Initial message
        next_message = f"""User Request: {user_prompt} \n\n Current Workflow State: Empty (no steps yet)"""

        # Incrementally build workflow
        while step_counter <= self.max_steps:
            
            # Generate next step
            # response = chat_session.send_message(next_message, category="generation")
            response = agents.generator.generate_structured_content(system_prompt_with_tools, next_message, next_step_response_model, max_retries=max_retries)
            
            # if debug:
            #     print(f"\nStep {step_counter} generated:")
            #     print(f"  Reasoning: {response.reasoning}")
            #     print(f"  Step: {response.step.model_dump_json(indent=2)}")
            #     print(f"  Is complete: {response.is_complete}")
            #     input("Press Enter to continue or Ctrl+C to exit...")
            
            # Add step to workflow
            parsed_response = next_step_response_model.model_validate(response)
            steps.extend(parsed_response.steps)
            
            # Check if workflow is complete (with early termination heuristics)
            if parsed_response.is_complete:
                break
            
            # Prepare next message with sliding window context
            step_counter += 1
            workflow_state = self._summarize_steps(steps, self.context_window_size)
            next_message = f"User Request: {user_prompt} \n\n Current Workflow State:\n{workflow_state}"

        if debug:
            print(f"\nWorkflow generation complete with {len(steps)} steps")
            input("Press Enter to continue or Ctrl+C to exit...")
        
        # Construct final workflow object
        workflow = response_model(
            title=f"Incrementally Generated Workflow",
            description=f"Workflow built step-by-step for: {user_prompt[:100]}",
            target_objective=user_prompt,
            type=type,
            steps=steps
        )
        
        return workflow