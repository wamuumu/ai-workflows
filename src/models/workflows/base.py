from pydantic import BaseModel, Field
from typing import Union

class Metadata(BaseModel):
    """Metadata for a workflow step."""
    original_prompt: str = Field(..., description="The original user prompt that initiated the workflow")

class ToolParameter(BaseModel):
    """Parameter for a tool call."""
    key: str = Field(..., description="Parameter key matching selected tool input schema")
    value: Union[str, int, float, bool] = Field(
        ..., 
        description=(
            "Literal value or reference to another step's output. "
            "To reference another step's output, use the format: {id.output_field} (e.g. {1.response}, {2.output}, etc.). "
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
    thoughts: str = Field(
        ..., 
        description=(
            "Extensive reasoning about the step's purpose and approach. "
            "This should include the rationale for tool selection and parameter choices. "
            "Be as detailed as possible to ensure clarity in the workflow's logic."
        )
    )

class FinalStep(BaseStep):
    """The final step either of a linear workflow or a branch in a structured workflow.
    
    - Indicates workflow completion.
    - MUST be the last step in a linear workflow or the terminal step in a structured workflow branch.
    """
    is_final: bool = True
