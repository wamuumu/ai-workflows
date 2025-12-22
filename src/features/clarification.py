from features.base import FeatureBase
from tools.registry import ToolRegistry 
from utils.prompt import PromptUtils

class ChatClarificationFeature(FeatureBase):
    """Enhancement feature for chat clarification."""

    _phase = "pre"

    def apply(self, context, debug):

        agents = context.agents
        user_prompt = context.prompt

        if debug:
            print("Chatting with user...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        chat_prompt = PromptUtils.get_system_prompt("chat_clarification")
        chat_prompt_with_tools = PromptUtils.inject(chat_prompt, ToolRegistry.to_prompt_format())

        if not agents.chatter:
            raise ValueError("Chatter agent not found.")

        chat_session = agents.chatter.init_chat(chat_prompt_with_tools)
        next_message = user_prompt

        while True:
            try:
                response = chat_session.send_message(next_message)
            except Exception as e:
                raise RuntimeError(f"Chat message failed: {e}")
            
            print(f"\nLLM: {response}\n")

            if "END_CLARIFICATIONS" in response.upper().strip():
                break
            else:
                next_message = input("User: ")
        
        messages = chat_session.get_history()
        history = "\n".join([f"{msg.role.capitalize()}: {msg.parts[0].text}" for msg in messages[1:]])  # Skip chat system prompt

        system_prompt = PromptUtils.get_system_prompt("workflow_generation")
        system_prompt_with_tools = PromptUtils.inject(system_prompt, ToolRegistry.to_prompt_format(), chat_history=history)
        
        context.prompt = system_prompt_with_tools

        return context