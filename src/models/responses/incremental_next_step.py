from pydantic import BaseModel, Field
from typing import List, Union, Optional
from models.workflows.linear_workflow import ToolStep as LinearToolStep, LLMStep as LinearLLMStep, FinalStep as LinearFinalStep
from models.workflows.structured_workflow import ToolStep as StructuredToolStep, LLMStep as StructuredLLMStep, FinalStep as StructuredFinalStep

class NextLinearStep(BaseModel):
    step: Union[LinearToolStep, LinearLLMStep, LinearFinalStep] = Field(..., description="The next step to add to the linear workflow")
    is_complete: bool = Field(..., description="Whether the linear workflow is complete after adding this step")
    reasoning: str = Field(..., description="Explanation for why this step is needed")

class NextStructuredStep(BaseModel):
    step: Union[StructuredToolStep, StructuredLLMStep, StructuredFinalStep] = Field(..., description="The next step to add to the workflow")
    is_complete: bool = Field(..., description="Whether the workflow is complete after adding this step")
    reasoning: str = Field(..., description="Explanation for why this step is needed")

class NextLinearStepBatch(BaseModel):
    """Response model for generating multiple linear workflow steps at once (1-3 steps)."""
    step_1: Union[LinearToolStep, LinearLLMStep, LinearFinalStep] = Field(
        ..., 
        description="The first step to add to the workflow (required)"
    )
    step_2: Optional[Union[LinearToolStep, LinearLLMStep, LinearFinalStep]] = Field(
        None, 
        description="The second step to add to the workflow (optional)"
    )
    step_3: Optional[Union[LinearToolStep, LinearLLMStep, LinearFinalStep]] = Field(
        None, 
        description="The third step to add to the workflow (optional)"
    )
    is_complete: bool = Field(..., description="Whether the linear workflow is complete after adding these steps")
    reasoning: str = Field(..., description="Explanation for why these steps are needed and how they relate to each other")

    @property
    def steps(self) -> List[Union[LinearToolStep, LinearLLMStep, LinearFinalStep]]:
        """Returns all non-None steps as a list for compatibility."""
        return [s for s in [self.step_1, self.step_2, self.step_3] if s is not None]


class NextStructuredStepBatch(BaseModel):
    """Response model for generating multiple structured workflow steps at once (1-3 steps)."""
    step_1: Union[StructuredToolStep, StructuredLLMStep, StructuredFinalStep] = Field(
        ..., 
        description="The first step to add to the workflow (required)"
    )
    step_2: Optional[Union[StructuredToolStep, StructuredLLMStep, StructuredFinalStep]] = Field(
        None, 
        description="The second step to add to the workflow (optional)"
    )
    step_3: Optional[Union[StructuredToolStep, StructuredLLMStep, StructuredFinalStep]] = Field(
        None, 
        description="The third step to add to the workflow (optional)"
    )
    is_complete: bool = Field(..., description="Whether the workflow is complete after adding these steps")
    reasoning: str = Field(..., description="Explanation for why these steps are needed and how they relate to each other")

    @property
    def steps(self) -> List[Union[StructuredToolStep, StructuredLLMStep, StructuredFinalStep]]:
        """Returns all non-None steps as a list for compatibility."""
        return [s for s in [self.step_1, self.step_2, self.step_3] if s is not None]
