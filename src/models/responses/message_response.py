from pydantic import BaseModel, Field
from typing import Union, Literal

class Question(BaseModel):
    """A clarification question to gather missing information.
    
    Question Guidelines:
    - Ask only if information is missing or ambiguous
    - Request ONE single piece of information per question
    - Be directly necessary for workflow generation
    - Introduce new information, don't restate previous answers
    
    Focus Areas:
    - Required inputs or outputs
    - Constraints or assumptions
    - Tool requirements or restrictions
    - Expected behavior or success criteria
    
    Question Quality:
    - Keep clear and concise
    - Preferably single-sentence
    - Avoid compound or multi-part questions
    - Do NOT ask speculative or optional questions
    """
    message: str = Field(
        ...,
        description=(
            "The clarification question to ask the user. Must be a single, clear, concise question "
            "requesting one specific piece of missing or ambiguous information needed for workflow generation. "
            "For the first message only, start with one short paragraph explaining the clarification approach, "
            "then ask the first question if needed."
        )
    )

class EndClarifications(BaseModel):
    """Indicates that all necessary information has been collected."""
    end_clarifications: Literal["END_CLARIFICATIONS"] = "END_CLARIFICATIONS"

class MessageResponse(BaseModel):
    """A clarification message response.
    
    Behavioral Constraints:
    - Do NOT generate workflows, plans, steps, examples, or schemas
    - Do NOT provide recommendations, explanations, or interpretations beyond clarification
    - Do NOT repeat, rephrase, or revisit previously asked questions
    - Do NOT ask multiple questions in one turn
    
    Response Rules:
    - Never return both in the same response
    """
    result: Union[Question, EndClarifications] = Field(
        ...,
        description=(
            "The clarification result: either a Question object (if more information needed) "
            "or EndClarifications object (if clarification is complete and workflow generation can proceed)."
        )
    )
