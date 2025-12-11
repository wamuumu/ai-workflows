from pydantic import BaseModel
from typing import List, Union, Literal

class Parameter(BaseModel):
    """An object representing a parameter item in a workflow step."""
    key: str
    value: Union[str, int, float, bool]

class ToolAction(BaseModel):
    """An action to call a tool."""
    action: Literal["call_tool"]
    tool_name: str
    parameters: List[Parameter]

class LLMAction(BaseModel):
    """An action to call a LLM."""
    action: Literal["call_llm"]
    description: str
    parameters: List[Parameter]

class Step(BaseModel):
    """A single step in a linear workflow."""
    id: str
    task: Union[ToolAction, LLMAction]
    thoughts: str

class LinearWorkflow(BaseModel):
    """A linear workflow consisting of a sequence of steps."""
    title: str
    description: str
    steps: List[Step]