from pydantic import BaseModel, Field, model_validator
from typing import List, Union, Literal, Optional

class Parameter(BaseModel):
    """An object representing a parameter item in a workflow step."""
    key: str = Field(..., description="The parameter key")
    value: Union[str, int, float, bool] = Field(..., description="The parameter value")
    from_step: Optional[str] = Field(None, description="Reference to a previous step's output")

class Transition(BaseModel):
    """A single transition in a structured workflow."""
    condition: str = Field(..., description="Condition for this transition")
    next_step: str = Field(..., description="The step ID to transition to")

class Step(BaseModel):
    """A single step in a structured workflow."""
    id: str = Field(..., description="Unique identifier for the step")
    title: str = Field(..., description="Title of the step")
    description: str = Field(..., description="Description of the step")
    action: Literal["call_tool", "call_llm"] = Field(..., description="The action type for this step")
    tool_name: Optional[str] = Field(None, description="Name of the tool to call, ONLY if action is 'call_tool'")
    parameters: Optional[List[Parameter]] = Field(None, description="Parameters for the tool or LLM")
    transitions: Optional[List[Transition]] = Field(None, description="Transitions for the steps")
    is_final: bool = Field(False, description="Indicates if this is the final step in the workflow")
    thoughts: str = Field(..., description="The agent's thoughts or reasoning for this step")

    @model_validator(mode="after")
    def validate_step(self):
        if self.is_final and self.transitions:
            raise ValueError("Final steps cannot have transitions.")
        elif self.action == "call_tool" and not self.tool_name:
            raise ValueError("tool_name must be provided when action is 'call_tool'")
        elif self.action == "call_llm" and self.tool_name is not None:
            raise ValueError("tool_name must be None when action is 'call_llm'")
        return self

class StructuredWorkflow(BaseModel):
    """A structured workflow consisting of a sequence of steps and allowing branching."""
    title: str = Field(..., description="Title of the structured workflow")
    description: str = Field(..., description="Description of the structured workflow")
    steps: List[Step] = Field(..., description="List of steps in the structured workflow")