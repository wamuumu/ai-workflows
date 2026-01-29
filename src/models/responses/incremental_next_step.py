"""
Incremental Strategy Response Models
=====================================

This module defines the Pydantic schemas for structured responses used in the
incremental workflow generation strategy. These models capture batched step
generation to optimize API calls while building workflows progressively.

Main Responsibilities:
    - Define FinalStep with workflow metadata for completion
    - Define NextLinearStepBatch for linear workflow generation
    - Define NextStructuredStepBatch for structured workflow generation

Key Dependencies:
    - pydantic: For data validation and schema definition
    - models.workflows.base: For base step types and metadata
    - models.workflows.linear_workflow: For linear step types
    - models.workflows.structured_workflow: For structured step types

Batch Generation Strategy:
    Instead of generating one step per LLM call, the incremental strategy
    generates 1-3 steps at a time. This reduces API calls while maintaining
    the ability to adapt the workflow based on intermediate context.
"""

from pydantic import BaseModel, Field
from typing import List, Union, Optional

from models.workflows.base import FinalStep as BaseFinalStep, Metadata as BaseMetadata
from models.workflows.linear_workflow import ToolStep as LinearToolStep, LLMStep as LinearLLMStep
from models.workflows.structured_workflow import ToolStep as StructuredToolStep, LLMStep as StructuredLLMStep


class FinalStep(BaseFinalStep):
    """
    Extended FinalStep for incremental generation with workflow metadata.
    
    When the incremental strategy determines the workflow is complete, the
    FinalStep includes full workflow metadata that would normally be at the
    top level of the workflow object.
    
    Attributes:
        workflow_title: Title for the completed workflow.
        workflow_description: Description of the workflow's purpose.
        target_objective: The goal this workflow achieves.
        metadata: Provenance information including original prompt.
    
    Design Notes:
        This approach allows metadata to be generated alongside the final step,
        ensuring the generator has full context of all steps when creating
        the summary information.
    """
    workflow_title: str = Field(..., description="Title of the entire completed workflow")
    workflow_description: str = Field(..., description="Description of the entire completed workflow")
    target_objective: str = Field(..., description="The intended objective based on the initial user prompt")
    metadata: BaseMetadata = Field(..., description="Additional metadata about the workflow")


class NextLinearStepBatch(BaseModel):
    """
    Response schema for generating batched linear workflow steps.
    
    Allows the generator to produce 1-3 consecutive steps in a single
    LLM call, reducing total API calls while maintaining incremental
    context awareness.
    
    Attributes:
        step_1: Required first step in this batch.
        step_2: Optional second step if sequence is clear.
        step_3: Optional third step if sequence is clear.
        is_complete: Whether workflow generation is finished.
        reasoning: Explanation for the batch generation decision.
    
    Properties:
        steps: Convenience property returning list of non-None steps.
    """
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
        """
        Collect all non-None steps as a list for iteration compatibility.
        
        Returns:
            List of steps in batch order, excluding None values.
        """
        return [s for s in [self.step_1, self.step_2, self.step_3] if s is not None]


class NextStructuredStepBatch(BaseModel):
    """
    Response schema for generating batched structured workflow steps.
    
    Similar to NextLinearStepBatch but for structured workflows with
    transition support.
    
    Attributes:
        step_1: Required first step in this batch.
        step_2: Optional second step if sequence is clear.
        step_3: Optional third step if sequence is clear.
        is_complete: Whether workflow generation is finished.
        reasoning: Explanation for the batch generation decision.
    
    Properties:
        steps: Convenience property returning list of non-None steps.
    """
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
        """
        Collect all non-None steps as a list for iteration compatibility.
        
        Returns:
            List of steps in batch order, excluding None values.
        """
        return [s for s in [self.step_1, self.step_2, self.step_3] if s is not None]
