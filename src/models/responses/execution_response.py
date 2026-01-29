from pydantic import BaseModel, Field
from typing import List, Union, Literal

class Parameter(BaseModel):
    """An object representing a key-value pair in tool parameters.
    
    Execution Rules:
    - All placeholders of the form {id.output_field} MUST be resolved before execution
    - Placeholders may ONLY reference outputs from previously completed steps in the same execution path
    - Use exact values from the current state - do NOT use stale, unresolved, or inferred values
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
    """Base class for a workflow step."""
    id: str = Field(
        ..., 
        description="""
            Unique identifier for the step, matching the step ID from the original workflow. 
            Must correspond to the current step being executed in sequence.
        """
    )

class ToolStep(BaseStep):
    """A tool step in a workflow execution response."""
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
    """An LLM step in a workflow execution response."""
    action: Literal["call_llm"] = "call_llm"
    response: str = Field(
        ..., 
        description="""
            The complete LLM response generated from the resolved prompt. 
            This response will be stored in state and can be referenced by downstream steps.
        """
    )

class FinalStep(BaseStep):
    """The final step in the execution path."""
    is_final: bool = True

class ExecutionResponse(BaseModel):
    """An execution response representing a single step in the workflow execution."""
    step: Union[ToolStep, LLMStep, FinalStep] = Field(
        ..., 
        description="""
            The currently executed step details. 
            Must be one of: ToolStep (requests external tool call), 
            LLMStep (contains LLM-generated response), or FinalStep (marks workflow completion).
        """
    )