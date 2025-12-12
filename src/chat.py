from agents.cerebras import CerebrasAgent, CerebrasModel
from models.structured_workflow import StructuredWorkflow
from models.response import Response
from workflows.utils import WorkflowUtils
from utils.prompts import SYSTEM_PROMPT, CHAT_SYSTEM_PROMPT, EXECUTOR_SYSTEM_PROMPT, USER_PROMPTS
from tools.registry import ToolRegistry

# Initialize the agent
cerebras = CerebrasAgent(model_name=CerebrasModel.GPT_OSS)

# Set up the prompts
chat_prompt_with_tools = f"{CHAT_SYSTEM_PROMPT}\n{ToolRegistry.to_prompt_format()}\n"
user_prompt = USER_PROMPTS[0]

# Generate the workflow (chat-based with clarification)
chat_history = cerebras.chat(chat_prompt_with_tools, user_prompt, debug=False)
workflow = cerebras.generate_workflow_from_chat(chat_history, SYSTEM_PROMPT, response_model=StructuredWorkflow, debug=False)

print("\nGenerated Workflow:")
print(workflow.model_dump_json(indent=2))

# Generate HTML visualization
wf_utils = WorkflowUtils(tools=ToolRegistry.get_all())
wf_utils.generate_html(workflow)    

# Execute the workflow
cerebras.execute_workflow(EXECUTOR_SYSTEM_PROMPT, workflow, response_model=Response, debug=True)