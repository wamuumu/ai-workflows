from strategies.base import StrategyBase
from tools.registry import ToolRegistry
from utils.prompt import PromptUtils

class IterativeStrategy(StrategyBase):
    """Iterative generation strategy where generator and discriminator agents work together to build the workflow step by step."""

    def __init__(self, max_rounds: int = 5):
        super().__init__(max_rounds=max_rounds)

    def generate(self, context, debug):
        
        if self.max_rounds < 1:
            raise ValueError("max_rounds must be a positive integer.")
        
        agents = context.agents
        user_prompt = context.prompt
        available_tools = context.available_tools
        response_model = context.response_model

        if debug:
            print("Generating workflow with IterativeStrategy...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        generation_prompt = PromptUtils.get_system_prompt("workflow_generation")
        generation_prompt_with_tools = PromptUtils.inject(generation_prompt, ToolRegistry.to_prompt_format(tools=available_tools))

        review_prompt = PromptUtils.get_system_prompt("workflow_review")
        review_prompt_with_tools = PromptUtils.inject(review_prompt, ToolRegistry.to_prompt_format(tools=available_tools), workflow_expected_schema=response_model.model_json_schema(), user_prompt=user_prompt)
        
        if not agents.generator:
            raise ValueError("Generator agent not found.")

        if not agents.discriminator:
            raise ValueError("Discriminator agent not found.")
        
        generator_chat = agents.generator.init_structured_chat(generation_prompt_with_tools, response_model)
        discriminator_chat = agents.discriminator.init_chat(review_prompt_with_tools)
        
        next_message = user_prompt
        for _ in range(self.max_rounds):
            
            workflow = generator_chat.send_message(next_message, category="generation")
            workflow_json = workflow.model_dump_json(indent=2)

            if debug:
                print("Generated Plan:", workflow)
                input("Press Enter to continue or Ctrl+C to exit...")
            
            review = discriminator_chat.send_message(workflow_json, category="generation")
            
            if debug:
                print("Discriminator Review:", review)
                input("Press Enter to continue or Ctrl+C to exit...")
            
            if "END_REVIEW" in review.upper().strip():
                break
            
            next_message = f"Please revise the workflow based on the following review:\n{review}\n"

        return workflow