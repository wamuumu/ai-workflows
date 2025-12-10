from pydantic import BaseModel
from typing import List, Union, Literal, Optional

class Parameter(BaseModel):
    """An object representing a parameter item in a workflow step."""
    key: str
    value: Union[str, int, float, bool]
    from_step: Optional[str] = None

class Result(BaseModel):
    """An object representing a result item in a workflow step."""
    key: str
    description: str

class ToolAction(BaseModel):
    """An action to call a tool."""
    action: Literal["call_tool"]
    tool_name: str
    parameters: Optional[List[Parameter]] = None

class LLMAction(BaseModel):
    """An action to call a LLM."""
    action: Literal["call_llm"]
    results: List[Result]

class StepResponse(BaseModel):
    """A response for a single step in a structured workflow."""
    step_id: str
    type: Union[ToolAction, LLMAction]
    results: Optional[dict] = None
    human_input: Optional[str] = None