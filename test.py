import json
import os, getpass

from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Dict, Any
from enum import Enum

from langchain.tools import tool
from langchain.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from a .env file
load_dotenv()

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")

# Define system prompt and user request
SYSTEM_PROMPT = """
You are a helpful workflow-definition agent.

Your task:
Given a user request, produce a JSON workflow that satisfies the request.

Rules:
- Output ONLY valid JSON matching the provided schema.
- Each step id must be in the following format: "step1", "step2", etc.
- For input values, if they use outputs from previous steps, reference them appropriately with step IDs (e.g., "step1.output").

Be precise, unambiguous, and do NOT include explanations.
"""

USER_REQUEST = "What's the weather in my city?"

# Define the tools
@tool(description="Get the current city")
def get_city() -> str:
    return "Trento, Italy"

@tool(description="Get the current weather in a given city")
def get_weather(city: str) -> str:
    # For demonstration purposes, return a static weather report
    return f"The current weather in {city} is sunny with a temperature of 25°C."

class ToolEnum(Enum):
    GET_CITY = get_city.name
    GET_WEATHER = get_weather.name

# Define the output schema
class Steps(BaseModel):
    id: str
    action: ToolEnum
    inputs: Dict[str, Any]

class Workflow(BaseModel):
    steps: List[Steps]

# Initialize the model with structured output
available_tools = [globals()[tool.value] for tool in ToolEnum]
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite").bind_tools(available_tools)
model = llm.with_structured_output(schema=Workflow.model_json_schema(), method="json_schema")

# Invoke the model with the system prompt and user request
messages = [SystemMessage(SYSTEM_PROMPT), HumanMessage(USER_REQUEST)]
workflow = model.invoke(messages)
print(json.dumps(workflow, indent=2))

# Execute steps
TOOLS_DICT = {tool.name: tool for tool in available_tools}
step_outputs = {}
for step in workflow["steps"]:
    action_name = step["action"]
    tool_obj = TOOLS_DICT[action_name]

    # Prepare inputs: replace references like "step1.output" with actual values
    inputs = {}
    for k, v in step["inputs"].items():
        if isinstance(v, str) and ".output" in v:
            ref_step_id = v.split(".")[0]
            inputs[k] = step_outputs[ref_step_id]
        else:
            inputs[k] = v

    # Execute the tool
    result = tool_obj.invoke(inputs)

    # Store output for possible references in later steps
    step_outputs[step["id"]] = result

    print(f"Step {step['id']} ({action_name}) result: {result}")