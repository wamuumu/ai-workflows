from pydantic import BaseModel, Field
from typing import List, Union, Literal

from models.workflows.base import ToolParameter, BaseStep, FinalStep
from tools.registry import ToolRegistry

class ToolStep(BaseStep):
    """A single tool step in a linear workflow.
    
    - Tool outputs produce fields that can be referenced in downstream transitions and steps.
    """
    action: Literal["call_tool"] = "call_tool"
    tool_name: str = Field(..., description="Name of the tool to call", json_schema_extra={"enum": ToolRegistry.get_all_tool_names()})
    parameters: List[ToolParameter] = Field(..., description="Input parameters for the tool function")

class LLMStep(BaseStep):
    """A single llm step in a linear workflow.
    
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
            "Allow only unstructured text output from the LLM."
        )
    )

class LinearWorkflow(BaseModel):
    """A workflow consisting of a linear sequence of steps."""
    title: str = Field(..., description="Title of the linear workflow")
    description: str = Field(..., description="Description of the linear workflow")
    target_objective: str = Field(..., description="The intended objective based on the user prompt")
    steps: List[Union[ToolStep, LLMStep, FinalStep]] = Field(..., description="List of steps in the linear workflow")