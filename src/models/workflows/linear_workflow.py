"""
Linear Workflow Model
=====================

This module defines the Pydantic schema for linear (sequential) workflows
in the AI-Workflows framework. Linear workflows execute steps in strict
order without branching or conditional logic.

Main Responsibilities:
    - Define ToolStep for tool invocation in linear context
    - Define LLMStep for LLM reasoning in linear context
    - Define LinearWorkflow as the top-level container

Key Dependencies:
    - pydantic: For data validation and schema definition
    - models.workflows.base: For shared step types and metadata

Use Cases:
    Linear workflows are suitable for tasks with deterministic execution
    paths where the sequence of operations is known in advance and does
    not depend on intermediate results.
"""

from pydantic import BaseModel, Field
from typing import List, Union, Literal

from models.workflows.base import Metadata, ToolParameter, BaseStep, FinalStep


class ToolStep(BaseStep):
    """
    A workflow step that invokes an external tool.
    
    Tool steps execute registered tools with specified parameters and
    produce structured outputs that can be referenced by subsequent steps.
    
    Attributes:
        action: Literal discriminator indicating this is a tool call.
        tool_name: Name of the registered tool to invoke.
        parameters: List of key-value pairs for the tool's input schema.
    
    Output Behavior:
        Tool outputs are stored in the workflow state and can be referenced
        by downstream steps using the {step_id.output_field} syntax.
    """
    action: Literal["call_tool"] = "call_tool"
    tool_name: str = Field(..., description="Name of the tool to call")
    parameters: List[ToolParameter] = Field(..., description="Input parameters for the tool function")


class LLMStep(BaseStep):
    """
    A workflow step that invokes LLM reasoning.
    
    LLM steps are used for non-deterministic decisions such as analysis,
    classification, summarization, or content generation. They produce
    unstructured text responses.
    
    Attributes:
        action: Literal discriminator indicating this is an LLM call.
        prompt: The prompt to send to the LLM, may include output references.
    
    Output Behavior:
        LLM responses are stored as a 'response' field in the workflow state
        and can be referenced by downstream steps using {step_id.response}.
    """
    action: Literal["call_llm"] = "call_llm"
    prompt: str = Field(
        ..., 
        description="""
            The prompt to send to the LLM, may include references to prior step outputs. 
            To reference another step's output, use the format: {id.output_field} (e.g. {1.response}, {2.output}, etc.). 
            Return only unstructured text output from the LLM.
        """
    )


class LinearWorkflow(BaseModel):
    """
    Top-level container for a linear (sequential) workflow.
    
    Linear workflows consist of an ordered list of steps that execute
    sequentially from first to last. The final step must be a FinalStep.
    
    Attributes:
        title: Human-readable title for the workflow.
        description: Detailed description of the workflow's purpose.
        target_objective: The goal this workflow aims to achieve.
        metadata: Provenance information including the original prompt.
        steps: Ordered list of workflow steps to execute.
    
    Execution Model:
        Steps are executed in list order (steps[0], steps[1], ...).
        Execution terminates when a FinalStep is reached.
    """
    title: str = Field(..., description="Title of the linear workflow")
    description: str = Field(..., description="Description of the linear workflow")
    target_objective: str = Field(..., description="The intended objective based on the user prompt")
    metadata: Metadata = Field(..., description="Metadata for the linear workflow")
    steps: List[Union[ToolStep, LLMStep, FinalStep]] = Field(..., description="List of steps in the linear workflow")