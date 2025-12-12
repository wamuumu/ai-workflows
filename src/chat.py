from agents.cerebras import CerebrasAgent, CerebrasModel
from models.structured_workflow import StructuredWorkflow
from models.response import Response
from utils.workflow import WorkflowUtils
from utils.prompt import PromptUtils
from tools.registry import ToolRegistry

# Initialize the agent
cerebras = CerebrasAgent(model_name=CerebrasModel.GPT_OSS)

# Set up the prompts
chat_prompt = PromptUtils.get_system_prompt("chat_clarification")
chat_prompt_with_tools = PromptUtils.inject(chat_prompt, ToolRegistry.to_prompt_format())
user_prompt = PromptUtils.get_user_prompt("weather_activity_plan")
executor_system_prompt = PromptUtils.get_system_prompt("workflow_executor")

# Generate the workflow (chat-based with clarification)
chat_history = cerebras.chat(chat_prompt_with_tools, user_prompt, debug=False)
workflow = cerebras.generate_workflow_from_chat(chat_history, chat_prompt, response_model=StructuredWorkflow, debug=False)
WorkflowUtils.show(workflow)

# Save the workflow and its visualization
json_path = WorkflowUtils.save_json(workflow)
html_path = WorkflowUtils.save_html(workflow)

# Execute the workflow
# workflow = WorkflowUtils.load_json(json_path, StructuredWorkflow)
cerebras.execute_workflow(executor_system_prompt, workflow, response_model=Response, debug=True)