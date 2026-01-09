from pydantic import BaseModel, Field
from typing import Union

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

class FinalStep(BaseStep):
    """The final step either of a linear workflow or a branch in a structured workflow."""
    is_final: bool = True
