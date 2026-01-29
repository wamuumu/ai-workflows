"""
Feature Base Module
===================

This module defines the abstract base class for workflow enhancement features
in the AI-Workflows framework. Features provide optional processing stages
that can be applied before or after workflow generation.

Main Responsibilities:
    - Define the FeatureBase abstract class interface
    - Establish phase-based feature organization (pre/post)
    - Provide common initialization pattern via kwargs

Key Dependencies:
    - abc: For abstract base class functionality

Feature Phases:
    - "pre": Applied before workflow generation (e.g., prompt clarification)
    - "post": Applied after workflow generation (e.g., refinement, validation)

Design Pattern:
    Features follow a Strategy-like pattern where each feature encapsulates
    a specific enhancement behavior. The orchestrator applies features in
    phase order, passing context between stages.
"""

from abc import ABC, abstractmethod
from typing import Literal


class FeatureBase(ABC):
    """
    Abstract base class for workflow enhancement features.
    
    Features augment the workflow generation pipeline by providing
    additional processing before (pre) or after (post) the main
    generation strategy executes.
    
    Attributes:
        _phase: The execution phase ("pre" or "post").
    
    Subclass Requirements:
        - Set _phase in __init__ before calling super().__init__()
        - Implement apply() to perform the enhancement
    """

    _phase: Literal["pre", "post"]

    def __init__(self, **kwargs):
        """
        Initialize the feature with optional keyword arguments.
        
        All keyword arguments are set as instance attributes, enabling
        flexible parameterization of feature behavior.
        
        Args:
            **kwargs: Additional parameters to set as instance attributes.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    @abstractmethod
    def apply(self, context, max_retries: int, debug: bool):
        """
        Apply the enhancement feature to the generation context.
        
        Pre-phase features typically modify the prompt or gather additional
        information. Post-phase features typically modify or validate the
        generated workflow.
        
        Args:
            context: The orchestrator Context object containing state.
            max_retries: Maximum retry attempts for LLM calls.
            debug: Whether to enable debug output.
            
        Returns:
            The modified context object.
        """
        pass

    def get_phase(self) -> str:
        """
        Get the execution phase of this feature.
        
        Returns:
            Either "pre" or "post" indicating when the feature applies.
        """
        return self._phase