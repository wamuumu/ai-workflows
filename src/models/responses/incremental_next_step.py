from pydantic import BaseModel, Field
from typing import List, Union, Optional

from models.workflows.base import FinalStep as BaseFinalStep, Metadata as BaseMetadata
from models.workflows.linear_workflow import ToolStep as LinearToolStep, LLMStep as LinearLLMStep
from models.workflows.structured_workflow import ToolStep as StructuredToolStep, LLMStep as StructuredLLMStep

class FinalStep(BaseFinalStep):
    """The final step of a completed incremental workflow, containing additional metadata."""
    workflow_title: str = Field(..., description="Title of the entire completed workflow")
    workflow_description: str = Field(..., description="Description of the entire completed workflow")
    target_objective: str = Field(..., description="The intended objective based on the initial user prompt")
    metadata: BaseMetadata = Field(..., description="Additional metadata about the workflow")

class NextLinearStepBatch(BaseModel):
    """Response model for generating multiple linear workflow steps at once (1-3 steps)."""
    step_1: Union[LinearToolStep, LinearLLMStep, FinalStep] = Field(
        ..., 
        description="The first step to add to the workflow"
    )
    step_2: Optional[Union[LinearToolStep, LinearLLMStep, FinalStep]] = Field(
        None, 
        description="The second step - generate this when additional sequential steps are clearly needed"
    )
    step_3: Optional[Union[LinearToolStep, LinearLLMStep, FinalStep]] = Field(
        None, 
        description="The third step - generate this when a third sequential step logically follows"
    )
    is_complete: bool = Field(..., description="Whether the workflow is complete after adding these steps")
    reasoning: str = Field(..., description="Brief explanation for why these steps are needed")

    @property
    def steps(self) -> List[Union[LinearToolStep, LinearLLMStep, FinalStep]]:
        """Returns all non-None steps as a list for compatibility."""
        return [s for s in [self.step_1, self.step_2, self.step_3] if s is not None]


class NextStructuredStepBatch(BaseModel):
    """Response model for generating multiple structured workflow steps at once (1-3 steps)."""
    step_1: Union[StructuredToolStep, StructuredLLMStep, FinalStep] = Field(
        ..., 
        description="The first step to add to the workflow"
    )
    step_2: Optional[Union[StructuredToolStep, StructuredLLMStep, FinalStep]] = Field(
        None, 
        description="The second step - generate this when additional sequential steps are clearly needed"
    )
    step_3: Optional[Union[StructuredToolStep, StructuredLLMStep, FinalStep]] = Field(
        None, 
        description="The third step - generate this when a third sequential step logically follows"
    )
    is_complete: bool = Field(..., description="Whether the workflow is complete after adding these steps")
    reasoning: str = Field(..., description="Brief explanation for why these steps are needed")

    @property
    def steps(self) -> List[Union[StructuredToolStep, StructuredLLMStep, FinalStep]]:
        """Returns all non-None steps as a list for compatibility."""
        return [s for s in [self.step_1, self.step_2, self.step_3] if s is not None]
