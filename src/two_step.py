from agents.cerebras import CerebrasAgent, CerebrasModel
from agents.google import GeminiAgent, GeminiModel
from models.structured_workflow import StructuredWorkflow
from models.response import Response
from utils.workflow import WorkflowUtils
from utils.prompt import PromptUtils
from tools.registry import ToolRegistry

# Initialize the agent
gemini = GeminiAgent(model_name=GeminiModel.GEMINI_2_5_FLASH_LITE)  # Planner
gpt_oss = CerebrasAgent(model_name=CerebrasModel.GPT_OSS) # Refiner
llama = CerebrasAgent(model_name=CerebrasModel.GPT_OSS) # Executor

# Set up the prompts
system_prompt = PromptUtils.get_system_prompt("workflow_generation")
system_prompt_with_tools = PromptUtils.inject(system_prompt, ToolRegistry.to_prompt_format())
refinement_prompt = PromptUtils.get_system_prompt("workflow_refinement")
user_prompt = PromptUtils.get_user_prompt("weather_activity_plan")
refinement_prompt_with_tools = PromptUtils.inject(refinement_prompt, ToolRegistry.to_prompt_format(), original_prompt=user_prompt)
executor_system_prompt = PromptUtils.get_system_prompt("workflow_executor")

# Generate the workflow (first draft)
workflow = gemini.generate_workflow(system_prompt_with_tools, user_prompt, response_model=StructuredWorkflow, debug=False)
WorkflowUtils.show(workflow)
json_path = WorkflowUtils.save_json(workflow)
html_path = WorkflowUtils.save_html(workflow)

# Second pass to refine the workflow
workflow = gpt_oss.generate_workflow_from_workflow(refinement_prompt_with_tools, workflow, response_model=StructuredWorkflow, debug=True)
WorkflowUtils.show(workflow)
json_path = WorkflowUtils.save_json(workflow)
html_path = WorkflowUtils.save_html(workflow)

# Execute the workflow
# workflow = WorkflowUtils.load_json(json_path, StructuredWorkflow)
llama.execute_workflow(executor_system_prompt, workflow, response_model=Response, debug=True)