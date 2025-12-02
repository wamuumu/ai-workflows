import os
import getpass

from google.genai import Client, types
from dotenv import load_dotenv
from pydantic import BaseModel

# Load API key from environment or prompt user
load_dotenv()

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")

class GeminiAgent:
    def __init__(self, model_name: str = "gemini-2.5-flash", tools: list = []):
        self.client = Client()
        self.model_name = model_name
        self.tools = [tool() for tool in tools]
    
    def generate(self, system_prompt: str, user_prompt: str, response_model: BaseModel, debug: bool = False) -> BaseModel:
        """Generate content using the Gemini model with structured response."""

        if self.tools:
            tool_descriptions = "\n".join([repr(tool) for tool in self.tools])
            system_prompt += f"\nAvailable tools: \n{tool_descriptions}\n"
        
        if debug:
            print("System Prompt:", system_prompt)
            print("User Prompt:", user_prompt)
            exit = input("Continue? (y/n): ")
            if exit.lower() != 'y':
                raise KeyboardInterrupt("Execution stopped by user.")

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
        