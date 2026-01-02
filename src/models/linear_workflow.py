from pydantic import BaseModel, Field, model_validator
from typing import List, Union, Literal, Optional

class Parameter(BaseModel):
    """An object representing a parameter item in a workflow step."""
    key: str = Field(..., description="The parameter key")
    value: Union[str, int, float, bool] = Field(..., description="The parameter value")

class Step(BaseModel):
    """A single step in a linear workflow."""
    id: str = Field(..., description="Unique identifier for the step")
    action: Literal["call_tool", "call_llm"] = Field(..., description="The action type for this step")
    tool_name: Optional[str] = Field(None, description="Name of the tool to call, ONLY if action is 'call_tool'")
    parameters: Optional[List[Parameter]] = Field(None, description="Parameters for the tool or LLM")
    is_final: bool = Field(False, description="Indicates if this is the final step in the workflow")
    thoughts: str = Field(..., description="The agent's thoughts or reasoning for this step")

    @model_validator(mode="after")
    def validate_step(self):
        if self.action == "call_tool" and not self.tool_name:
            raise ValueError("tool_name must be provided when action is 'call_tool'")
        elif self.action == "call_llm" and self.tool_name is not None:
            raise ValueError("tool_name must be None when action is 'call_llm'")
        return self

class LinearWorkflow(BaseModel):
    """A linear workflow consisting of a sequence of steps."""
    title: str = Field(..., description="Title of the linear workflow")
    description: str = Field(..., description="Description of the linear workflow")
    target_objective: str = Field(..., description="The intended objective based on the user prompt")
    steps: List[Step] = Field(..., description="List of steps in the linear workflow")