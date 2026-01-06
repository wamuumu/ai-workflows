from pydantic import BaseModel, Field
from typing import Union
from models.linear_workflow import ToolStep as LinearToolStep, LLMStep as LinearLLMStep, FinalStep as LinearFinalStep
from models.structured_workflow import ToolStep as StructuredToolStep, LLMStep as StructuredLLMStep, FinalStep as StructuredFinalStep

class NextLinearStep(BaseModel):
    step: Union[LinearToolStep, LinearLLMStep, LinearFinalStep] = Field(..., description="The next step to add to the linear workflow")
    is_complete: bool = Field(..., description="Whether the linear workflow is complete after adding this step")
    reasoning: str = Field(..., description="Explanation for why this step is needed")

class NextStructuredStep(BaseModel):
    step: Union[StructuredToolStep, StructuredLLMStep, StructuredFinalStep] = Field(..., description="The next step to add to the workflow")
    is_complete: bool = Field(..., description="Whether the workflow is complete after adding this step")
    reasoning: str = Field(..., description="Explanation for why this step is needed")