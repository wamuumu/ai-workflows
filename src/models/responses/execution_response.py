"""
Execution Response Models
=========================

This module defines the Pydantic schemas for workflow execution responses.
These models represent the executor agent's output at each step during
workflow execution, enabling proper parameter resolution and state management.

Main Responsibilities:
    - Define Parameter schema for resolved tool parameters
    - Define step types (ToolStep, LLMStep, FinalStep) for execution context
    - Define ExecutionResponse as the per-step execution output

Key Dependencies:
    - pydantic: For data validation and schema definition

Execution Flow:
    1. Executor receives current workflow state and workflow definition
    2. Executor produces ExecutionResponse indicating next action
    3. Orchestrator executes the action (tool call or stores LLM response)
    4. State is updated and fed back for next iteration

Design Notes:
    The Parameter class differs from workflow ToolParameter by requiring
    fully resolved values (no placeholders). All {step_id.field} references
    must be replaced with actual values from the execution state.
"""

from pydantic import BaseModel, Field
from typing import List, Union, Literal


class Parameter(BaseModel):
    """
    Schema for a resolved parameter in tool execution.
    
    Unlike workflow-level ToolParameter, execution Parameters must have
    all placeholders fully resolved to concrete values from the current
    execution state.
    
    Attributes:
        key: Parameter name matching the tool's input schema.
        value: Fully resolved value (no placeholders allowed).
    
    Execution Rules:
        - All {id.output_field} placeholders must be resolved before execution.
        - Values must come from previously completed steps in the execution path.
        - Stale, unresolved, or inferred values must not be used.
    """
    key: str = Field(..., description="The exact parameter key as defined in the original workflow step")
    value: Union[str, int, float, bool] = Field(
        ..., 
        description="""
            The fully resolved parameter value with all placeholders replaced from state. "
            Must be the exact value from a completed step's output, not an inferred or placeholder value."
        """
    )


class BaseStep(BaseModel):
    """
    Base class for execution step representations.
    
    Provides the common identifier that links execution responses back
    to the original workflow step definitions.
    
    Attributes:
        id: Step identifier matching the workflow step ID.
    """
    id: str = Field(
        ..., 
        description="""
            Unique identifier for the step, matching the step ID from the original workflow. 
            Must correspond to the current step being executed in sequence.
        """
    )


class ToolStep(BaseStep):
    """
    Execution representation of a tool invocation step.
    
    Contains the resolved parameters ready for immediate tool execution.
    
    Attributes:
        action: Discriminator indicating tool execution.
        tool_name: Exact name of the tool to invoke.
        parameters: List of fully resolved parameter values.
    """
    action: Literal["call_tool"] = "call_tool"
    tool_name: str = Field(
        ..., 
        description="Exact name of the tool to call, as defined in the original workflow step"
    )
    parameters: List[Parameter] = Field(
        ..., 
        description="""
            Input parameters for the tool function with ALL placeholders resolved. 
            Each parameter must use exact values from the current state. 
            Do NOT include unresolved placeholders or inferred values.
        """
    )


class LLMStep(BaseStep):
    """
    Execution representation of an LLM reasoning step.
    
    Contains the LLM's generated response which will be stored in state.
    
    Attributes:
        action: Discriminator indicating LLM execution.
        response: The complete LLM-generated response text.
    """
    action: Literal["call_llm"] = "call_llm"
    response: str = Field(
        ..., 
        description="""
            The complete LLM response generated from the resolved prompt. 
            This response will be stored in state and can be referenced by downstream steps.
        """
    )


class FinalStep(BaseStep):
    """
    Execution representation of workflow termination.
    
    Indicates that the workflow has completed successfully.
    
    Attributes:
        is_final: Boolean flag always set to True.
    """
    is_final: bool = True


class ExecutionResponse(BaseModel):
    """
    Response schema for a single workflow execution step.
    
    Represents the executor's output for each iteration of the execution
    loop. The step field indicates what action to take next.
    
    Attributes:
        step: The execution step details (ToolStep, LLMStep, or FinalStep).
    
    Step Types:
        - ToolStep: Requests external tool invocation with resolved parameters.
        - LLMStep: Contains LLM-generated response to store in state.
        - FinalStep: Signals workflow completion.
    """
    step: Union[ToolStep, LLMStep, FinalStep] = Field(
        ..., 
        description="""
            The currently executed step details. 
            Must be one of: ToolStep (requests external tool call), 
            LLMStep (contains LLM-generated response), or FinalStep (marks workflow completion).
        """
    )