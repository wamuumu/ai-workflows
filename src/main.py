import json

from agents.google import GeminiAgent
from workflows.models.linear import LinearWorkflow
# from workflows.core import WorkflowManager
from utils.constants import LINEAR_SYSTEM_PROMPT, USER_PROMPT
from tools.registry import ToolRegistry

print(ToolRegistry.list_tools())
print(ToolRegistry.get("calculator").run(expression="2 + 2 * 2"))
exit(0)

agent = GeminiAgent(tools=MACRO_TOOLS)
workflow = agent.generate(LINEAR_SYSTEM_PROMPT, USER_PROMPT, response_model=LinearWorkflow, debug=True)

print("\nGenerated Workflow:")
print(json.dumps(workflow.model_dump(), indent=2))

manager = WorkflowManager(tools=MACRO_TOOLS)
manager.generate_html(workflow)
outputs = manager.execute(workflow, debug=True)

print("\nWorkflow Outputs:")
print(json.dumps(outputs, indent=2))