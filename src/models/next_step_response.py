from pydantic import BaseModel, Field
from typing import Union
from models.structured_workflow import ToolStep, LLMStep, FinalStep

class NextStepResponse(BaseModel):
    step: Union[ToolStep, LLMStep, FinalStep] = Field(..., description="The next step to add to the workflow")
    is_complete: bool = Field(..., description="Whether the workflow is complete after adding this step")
    reasoning: str = Field(..., description="Explanation for why this step is needed")