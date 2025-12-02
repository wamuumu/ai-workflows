from pydantic import BaseModel
from typing import List, Dict, Any
from tools.base import BaseTool

class WorkflowRunner:
    """ Executor to run workflows defined by structured models."""

    step_outputs: Dict[str, Any] = {}

    def __init__(self, tools: List[BaseTool] = []):
        self.tools = [tool() for tool in tools]

    def execute(self, workflow: BaseModel, debug: bool = False) -> Dict[str, Any]:
        """Execute the workflow step by step."""
        workflow_json = workflow.model_dump()
        
        # APPROACH 1: LLM takes the entire workflow and decides what do to do at each step
        # - LLM execute the workflow, but it's non deterministic and may not follow the defined steps exactly.

        # APPROACH 2: We execute each step based on its defined action
        # - LLM doesn't execute the workflow, but it's more deterministic and follows the defined steps exactly.
        # - LLM is called only when action is "call_llm"

        for step in workflow_json["steps"]:
            action = step["action"]

            if action == "call_llm":
                raise NotImplementedError("LLM call action is not implemented in this runner.")
            elif action == "call_tool":
                tool_name = step.get("tool_name")
                tool = next((t for t in self.tools if t.name == tool_name), None)

                if not tool:
                    raise ValueError(f"Tool {tool_name} not found among available tools.")
                
                # TODO: Resolve inputs that reference previous step outputs
                inputs = {}
                for param in step["params"]:
                    inputs[param["key"]] = param["value"]

                results = tool.run(**inputs)
                self.step_outputs[step["id"]] = results
            else:
                raise ValueError(f"Unknown action {action} in step {step['id']}.")
        
        return self.step_outputs