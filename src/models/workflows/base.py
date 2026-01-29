"""
Workflow Base Models
====================

This module defines the foundational Pydantic models used across all workflow
representations in the AI-Workflows framework. These base classes establish
the common schema elements shared by both linear and structured workflows.

Main Responsibilities:
    - Define Metadata schema for workflow provenance tracking
    - Define ToolParameter schema for tool invocation parameters
    - Define BaseStep as the foundation for all workflow step types
    - Define FinalStep to mark workflow termination points

Key Dependencies:
    - pydantic: For data validation and schema definition

Design Notes:
    The separation of base models allows for consistent schema enforcement
    while enabling specialized step types (ToolStep, LLMStep) in derived
    workflow models. The Field descriptions serve as prompts to guide
    LLM-based workflow generation.
"""

from pydantic import BaseModel, Field
from typing import Union


class Metadata(BaseModel):
    """
    Metadata container for workflow provenance information.
    
    Captures the original user prompt that initiated workflow generation,
    enabling traceability and evaluation against the original intent.
    
    Attributes:
        original_prompt: The verbatim user prompt used to generate this workflow.
    """
    original_prompt: str = Field(..., description="The original user prompt that initiated the workflow")


class ToolParameter(BaseModel):
    """
    Schema for a single parameter passed to a tool invocation.
    
    Parameters can contain either literal values or references to outputs
    from previous workflow steps, enabling data flow between steps.
    
    Attributes:
        key: Parameter name matching the tool's input schema.
        value: Literal value or step output reference (e.g., {1.response}).
    
    Reference Format:
        Step output references use the syntax {step_id.output_field},
        where step_id is the numeric ID of a prior step and output_field
        is one of that step's output keys.
    """
    key: str = Field(..., description="Parameter key matching selected tool input schema")
    value: Union[str, int, float, bool] = Field(
        ..., 
        description="""
            Literal value or reference to another step's output. 
            To reference another step's output, use the format: {id.output_field} (e.g. {1.response}, {2.output}, etc.). 
        """
    )


class BaseStep(BaseModel):
    """
    Abstract base class for all workflow steps.
    
    Provides the common attributes that every step in a workflow must have,
    including a unique identifier and reasoning documentation.
    
    Attributes:
        id: Unique sequential step identifier (1-indexed).
        thoughts: Detailed reasoning explaining the step's purpose and approach.
    
    Design Notes:
        The 'thoughts' field serves dual purposes: documenting the workflow
        logic for human reviewers and providing context for LLM-based
        evaluation and refinement.
    """
    id: int = Field(
        ...,
        description=(
            "Sequential, unique step identifier. "
            "Step IDs must start at 1 and increment by 1 for each subsequent step. "
            "Do not repeat IDs across steps."
        )
    )
    thoughts: str = Field(
        ..., 
        description="""
            Extensive reasoning about the step's purpose and approach. 
            This should include the rationale for tool selection and parameter choices. 
            Be as detailed as possible to ensure clarity in the workflow's logic.
        """
    )


class FinalStep(BaseStep):
    """
    Terminal step indicating workflow completion.
    
    A FinalStep marks the end of a workflow execution path. In linear workflows,
    this must be the last step. In structured workflows with branching, each
    branch must eventually terminate at a FinalStep.
    
    Attributes:
        is_final: Boolean flag always set to True for final steps.
    
    Usage:
        The presence of is_final=True distinguishes terminal steps from
        action steps during workflow execution.
    """
    is_final: bool = True
