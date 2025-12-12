from agents.google import GeminiAgent, GeminiModel
from models.linear_workflow import LinearWorkflow
from models.response import Response
from utils.workflow import WorkflowUtils
from utils.prompt import PromptUtils
from tools.registry import ToolRegistry

# Initialize the agent
gemini = GeminiAgent(model_name=GeminiModel.GEMINI_2_5_FLASH_LITE)

# Set up the prompts
system_prompt = PromptUtils.get_system_prompt("workflow_generation")
system_prompt_with_tools = PromptUtils.inject(system_prompt, ToolRegistry.to_prompt_format())
user_prompt = PromptUtils.get_user_prompt("weather_activity_plan")
executor_system_prompt = PromptUtils.get_system_prompt("workflow_executor")

# Generate the workflow (one-shot)
workflow = gemini.generate_workflow(system_prompt_with_tools, user_prompt, response_model=LinearWorkflow, debug=True)
WorkflowUtils.show(workflow)

# Save the workflow and its visualization
json_path = WorkflowUtils.save_json(workflow)
html_path = WorkflowUtils.save_html(workflow)

# Execute the workflow 
# workflow = WorkflowUtils.load_json(json_path, LinearWorkflow)
gemini.execute_workflow(executor_system_prompt, workflow, response_model=Response, debug=True)