from pydantic import BaseModel
from typing import List, Union

class StepObject(BaseModel):
    """Input for a single step in a linear workflow."""
    key: str
    value: Union[str, int, float, bool]

class Steps(BaseModel):
    """A single step in a linear workflow."""
    id: str
    action: str
    inputs: List[StepObject]

class LinearWorkflow(BaseModel):
    """A linear workflow consisting of a sequence of steps."""
    steps: List[Steps]