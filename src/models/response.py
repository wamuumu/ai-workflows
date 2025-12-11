from pydantic import BaseModel
from typing import List, Union, Literal, Optional

class StepObject(BaseModel):
    """An object representing a key-value pair in tool parameters or results."""
    key: str
    value: Union[str, int, float, bool]

class ToolAction(BaseModel):
    """An action to call a tool."""
    action: Literal["call_tool"]
    tool_name: str
    parameters: Optional[List[StepObject]] = None

class LLMAction(BaseModel):
    """An action to call a LLM."""
    action: Literal["call_llm"]
    results: List[StepObject]

class Response(BaseModel):
    """A response for a single step in a structured workflow."""
    step_id: str
    type: Union[ToolAction, LLMAction]
    finished: bool = False