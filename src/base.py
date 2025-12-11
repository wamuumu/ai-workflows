from agents.google import GeminiAgent
from models.structured_workflow import StructuredWorkflow
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
print(workflow.model_dump_json(indent=2))

# Generate HTML visualization
wf_utils = WorkflowUtils(tools=ToolRegistry.get_all())
wf_utils.generate_html(workflow)