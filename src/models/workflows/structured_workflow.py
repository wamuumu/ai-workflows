"""
Structured Workflow Model
=========================

This module defines the Pydantic schema for structured (branching) workflows
in the AI-Workflows framework. Structured workflows support conditional
transitions and non-linear execution paths based on step outputs.

Main Responsibilities:
    - Define Transition schema for conditional branching logic
    - Define ToolStep with transitions for tool invocation
    - Define LLMStep with transitions for LLM reasoning
    - Define StructuredWorkflow as the top-level container

Key Dependencies:
    - pydantic: For data validation and schema definition
    - models.workflows.base: For shared step types and metadata

Use Cases:
    Structured workflows are suitable for tasks requiring decision points,
    error handling branches, or dynamic execution paths that depend on
    intermediate results (e.g., weather-dependent activity planning).
"""

from pydantic import BaseModel, Field
from typing import List, Union, Literal

from models.workflows.base import Metadata, ToolParameter, BaseStep, FinalStep


class Transition(BaseModel):
    """
    Schema for conditional branching between workflow steps.
    
    Transitions define the control flow in structured workflows by specifying
    conditions under which execution should proceed to a target step.
    
    Attributes:
        condition: Human-readable condition expression (e.g., 'if weather is rainy').
        next_step: Target step ID to transition to when condition is met.
    
    Design Notes:
        Conditions are evaluated semantically by the executor agent rather
        than programmatically. Each step should have mutually exclusive
        conditions that collectively cover all possible outcomes. Tool steps
        typically have a single 'always' condition to proceed to the next step.
    """
    condition: str = Field(
        ..., 
        description="""
            Condition to evaluate for this transition. 
            This should be a clear, concise expression based on the current step's outputs. 
            For example, 'if response contains "yes"' or 'if output_value > 10'. 
        """
    )
    next_step: int = Field(..., description="Target step ID to transition to if condition is met")


class ToolStep(BaseStep):
    """
    A workflow step that invokes an external tool with conditional transitions.
    
    Attributes:
        action: Literal discriminator indicating this is a tool call.
        tool_name: Name of the registered tool to invoke.
        parameters: List of key-value pairs for the tool's input schema.
        transition: Transition defining control flow after tool execution.
    """
    action: Literal["call_tool"] = "call_tool"
    tool_name: str = Field(..., description="Name of the tool to call")
    parameters: List[ToolParameter] = Field(..., description="Input parameters for the tool function")
    transition: Transition = Field(
        ...,
        description="Transition defining control flow after tool execution."    
    )


class LLMStep(BaseStep):
    """
    A workflow step that invokes LLM reasoning with conditional transitions.
    
    LLM steps in structured workflows are particularly useful for non-deterministic
    decision points where the next action depends on semantic analysis of prior outputs.
    
    Attributes:
        action: Literal discriminator indicating this is an LLM call.
        prompt: The prompt to send to the LLM, may include output references.
        transitions: List of conditional branches based on LLM response.
    
    Transition Requirements:
        - Conditions should be based on expected patterns in LLM output.
        - All possible outcomes should be covered.
        - Prompts should be designed to produce predictable response formats.
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
    transitions: List[Transition] = Field(
        ...,
        description="""
            List of transitions defining control flow. Must be mutually exclusive conditions covering all outcomes.
            For example, a possible scenario can contain: 'if A', 'if B', 'if C', etc. where A, B, C are distinct conditions based on LLM output.
            Ensure all possible conditions are covered to avoid dead-ends in the workflow.
        """
    )


class StructuredWorkflow(BaseModel):
    """
    Top-level container for a structured (branching) workflow.
    
    Structured workflows support non-linear execution through conditional
    transitions. The execution engine evaluates transition conditions after
    each step to determine the next step to execute.
    
    Attributes:
        title: Human-readable title for the workflow.
        description: Detailed description of the workflow's purpose.
        target_objective: The goal this workflow aims to achieve.
        metadata: Provenance information including the original prompt.
        steps: Collection of workflow steps (order in list is not execution order).
    
    Execution Model:
        Execution begins at step ID 1. After each step, the executor evaluates
        that step's transitions to determine the next step. Execution terminates
        when a FinalStep is reached.
    
    Graph Constraints:
        - All steps must be reachable from step 1.
        - All non-final steps must have at least one outgoing transition.
        - All execution paths must eventually reach a FinalStep.
    """
    title: str = Field(..., description="Title of the structured workflow")
    description: str = Field(..., description="Description of the structured workflow")
    target_objective: str = Field(..., description="The intended objective based on the user prompt")
    metadata: Metadata = Field(..., description="Metadata for the structured workflow")
    steps: List[Union[ToolStep, LLMStep, FinalStep]] = Field(..., description="List of steps in the structured workflow")