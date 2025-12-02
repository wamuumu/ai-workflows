import json

from agents.google import GeminiAgent
from workflows.models.linear import LinearWorkflow
from workflows.runner import WorkflowRunner
from tools.macro import MACRO_TOOLS
from utils.constants import SYSTEM_PROMPT, USER_PROMPT

agent = GeminiAgent(tools=MACRO_TOOLS)
workflow = agent.generate(SYSTEM_PROMPT, USER_PROMPT, response_model=LinearWorkflow, debug=True)

print("\nGenerated Workflow:")
print(json.dumps(workflow.model_dump(), indent=2))

runner = WorkflowRunner(tools=MACRO_TOOLS)
outputs = runner.execute(workflow)

print("\nWorkflow Outputs:")
print(json.dumps(outputs, indent=2))