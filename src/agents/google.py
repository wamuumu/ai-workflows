import os
import getpass

from google.genai import Client, types
from pydantic import BaseModel
from dotenv import load_dotenv

# Load API key from environment or prompt user
load_dotenv()

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")

class GeminiAgent:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.client = Client()
        self.model_name = model_name
    
    def generate_workflow(self, system_prompt: str, user_prompt: str, response_model: BaseModel, debug: bool = False) -> BaseModel:
        """Generate a workflow in one-shot."""

        if debug:
            print("System Prompt:", system_prompt)
            print("User Prompt:", user_prompt)
            exit = input("Continue? (y/n): ")
            if exit.lower() != 'y':
                raise KeyboardInterrupt("Execution stopped by user.")

        return self._get_workflow(system_prompt, user_prompt, response_model)

    def chat(self, system_prompt: str, user_prompt: str, debug: bool = False):
        """Engage in a chat using the Gemini model with structured response."""

        if debug:
            print("System Prompt:", system_prompt)
            print("User Prompt:", user_prompt)
            exit = input("Continue? (y/n): ")
            if exit.lower() != 'y':
                raise KeyboardInterrupt("Execution stopped by user.")

        # Instantiate a chat session with system prompt    
        chat_session = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt
            )
        )

        # Send user prompt and get initial reasoning
        try:
            response = chat_session.send_message(f"Workflow prompt is '{user_prompt}'")
            print("Initial reasoning:", response.text)
        except Exception as e:
            raise RuntimeError(f"Chat message failed: {e}")
        
        # Iterative workflow refinement with questions and answers
        while True:
            user_input = input("Your message (type 'exit'): ")
            if user_input.lower() == 'exit':
                break

            response = chat_session.send_message(user_input)
            print(f"Response: {response.text}\n")
        
        return chat_session
    
    def generate_workflow_from_chat(self, chat_session, system_prompt: str, response_model: BaseModel, debug: bool = False) -> BaseModel:
        """Generate a workflow from the chat history."""
        
        if debug:
            print("System Prompt for final generation:", system_prompt)
            exit = input("Continue? (y/n): ")
            if exit.lower() != 'y':
                raise KeyboardInterrupt("Execution stopped by user.")

        # Compile chat history into a single prompt
        history_text = "\n".join(
            f"{msg.role.capitalize()}: {msg.parts[0].text}" for msg in chat_session.get_history()
        )
        final_prompt = f"Based on the conversation we just had, please generate the required JSON workflow. The conversation was:\n\n---\n{history_text}\n\n---"

        return self._get_workflow(system_prompt, final_prompt, response_model)
    
    def _get_workflow(self, system_prompt: str, user_prompt: str, response_model: BaseModel) -> BaseModel:
        """Private method to get the structured response (i.e, workflow schema) from the model."""
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type= 'application/json',
                response_schema=response_model
            )
        )

        try:
            workflow = response_model.model_validate_json(response.text)
        except Exception as e:
            raise ValueError(f"Failed to parse response into {response_model.__name__}: {e}")

        return workflow