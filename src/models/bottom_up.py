from pydantic import BaseModel, Field
from typing import List

class ToolRequirement(BaseModel):
    tool_name: str = Field(..., description="Name of the required tool")
    purpose: str = Field(..., description="Why this tool is needed")
    inputs_needed: List[str] = Field(..., description="What inputs this tool needs")
    outputs_produced: List[str] = Field(..., description="What outputs this tool produces")

class ToolAnalysisResponse(BaseModel):
    required_tools: List[ToolRequirement] = Field(..., description="All tools needed to accomplish the task")
    reasoning: str = Field(..., description="Overall reasoning for tool selection")

class ControlFlowDecision(BaseModel):
    decision_point: str = Field(..., description="Where decision/branching is needed (step_id or 'none')")
    decision_type: str = Field(..., description="Type: 'branching', 'conditional', or 'none'")
    reason: str = Field(..., description="Why control flow is needed here")
    branches: List[str] = Field(default_factory=list, description="Possible branch outcomes")

class ControlFlowResponse(BaseModel):
    control_decisions: List[ControlFlowDecision] = Field(..., description="All control flow decisions needed")
    llm_calls_needed: List[str] = Field(..., description="Step IDs where LLM reasoning is needed")
    reasoning: str = Field(..., description="Overall control flow reasoning")