from models.responses.message_response import MessageResponse
from features.base import FeatureBase
from tools.registry import ToolRegistry 
from utils.prompt import PromptUtils

class ChatClarificationFeature(FeatureBase):
    """Enhancement feature for chat clarification."""

    def __init__(self):
        self._phase = "pre"
        super().__init__()

    def apply(self, context, max_retries, debug):

        agents = context.agents
        user_prompt = context.prompt
        available_tools = context.available_tools

        if debug:
            print("Chatting with user...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        chat_prompt = PromptUtils.get_system_prompt("chat_clarification")
        chat_prompt_with_tools = PromptUtils.inject(chat_prompt, ToolRegistry.to_prompt_format(tools=available_tools))

        if not agents.chatter:
            raise ValueError("Chatter agent not found.")

        chat_session = agents.chatter.init_structured_chat(chat_prompt_with_tools, MessageResponse)
        next_message = user_prompt

        while True:
            
            response = chat_session.send_message(next_message, max_retries=max_retries)

            try:
                message_response = MessageResponse.model_validate(response)
            except Exception as e:
                raise ValueError(f"Invalid message response format: {e}")
            
            if hasattr(message_response.result, "end_clarifications") and message_response.result.end_clarifications:
                break
            
            if hasattr(message_response.result, "message") and message_response.result.message:
                print(f"\nLLM: {message_response.result.message}\n")
            else:
                print("\nLLM did not provide a message.\n")
            
            next_message = input("User: ")
        
        messages = chat_session.get_history()

        history = ""
        for msg in messages[2:]:  # Skip system prompt and first user message
            if msg.role == "assistant":
                struct_msg = MessageResponse.model_validate_json(msg.parts[0].text)
                if hasattr(struct_msg.result, "message") and struct_msg.result.message:
                    history += f"{msg.role.capitalize()}: {struct_msg.result.message}\n"
            else:
                history += f"{msg.role.capitalize()}: {msg.parts[0].text}\n"
        
        context.prompt = PromptUtils.inject(user_prompt, history=history)

        return context