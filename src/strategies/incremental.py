import time

from models.next_step_response import NextStepResponse
from strategies.base import StrategyBase
from tools.registry import ToolRegistry
from utils.prompt import PromptUtils

class IncrementalStrategy(StrategyBase):
    """Incremental construction strategy that builds workflows one step at a time."""

    def __init__(self, max_steps: int = 20):
        super().__init__()
        self.max_steps = max_steps

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
        
        # Create chat session for stateful generation
        chat_session = agents.generator.init_structured_chat(system_prompt_with_tools, NextStepResponse)
        
        # Initial message
        next_message = f"""User Request: {user_prompt} \n\n Current Workflow State: Empty (no steps yet)"""

        # Incrementally build workflow
        while step_counter <= self.max_steps:
            
            # Generate next step
            retry = 0
            while retry < max_retries:
                try:
                    response = chat_session.send_message(next_message, category="generation")
                    break
                except Exception as e:
                    rety += 1
                    retry_time = 2 ** retry
                    print(f"Step generation retry {retry}/{max_retries} after error: {e}. Retrying in {retry_time} seconds...")
                    time.sleep(retry_time)
        
            if retry == max_retries:
                raise RuntimeError("Max retries exceeded during step generation.")
            
            if debug:
                print(f"\nStep {step_counter} generated:")
                print(f"  Reasoning: {response.reasoning}")
                print(f"  Step: {response.step.model_dump_json(indent=2)}")
                print(f"  Is complete: {response.is_complete}")
                input("Press Enter to continue or Ctrl+C to exit...")
            
            # Add step to workflow
            steps.append(NextStepResponse.model_validate(response).step)
            
            # Check if workflow is complete
            if response.is_complete:
                break
            
            # Prepare next message with updated state
            step_counter += 1
            workflow_state = "\n".join([f"Step {i+1}: {step.model_dump_json()}" for i, step in enumerate(steps)])
            next_message = f"""Current Workflow State: {workflow_state} \n\n Generate the NEXT step needed. The workflow is not yet complete."""

        if debug:
            print(f"\nWorkflow generation complete with {len(steps)} steps")
            input("Press Enter to continue or Ctrl+C to exit...")
        
        # Construct final workflow object
        workflow = response_model(
            title=f"Incrementally Generated Workflow",
            description=f"Workflow built step-by-step for: {user_prompt[:100]}",
            target_objective=user_prompt,
            type="structured",
            steps=steps
        )
        
        return workflow