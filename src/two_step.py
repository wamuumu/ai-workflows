from agents.cerebras import CerebrasAgent, CerebrasModel
from agents.google import GeminiAgent, GeminiModel
from models.structured_workflow import StructuredWorkflow
from models.response import Response
from utils.workflow import WorkflowUtils
from utils.prompt import SYSTEM_PROMPT, REFINEMENT_SYSTEM_PROMPT, EXECUTOR_SYSTEM_PROMPT, USER_PROMPTS
from tools.registry import ToolRegistry

# Initialize the agent
gemini = GeminiAgent(model_name=GeminiModel.GEMINI_2_5_FLASH_LITE)  # Planner
gpt_oss = CerebrasAgent(model_name=CerebrasModel.GPT_OSS) # Refiner
llama = CerebrasAgent(model_name=CerebrasModel.GPT_OSS) # Executor

# Set up the prompts
system_prompt_with_tools = f"{SYSTEM_PROMPT}\n{ToolRegistry.to_prompt_format()}\n"
user_prompt = USER_PROMPTS[0]

# Generate the workflow (first draft)
workflow = gemini.generate_workflow(system_prompt_with_tools, user_prompt, response_model=StructuredWorkflow, debug=False)
WorkflowUtils.show(workflow)
json_path = WorkflowUtils.save_json(workflow)
html_path = WorkflowUtils.save_html(workflow)

# Second pass to refine the workflow
refinement_prompt_with_tools = f"{REFINEMENT_SYSTEM_PROMPT}\n\n{ToolRegistry.to_prompt_format()}\n\nOriginal user prompt: {user_prompt}"
workflow = gpt_oss.generate_workflow_from_workflow(refinement_prompt_with_tools, workflow, response_model=StructuredWorkflow, debug=True)
WorkflowUtils.show(workflow)
json_path = WorkflowUtils.save_json(workflow)
html_path = WorkflowUtils.save_html(workflow)

# Execute the workflow
# workflow = WorkflowUtils.load_json(json_path, StructuredWorkflow)
llama.execute_workflow(EXECUTOR_SYSTEM_PROMPT, workflow, response_model=Response, debug=True)