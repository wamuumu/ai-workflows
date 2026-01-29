"""
Bottom-Up Strategy Response Models
==================================

This module defines the Pydantic schemas for structured responses used in the
bottom-up workflow generation strategy. These models capture the intermediate
analysis results during the multi-phase construction process.

Main Responsibilities:
    - Define ToolRequirement for capturing tool analysis results
    - Define ToolAnalysisResponse for the tool identification phase
    - Define ToolOrderingResponse for the execution sequencing phase
    - Define ControlFlowResponse for branching/conditional analysis

Key Dependencies:
    - pydantic: For data validation and schema definition

Strategy Phases:
    1. Tool Identification (ToolAnalysisResponse): What tools are needed?
    2. Tool Ordering (ToolOrderingResponse): In what sequence?
    3. Control Flow (ControlFlowResponse): Where is branching needed?
    4. Assembly: Combine analysis into final workflow (uses workflow models)
"""

from pydantic import BaseModel, Field
from typing import List, Literal


class ToolRequirement(BaseModel):
    """
    Schema representing a required tool identified during analysis.
    
    Captures the rationale for including a tool in the workflow along
    with its data dependencies and outputs.
    
    Attributes:
        tool_name: Name of the required tool from the registry.
        purpose: Explanation of why this tool is needed.
        inputs_needed: List of inputs this tool requires.
        outputs_produced: List of outputs this tool generates.
    """
    tool_name: str = Field(..., description="Name of the required tool")
    purpose: str = Field(..., description="Why this tool is needed")
    inputs_needed: List[str] = Field(..., description="What inputs this tool needs")
    outputs_produced: List[str] = Field(..., description="What outputs this tool produces")


class ToolAnalysisResponse(BaseModel):
    """
    Response schema for the tool identification phase.
    
    Captures the complete set of tools needed to accomplish the user's
    task along with the overall reasoning for the selection.
    
    Attributes:
        required_tools: List of tools needed for the workflow.
        reasoning: Explanation of the overall tool selection strategy.
    """
    required_tools: List[ToolRequirement] = Field(..., description="All tools needed to accomplish the task")
    reasoning: str = Field(..., description="Overall reasoning for tool selection")


class ToolOrderingResponse(BaseModel):
    """
    Response schema for the tool execution sequencing phase.
    
    Determines the optimal order for tool execution based on data
    dependencies between tools.
    
    Attributes:
        ordered_calls: Tool names in execution order.
        reasoning: Explanation of the ordering rationale.
    """
    ordered_calls: List[str] = Field(..., description="Names of tools in the order they should be called")
    reasoning: str = Field(..., description="Overall reasoning for tool ordering")


class ControlFlowDecision(BaseModel):
    """
    Schema for a single control flow decision point in the workflow.
    
    Identifies where conditional branching or decision-making is needed
    and specifies the possible branches.
    
    Attributes:
        decision_point: Step ID where branching occurs.
        decision_type: Type of control flow (branching or conditional).
        reason: Explanation of why control flow is needed here.
        branches: List of possible branch outcomes.
    """
    decision_point: int = Field(..., description="The step ID where decision/branching is needed")
    decision_type: Literal["branching", "conditional"] = Field(..., description="Type of control flow needed")
    reason: str = Field(..., description="Why control flow is needed here")
    branches: List[str] = Field(..., description="Possible branch outcomes")


class ControlFlowResponse(BaseModel):
    """
    Response schema for the control flow analysis phase.
    
    Identifies all decision points and LLM reasoning steps needed
    in the workflow.
    
    Attributes:
        control_decisions: List of all identified decision points.
        llm_calls_needed: Step IDs requiring LLM reasoning.
        reasoning: Explanation of the control flow design.
    """
    control_decisions: List[ControlFlowDecision] = Field(..., description="All control flow decisions needed")
    llm_calls_needed: List[int] = Field(..., description="Step IDs where LLM reasoning is needed")
    reasoning: str = Field(..., description="Overall control flow reasoning")