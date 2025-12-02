from pydantic import BaseModel
from typing import List, Union, Literal, Optional

class StructuredWorkflow(BaseModel):
    """A linear workflow consisting of a sequence of steps."""
    title: str
    description: str
    # TODO: Implment