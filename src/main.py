import json

from agents.google import GeminiAgent
from workflows.models.linear import LinearWorkflow
# from workflows.core import WorkflowManager
from utils.prompts import SYSTEM_PROMPT, CHAT_SYSTEM_PROMPT, USER_PROMPTS
from tools.registry import ToolRegistry

# Initialize Gemini Agent
agent = GeminiAgent()

# Set up the prompts
system_prompt_with_tools = f"{SYSTEM_PROMPT}\n{ToolRegistry.to_prompt_format()}\n"
chat_prompt_with_tools = f"{CHAT_SYSTEM_PROMPT}\n{ToolRegistry.to_prompt_format()}\n"
user_prompt = USER_PROMPTS[0]

# Generate the workflow (one-shot)
# workflow = agent.generate(system_prompt_with_tools, user_prompt, response_model=LinearWorkflow, debug=True)

# Generate the workflow (chat-based with clarification)
workflow = agent.chat(SYSTEM_PROMPT, chat_prompt_with_tools, user_prompt, response_model=LinearWorkflow, debug=True)

print("\nGenerated Workflow:")
print(json.dumps(workflow.model_dump(), indent=2))
exit(0)

manager = WorkflowManager(tools=MACRO_TOOLS)
manager.generate_html(workflow)
outputs = manager.execute(workflow, debug=True)

print("\nWorkflow Outputs:")
print(json.dumps(outputs, indent=2))