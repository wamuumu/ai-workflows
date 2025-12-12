from agents.google import GeminiAgent, GeminiModel
from models.linear_workflow import LinearWorkflow
from models.response import Response
from workflows.utils import WorkflowUtils
from utils.prompts import SYSTEM_PROMPT, EXECUTOR_SYSTEM_PROMPT, USER_PROMPTS
from tools.registry import ToolRegistry

# Initialize the agent
gemini = GeminiAgent(model_name=GeminiModel.GEMINI_2_5_FLASH_LITE)

# Set up the prompts
system_prompt_with_tools = f"{SYSTEM_PROMPT}\n{ToolRegistry.to_prompt_format()}\n"
user_prompt = USER_PROMPTS[0]

# Generate the workflow (one-shot)
workflow = gemini.generate_workflow(system_prompt_with_tools, user_prompt, response_model=LinearWorkflow, debug=True)

WorkflowUtils.show(workflow)

# Save the workflow and its visualization
json_path = WorkflowUtils.save_json(workflow)
html_path = WorkflowUtils.save_html(workflow)

# Execute the workflow 
# workflow = WorkflowUtils.load_json(json_path, LinearWorkflow)
gemini.execute_workflow(EXECUTOR_SYSTEM_PROMPT, workflow, response_model=Response, debug=True)