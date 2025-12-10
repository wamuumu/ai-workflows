import json

from agents.google import GeminiAgent
from models.workflow import StructuredWorkflow
from workflows.utils import WorkflowUtils
from utils.prompts import SYSTEM_PROMPT, USER_PROMPTS
from tools.registry import ToolRegistry

# Initialize the agent
gemini = GeminiAgent(model_name="gemini-2.5-flash-lite")

# Set up the prompts
system_prompt_with_tools = f"{SYSTEM_PROMPT}\n{ToolRegistry.to_prompt_format()}\n"
user_prompt = USER_PROMPTS[0]

# Generate the workflow (one-shot)
workflow = gemini.generate_workflow(system_prompt_with_tools, user_prompt, response_model=StructuredWorkflow, debug=True)

print("\nGenerated Workflow:")
print(json.dumps(workflow.model_dump(), indent=2))

wf_utils = WorkflowUtils(tools=ToolRegistry.get_all())
wf_utils.generate_html(workflow)