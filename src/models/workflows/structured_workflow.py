from pydantic import BaseModel, Field
from typing import List, Union, Literal

from tools.registry import ToolRegistry

class ToolParameter(BaseModel):
    """Parameter for a tool call."""
    key: str = Field(..., description="Parameter key matching selected tool input schema", json_schema_extra={"enum": ToolRegistry.get_all_input_keys()})
    value: Union[str, int, float, bool] = Field(
        ..., 
        description=(
            "Literal value or reference to another step's output. "
            "To reference another step's output, use the format: {id.output_field} (e.g. {1.response}, {2.output}, etc.). "
            f"Valid 'output_field' values are: {', '.join(['response'] + ToolRegistry.get_all_output_keys())}"
        )
    )

class Transition(BaseModel):
    """Defines conditional branching to next step.
    
    - All transitions from a single step must be mutually exclusive.
    """
    condition: str = Field(
        ..., 
        description=(
            "Condition to evaluate for this transition. "
            "Use clear and simple conditions like 'if yes', 'if no', 'true', 'false', 'success', 'error', 'always', 'default', etc."
        )
    )
    next_step: int = Field(..., description="Target step ID to transition to if condition is met")

class BaseStep(BaseModel):
    """Base for all workflow steps."""
    id: int = Field(
        ...,
        description=(
            "Sequential, unique step identifier. "
            "Step IDs must start at 1 and increment by 1 for each subsequent step. "
            "Do not repeat IDs across steps."
        )
    )
    thoughts: str = Field(..., description="Reasoning for this step's purpose and logic")

class ToolStep(BaseStep):
    """A single tool step in a structured workflow.
    
    - Tool steps must explicitly define transitions to handle all possible outcomes.
    - Tool outputs produce fields that can be referenced in downstream transitions and steps.
    """
    action: Literal["call_tool"] = "call_tool"
    tool_name: str = Field(..., description="Name of the tool to call", json_schema_extra={"enum": ToolRegistry.get_all_tool_names()})
    parameters: List[ToolParameter] = Field(..., description="Input parameters for the tool function")
    transitions: List[Transition] = Field(
        ...,
        description="List of transitions defining control flow. Must be mutually exclusive conditions covering all outcomes."    
    )

class LLMStep(BaseStep):
    """A single llm step in a structured workflow.
    
    - Used for non-deterministic decisions (e.g., analysis, classification, branching, summarization, etc.)
    - Output an unstructure text 'response' field that can be referenced by downstream steps.
    """
    action: Literal["call_llm"] = "call_llm"
    prompt: str = Field(
        ..., 
        description=(
            "The prompt to send to the LLM, may include references to prior step outputs. "
            "To reference another step's output, use the format: {id.output_field} (e.g. {1.response}, {2.output}, etc.). "
            f"Valid 'output_field' values are: {', '.join(['response'] + ToolRegistry.get_all_output_keys())}"
        )
    )
    transitions: List[Transition] = Field(
        ...,
        description="List of transitions defining control flow. Must be mutually exclusive conditions covering all outcomes."
    )

class FinalStep(BaseStep):
    """The final step in an execution path / branch of a structured workflow."""
    is_final: bool = True

class StructuredWorkflow(BaseModel):
    """A workflow consisting of steps with branching and conditional transitions."""
    title: str = Field(..., description="Title of the structured workflow")
    description: str = Field(..., description="Description of the structured workflow")
    target_objective: str = Field(..., description="The intended objective based on the user prompt")
    steps: List[Union[ToolStep, LLMStep, FinalStep]] = Field(..., description="List of steps in the structured workflow")