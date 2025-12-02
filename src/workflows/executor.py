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
        
        for step in workflow_json["steps"]:
            action = step["action"]
            tool = next((t for t in self.tools if t.name == action), None)

            if not tool:
                raise ValueError(f"Tool {action} not found among available tools.")
            
            inputs = {}
            for param in step["inputs"]:
                key = param["key"]
                value = param["value"]
                if isinstance(value, str) and ".output" in value:
                    ref_step_id = value.split(".")[0]
                    inputs[key] = self.step_outputs[ref_step_id]
                else:
                    inputs[key] = value
            
            result = tool.run(**inputs)
            self.step_outputs[step["id"]] = result

            if debug:
                print(f"Executed step {step['id']} using tool {action}, result: {result}")
        
        return self.step_outputs