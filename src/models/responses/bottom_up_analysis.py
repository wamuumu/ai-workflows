from pydantic import BaseModel, Field
from typing import List, Literal

class ToolRequirement(BaseModel):
    """An object representing a required tool for the workflow."""
    tool_name: str = Field(..., description="Name of the required tool")
    purpose: str = Field(..., description="Why this tool is needed")
    inputs_needed: List[str] = Field(..., description="What inputs this tool needs")
    outputs_produced: List[str] = Field(..., description="What outputs this tool produces")

class ToolAnalysisResponse(BaseModel):
    """Response detailing tool requirements for the workflow."""
    required_tools: List[ToolRequirement] = Field(..., description="All tools needed to accomplish the task")
    reasoning: str = Field(..., description="Overall reasoning for tool selection")

class ToolOrderingResponse(BaseModel):
    """Response detailing the execution order of tool calls."""
    ordered_calls: List[str] = Field(..., description="Names of tools in the order they should be called")
    reasoning: str = Field(..., description="Overall reasoning for tool ordering")

class ControlFlowDecision(BaseModel):
    """A decision point in the workflow where control flow (branching/conditional) is needed."""
    decision_point: int = Field(..., description="The step ID where decision/branching is needed")
    decision_type: Literal["branching", "conditional"] = Field(..., description="Type of control flow needed")
    reason: str = Field(..., description="Why control flow is needed here")
    branches: List[str] = Field(..., description="Possible branch outcomes")

class ControlFlowResponse(BaseModel):
    """Response detailing control flow decisions needed in the workflow."""
    control_decisions: List[ControlFlowDecision] = Field(..., description="All control flow decisions needed")
    llm_calls_needed: List[int] = Field(..., description="Step IDs where LLM reasoning is needed")
    reasoning: str = Field(..., description="Overall control flow reasoning")