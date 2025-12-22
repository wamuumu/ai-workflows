from pydantic import BaseModel, Field, model_validator
from typing import List, Union, Literal, Optional

class StepObject(BaseModel):
    """An object representing a key-value pair in tool parameters or results."""
    key: str = Field(..., description="The parameter key")
    value: Union[str, int, float, bool] = Field(..., description="The parameter value")

class ExecutionResponse(BaseModel):
    """A model representing the response from executing a step in a workflow."""
    step_id: str = Field(..., description="Unique identifier for the step")
    action: Literal["call_tool", "call_llm"] = Field(..., description="The action type for this step")
    tool_name: Optional[str] = Field(None, description="Name of the tool to call, ONLY if action is 'call_tool'")
    tool_parameters: Optional[List[StepObject]] = Field(None, description="Parameters for the tool, ONLY if action is 'call_tool'")
    llm_results: Optional[List[StepObject]] = Field(None, description="Results from the LLM, ONLY if action is 'call_llm'")

    @model_validator(mode='after')
    def validate_response(self):
        if self.action == "call_tool":
            if not self.tool_name:
                raise ValueError("tool_name must be provided for 'call_tool'")
            if self.llm_results is not None:
                raise ValueError("llm_results must be None for 'call_tool'")
        elif self.action == "call_llm":
            if self.tool_name is not None or self.tool_parameters is not None:
                raise ValueError("tool_name and tool_parameters must be None for 'call_llm'")
            if self.llm_results is None:
                raise ValueError("llm_results must be provided for 'call_llm'")
        return self