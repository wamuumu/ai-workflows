from pydantic import BaseModel
from typing import List, Union, Literal, Optional

class Parameter(BaseModel):
    """An object representing a parameter item in a workflow step."""
    key: str
    description: str
    value: Union[str, int, float, bool]

class Result(BaseModel):
    """An object representing a result item in a workflow step."""
    key: str
    description: str

class ToolAction(BaseModel):
    """An action to call a tool."""
    action: Literal["call_tool"]
    tool_name: str

class LLMAction(BaseModel):
    """An action to call a LLM."""
    action: Literal["call_llm"]

class Step(BaseModel):
    """A single step in a linear workflow."""
    id: str
    task: Union[ToolAction, LLMAction]
    parameters: Optional[List[Parameter]] = None
    results: List[Result]
    thoughts: str

class LinearWorkflow(BaseModel):
    """A linear workflow consisting of a sequence of steps."""
    title: str
    description: str
    steps: List[Step]