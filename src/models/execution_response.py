from pydantic import BaseModel, Field
from typing import List, Union, Literal

class Parameter(BaseModel):
    """An object representing a key-value pair in tool parameters or results."""
    key: str = Field(..., description="The parameter key")
    value: Union[str, int, float, bool] = Field(..., description="The parameter value")

class BaseStep(BaseModel):
    """Base class for a workflow step."""
    id: str = Field(..., description="Unique identifier for the step")

class ToolStep(BaseStep):
    """A tool step in a workflow execution response."""
    action: Literal["call_tool"] = "call_tool"
    tool_name: str = Field(..., description="Name of the tool to call")
    tool_parameters: List[Parameter] = Field(..., description="Input parameters for the tool function")

class LLMStep(BaseStep):
    """An LLM step in a workflow execution response."""
    action: Literal["call_llm"] = "call_llm"
    response: str = Field(..., description="The LLM response content")

class FinalStep(BaseStep):
    """The final step in a workflow."""
    is_final: Literal[True] = True

class ExecutionResponse(BaseModel):
    """An execution response representing a single step in the workflow execution."""
    step: Union[ToolStep, LLMStep, FinalStep] = Field(..., description="The executed step details")