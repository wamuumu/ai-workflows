from pydantic import BaseModel, Field
from typing import List, Union, Literal

class Parameter(BaseModel):
    """An object representing a parameter item in a workflow step."""
    key: str = Field(..., description="The parameter key")
    value: Union[str, int, float, bool] = Field(..., description="The parameter value")

class Transition(BaseModel):
    """A single transition in a structured workflow."""
    condition: str = Field(..., description="Condition for this transition")
    next_step: str = Field(..., description="The step ID to transition to")

class BaseStep(BaseModel):
    """Base class for a workflow step."""
    id: str = Field(..., description="Unique identifier for the step")
    thoughts: str = Field(..., description="The agent's thoughts or reasoning for this step")

class ToolStep(BaseStep):
    """A single tool step in a linear workflow."""
    action: Literal["call_tool"] = "call_tool"
    tool_name: str = Field(..., description="Name of the tool to call")
    parameters: List[Parameter] = Field(..., description="Input parameters for the tool function")
    transitions: List[Transition] = Field(..., description="Transitions for the steps")

class LLMStep(BaseStep):
    """A single LLM step in a linear workflow."""
    action: Literal["call_llm"] = "call_llm"
    prompt: str = Field(..., description="The prompt to send to the LLM")
    transitions: List[Transition] = Field(..., description="Transitions for the steps")

class FinalStep(BaseStep):
    """The final step in a workflow."""
    is_final: bool = True

class StructuredWorkflow(BaseModel):
    """A structured workflow consisting of a sequence of steps and allowing branching."""
    title: str = Field(..., description="Title of the structured workflow")
    description: str = Field(..., description="Description of the structured workflow")
    target_objective: str = Field(..., description="The intended objective based on the user prompt")
    type: Literal["structured"] = "structured"
    steps: List[Union[ToolStep, LLMStep, FinalStep]] = Field(..., description="List of steps in the structured workflow")