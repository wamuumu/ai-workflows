from pydantic import BaseModel, Field
from typing import List

# Phase 1: Tool Identification
class ToolRequirement(BaseModel):
    tool_name: str = Field(..., description="Name of the required tool")
    purpose: str = Field(..., description="Why this tool is needed")
    inputs_needed: List[str] = Field(..., description="What inputs this tool needs")
    outputs_produced: List[str] = Field(..., description="What outputs this tool produces")

class ToolAnalysisResponse(BaseModel):
    required_tools: List[ToolRequirement] = Field(..., description="All tools needed to accomplish the task")
    reasoning: str = Field(..., description="Overall reasoning for tool selection")

# Phase 2: Tool Ordering
class ToolCall(BaseModel):
    step_id: str = Field(..., description="Sequential step ID (step_1, step_2, etc.)")
    tool_name: str = Field(..., description="Name of the tool to call")
    depends_on: List[str] = Field(default_factory=list, description="Step IDs this depends on")
    purpose: str = Field(..., description="What this tool call accomplishes")

class ToolOrderingResponse(BaseModel):
    ordered_calls: List[ToolCall] = Field(..., description="Tools in execution order")
    reasoning: str = Field(..., description="Reasoning for the ordering")

# Phase 3: Control Flow
class ControlFlowDecision(BaseModel):
    decision_point: str = Field(..., description="Where decision/branching is needed (step_id or 'none')")
    decision_type: str = Field(..., description="Type: 'branching', 'conditional', or 'none'")
    reason: str = Field(..., description="Why control flow is needed here")
    branches: List[str] = Field(default_factory=list, description="Possible branch outcomes")

class ControlFlowResponse(BaseModel):
    control_decisions: List[ControlFlowDecision] = Field(..., description="All control flow decisions needed")
    llm_calls_needed: List[str] = Field(..., description="Step IDs where LLM reasoning is needed")
    reasoning: str = Field(..., description="Overall control flow reasoning")