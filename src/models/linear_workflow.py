from pydantic import BaseModel, Field
from typing import List, Union, Literal

class Parameter(BaseModel):
    """An object representing a parameter item in a workflow step."""
    key: str = Field(..., description="The parameter key")
    value: Union[str, int, float, bool] = Field(..., description="The parameter value")

class BaseStep(BaseModel):
    """Base class for a workflow step."""
    id: str = Field(..., description="Unique identifier for the step")
    thoughts: str = Field(..., description="The agent's thoughts or reasoning for this step")

class ToolStep(BaseStep):
    """A single tool step in a linear workflow."""
    action: Literal["call_tool"] = "call_tool"
    tool_name: str = Field(..., description="Name of the tool to call")
    parameters: List[Parameter] = Field(..., description="Input parameters for the tool function")

class LLMStep(BaseStep):
    """A single LLM step in a linear workflow."""
    action: Literal["call_llm"] = "call_llm"
    prompt: str = Field(..., description="The prompt to send to the LLM")

class FinalStep(BaseStep):
    """The final step in a workflow."""
    is_final: bool = True    

class LinearWorkflow(BaseModel):
    """A linear workflow consisting of a sequence of steps."""
    title: str = Field(..., description="Title of the linear workflow")
    description: str = Field(..., description="Description of the linear workflow")
    target_objective: str = Field(..., description="The intended objective based on the user prompt")
    type: Literal["linear"] = "linear"
    steps: List[Union[ToolStep, LLMStep, FinalStep]] = Field(..., description="List of steps in the linear workflow")