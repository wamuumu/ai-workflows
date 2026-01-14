from pydantic import BaseModel, Field
from typing import List, Union, Literal

from models.workflows.base import Metadata, ToolParameter, BaseStep, FinalStep
from tools.registry import ToolRegistry

class Transition(BaseModel):
    """Defines conditional branching to next step."""
    condition: str = Field(
        ..., 
        description=(
            "Condition to evaluate for this transition. "
            "Use clear and simple conditions labels like 'if success', 'if failure', ' if contains XYZ', 'always', 'if yes', 'if no', etc. "
        )
    )
    next_step: int = Field(..., description="Target step ID to transition to if condition is met")

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
    - All possible outcomes must be handled via transitions to avoid dead-ends.
    - Transitions should use clear conditions based on expected LLM outputs.
    """
    action: Literal["call_llm"] = "call_llm"
    prompt: str = Field(
        ..., 
        description=(
            "The prompt to send to the LLM, may include references to prior step outputs. "
            "To reference another step's output, use the format: {id.output_field} (e.g. {1.response}, {2.output}, etc.). "
            f"Valid 'output_field' values are: {', '.join(['response'] + ToolRegistry.get_all_output_keys())}"
            "Allow only unstructured text output from the LLM."
        )
    )
    transitions: List[Transition] = Field(
        ...,
        description=(
            "List of transitions defining control flow. Must be mutually exclusive conditions covering all outcomes. ",
            "For example, a possible scenario can contain: 'if A', 'if B', 'if C', etc. where A, B, C are distinct conditions based on LLM output."
            "You MUST ensure that all possible conditions are covered to avoid dead-ends in the workflow."
        )
    )

class StructuredWorkflow(BaseModel):
    """A workflow consisting of steps with branching and conditional transitions."""
    title: str = Field(..., description="Title of the structured workflow")
    description: str = Field(..., description="Description of the structured workflow")
    target_objective: str = Field(..., description="The intended objective based on the user prompt")
    metadata: Metadata = Field(..., description="Metadata for the structured workflow")
    steps: List[Union[ToolStep, LLMStep, FinalStep]] = Field(..., description="List of steps in the structured workflow")