"""
Message Response Models
=======================

This module defines the Pydantic schemas for chat clarification responses
used in the ChatClarificationFeature. These models structure the agent's
clarification questions and signal when clarification is complete.

Main Responsibilities:
    - Define Question schema for clarification requests
    - Define EndClarifications to signal completion
    - Define MessageResponse as the unified response type

Key Dependencies:
    - pydantic: For data validation and schema definition

Clarification Flow:
    1. Feature initiates chat with user prompt
    2. Agent asks clarifying questions (Question responses)
    3. User provides answers
    4. Agent signals completion (EndClarifications response)
    5. Feature augments original prompt with clarification history
"""

from pydantic import BaseModel, Field
from typing import Union, Literal


class Question(BaseModel):
    """
    Schema for a single clarification question.
    
    Represents a question the agent needs answered to properly understand
    the user's intent before generating a workflow.
    
    Attributes:
        message: The clarification question text.
    
    Question Guidelines:
        - Ask only if information is missing or ambiguous.
        - Request ONE single piece of information per question.
        - Must be directly necessary for workflow generation.
        - Should not repeat or rephrase previous questions.
    
    Focus Areas:
        - Required inputs or outputs not specified in prompt.
        - Constraints or assumptions needing confirmation.
        - Tool requirements or restrictions.
        - Expected behavior or success criteria.
    """
    message: str = Field(
        ...,
        description="""
            The clarification question to ask the user. Must be a single, clear, concise question 
            requesting one specific piece of missing or ambiguous information needed for workflow generation. 
            For the first message only, start with one short paragraph explaining the clarification approach, 
            then ask the first question if needed.
        """
    )


class EndClarifications(BaseModel):
    """
    Schema signaling that clarification is complete.
    
    When the agent determines sufficient information has been gathered,
    it returns this model to indicate workflow generation can proceed.
    
    Attributes:
        end_clarifications: Literal sentinel value for type discrimination.
    """
    end_clarifications: Literal["END_CLARIFICATIONS"] = "END_CLARIFICATIONS"


class MessageResponse(BaseModel):
    """
    Union response type for clarification interactions.
    
    Wraps either a Question (more info needed) or EndClarifications
    (ready to proceed) in a single response schema.
    
    Attributes:
        result: Either Question or EndClarifications instance.
    
    Behavioral Constraints:
        - Agent must not generate workflows, plans, or examples.
        - Agent must not repeat previously asked questions.
        - Agent must ask at most one question per response.
        - Only one of Question or EndClarifications can be returned.
    """
    result: Union[Question, EndClarifications] = Field(
        ...,
        description="""
            The clarification result: either a Question object (if more information needed) 
            or EndClarifications object (if clarification is complete and workflow generation can proceed).
        """
    )
