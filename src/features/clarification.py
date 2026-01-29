"""
Chat Clarification Feature
==========================

This module implements the ChatClarificationFeature, a pre-generation
enhancement that enables interactive clarification of ambiguous user prompts
through a chat-based dialogue.

Main Responsibilities:
    - Initialize structured chat session with clarification prompt
    - Manage multi-turn dialogue to gather missing information
    - Augment original prompt with clarification history

Key Dependencies:
    - models.responses.message_response: For structured clarification schema
    - features.base: For FeatureBase interface
    - tools.registry: For tool information injection
    - utils.prompt: For prompt template loading

Use Cases:
    - User prompts with missing required information
    - Ambiguous specifications needing disambiguation
    - Complex workflows requiring detailed requirements gathering
"""

from models.responses.message_response import MessageResponse
from features.base import FeatureBase
from tools.registry import ToolRegistry 
from utils.prompt import PromptUtils


class ChatClarificationFeature(FeatureBase):
    """
    Pre-generation feature for interactive prompt clarification.
    
    Engages the user in a dialogue to gather missing information before
    workflow generation begins. The clarification history is appended to
    the original prompt for context.
    
    Attributes:
        _phase: Set to "pre" for pre-generation execution.
    
    Required Agents:
        - chatter: Agent for conducting the clarification dialogue.
    """

    def __init__(self):
        """Initialize the feature with pre-generation phase."""
        self._phase = "pre"
        super().__init__()

    def apply(self, context, max_retries, debug):
        """
        Conduct interactive clarification dialogue with the user.
        
        Opens a chat session with the chatter agent and iteratively asks
        clarifying questions until sufficient information is gathered.
        The conversation history is then appended to the original prompt.
        
        Args:
            context: Orchestrator context containing agents and prompt.
            max_retries: Maximum retry attempts for LLM calls.
            debug: Whether to enable debug output.
            
        Returns:
            Modified context with augmented prompt.
            
        Raises:
            ValueError: If chatter agent is not configured.
            ValueError: If response validation fails.
        """
        agents = context.agents
        user_prompt = context.prompt
        available_tools = context.available_tools

        if debug:
            print("Chatting with user...")
            print("User Prompt:", user_prompt)
            input("Press Enter to continue or Ctrl+C to exit...")

        # Load and prepare clarification system prompt with tool context
        chat_prompt = PromptUtils.get_system_prompt("chat_clarification")
        chat_prompt_with_tools = PromptUtils.inject(chat_prompt, ToolRegistry.to_prompt_format(tools=available_tools))

        if not agents.chatter:
            raise ValueError("Chatter agent not found.")

        # Initialize structured chat session for type-safe responses
        chat_session = agents.chatter.init_structured_chat(chat_prompt_with_tools, MessageResponse)
        next_message = user_prompt

        # Clarification dialogue loop
        while True:
            
            response = chat_session.send_message(next_message, max_retries=max_retries)

            try:
                message_response = MessageResponse.model_validate(response)
            except Exception as e:
                raise ValueError(f"Invalid message response format: {e}")
            
            # Check for clarification completion signal
            if hasattr(message_response.result, "end_clarifications") and message_response.result.end_clarifications:
                break
            
            # Display agent's clarification question
            if hasattr(message_response.result, "message") and message_response.result.message:
                print(f"\nLLM: {message_response.result.message}\n")
            else:
                print("\nLLM did not provide a message.\n")
            
            # Get user's response
            next_message = input("User: ")
        
        # Build clarification history for prompt augmentation
        messages = chat_session.get_history()

        history = ""
        # Skip system prompt and initial user message (indices 0-1)
        for msg in messages[2:]:
            if msg.role == "assistant":
                # Parse structured responses to extract message text
                struct_msg = MessageResponse.model_validate_json(msg.parts[0].text)
                if hasattr(struct_msg.result, "message") and struct_msg.result.message:
                    history += f"{msg.role.capitalize()}: {struct_msg.result.message}\n"
            else:
                history += f"{msg.role.capitalize()}: {msg.parts[0].text}\n"
        
        # Augment original prompt with clarification context
        context.prompt = PromptUtils.inject(user_prompt, history=history)

        return context