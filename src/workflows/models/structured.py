from pydantic import BaseModel, Field
from typing import List, Union, Literal, Optional

class Parameter(BaseModel):
    """An object representing a parameter item in a workflow step."""
    key: str
    value: Union[str, int, float, bool]
    from_step: Optional[str] = None

class Result(BaseModel):
    """An object representing a result item in a workflow step."""
    key: str
    description: str

class ToolAction(BaseModel):
    """An action to call a tool."""
    action: Literal["call_tool"]
    tool_name: str

class LLMAction(BaseModel):
    """An action to call a LLM."""
    action: Literal["call_llm"]

class HumanAction(BaseModel):
    """An action to involve a human."""
    action: Literal["human_input"]
    instructions: str

class GlobalTransitions(BaseModel):
    rerun: Literal["default_rerun_logic"]
    human_needed: Literal["default_human_logic"]

class StepTransitions(BaseModel):
    """A transition from one step to another in a structured workflow."""
    success: str
    failure: str
    others: Optional[GlobalTransitions] = None

class Step(BaseModel):
    """A single step in a structured workflow."""
    id: str
    title: str
    description: str
    task: Union[ToolAction, LLMAction, HumanAction]
    parameters: Optional[List[Parameter]] = None
    results: List[Result]
    transitions: StepTransitions # ? Should we implement complex conditional logic
    thoughts: str

class StructuredWorkflow(BaseModel):
    """A structured workflow consisting of a sequence of steps and allowing branching."""
    title: str
    description: str
    global_transitions: GlobalTransitions
    steps: List[Step]