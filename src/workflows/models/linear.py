from pydantic import BaseModel
from typing import List, Union, Literal, Optional

class StepObject(BaseModel):
    """Input for a single step in a linear workflow."""
    key: str
    value: Union[str, int, float, bool]

class Steps(BaseModel):
    """A single step in a linear workflow."""
    id: str
    action: Literal["call_tool", "call_llm"]
    tool_name: Optional[str] = None
    params: Optional[List[StepObject]] = None
    thoughts: str

class LinearWorkflow(BaseModel):
    """A linear workflow consisting of a sequence of steps."""
    title: str
    description: str
    steps: List[Steps]