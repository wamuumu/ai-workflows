import json

from agents.google import GeminiAgent
from workflows.models.linear import LinearWorkflow
from workflows.core import WorkflowManager
from tools.macro import MACRO_TOOLS
from utils.constants import LINEAR_SYSTEM_PROMPT, USER_PROMPT

agent = GeminiAgent(tools=MACRO_TOOLS)
workflow = agent.generate(LINEAR_SYSTEM_PROMPT, USER_PROMPT, response_model=LinearWorkflow, debug=True)

print("\nGenerated Workflow:")
print(json.dumps(workflow.model_dump(), indent=2))

manager = WorkflowManager(tools=MACRO_TOOLS)
manager.generate_html(workflow)
outputs = manager.execute(workflow, debug=True)

print("\nWorkflow Outputs:")
print(json.dumps(outputs, indent=2))